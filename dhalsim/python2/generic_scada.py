import argparse
import csv
import os.path
import sqlite3
import signal
import sys
import time
from pathlib import Path

import yaml
from minicps.devices import SCADAServer


class Error(Exception):
    """Base class for exceptions in this module."""


class TagDoesNotExist(Error):
    """Raised when tag you are looking for does not exist"""


class InvalidControlValue(Error):
    """Raised when tag you are looking for does not exist"""


def generate_real_tags(plcs):
    """
    Generates real tags with all sensors and actuators attached to pls in the network.

    :param plcs: list of plcs
    """
    real_tags = []

    for plc in plcs:
        if 'sensors' not in plc:
            plc['sensors'] = list()

        if 'actuators' not in plc:
            plc['actuators'] = list()

        for sensor in plc['sensors']:
            if sensor != "":
                real_tags.append((sensor, 1, 'REAL'))
        for actuator in plc['actuators']:
            if actuator != "":
                real_tags.append((actuator, 1, 'REAL'))

    return tuple(real_tags)


def generate_tags(taggable):
    """
    Generates tags from a list of taggable entities (sensor or actuator)

    :param taggable: a list of strings containing names of things like tanks, pumps, and valves
    """
    tags = []

    if taggable:
        for tag in taggable:
            if tag and tag != "":
                tags.append((tag, 1))

    return tags


class GenericScada(SCADAServer):
    """
    This class represents a scada. This scada knows what plcs it is collecting data from by reading the
    yaml file at intermediate_yaml_path and looking at the plcs.
    """
    def __init__(self, intermediate_yaml_path):
        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        # Initialize connection to the database
        self.initialize_db()

        self.output_path = Path(self.intermediate_yaml["output_path"]) / "scada_values.csv"

        self.output_path.touch(exist_ok=True)

        # Create state from db values
        state = {
            'name': "plant",
            'path': self.intermediate_yaml['db_path']
        }

        # Create server, real tags are generated
        scada_server = {
            'address': self.intermediate_yaml['scada']['local_ip'],
            'tags': generate_real_tags(self.intermediate_yaml['plcs'])
        }

        # Create protocol
        scada_protocol = {
            'name': 'enip',
            'mode': 1,
            'server': scada_server
        }

        self.plc_data = self.generate_plcs()
        self.saved_values = [[]]

        for PLC in self.intermediate_yaml['plcs']:
            if 'sensors' not in PLC:
                PLC['sensors'] = list()

            if 'actuators' not in PLC:
                PLC['actuators'] = list()
            self.saved_values[0].extend(PLC['sensors'])
            self.saved_values[0].extend(PLC['actuators'])

        # print "-----------DEBUG SCADA INIT-----------"
        # print "state = " + str(state)
        # print "scada_protocol = " + str(scada_protocol)
        # print "plc_data = " + str(self.plc_data)
        # print "output_format = " + str(self.saved_values)
        # print "-----------DEBUG SCADA INIT-----------"

        self.do_super_construction(scada_protocol, state)

    def do_super_construction(self, scada_protocol, state):
        """
        Function that performs the super constructor call to SCADAServer
        Introduced to better facilitate testing
        """
        super(GenericScada, self).__init__(name='scada', state=state, protocol=scada_protocol)

    def initialize_db(self):
        """
        Function that initializes PLC connection to the database
        Introduced to better facilitate testing
        """
        self.conn = sqlite3.connect(self.intermediate_yaml["db_path"])
        self.cur = self.conn.cursor()

    def pre_loop(self, sleep=0.5):
        """
        The pre loop of a SCADA. In which setup actions are started.

        :param sleep:  (Default value = 0.5) The time to sleep after setting everything up
        """
        print('DEBUG: SCADA enters pre_loop')

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        time.sleep(sleep)

    def get_sync(self):
        """
        Get the sync flag of this plc.

        :return: False if physical process wants the plc to do a iteration, True if not.
        """
        self.cur.execute("SELECT flag FROM sync WHERE name IS 'scada'")
        flag = bool(self.cur.fetchone()[0])
        return flag

    def set_sync(self, flag):
        """
        Set this plcs sync flag in the sync table. When this is 1, the physical process
        knows this plc finished the requested iteration.

        :param flag: True for sync to 1, false for sync to 0
        """
        self.cur.execute("UPDATE sync SET flag=? WHERE name IS 'scada'",
                         (int(flag),))
        self.conn.commit()

    def sigint_handler(self, sig, frame):
        """
        Shutdown protocol for the scada, writes the output before exiting.
        """
        print 'DEBUG SCADA shutdown'
        self.write_output()
        sys.exit(0)

    def write_output(self):
        """
        Writes the csv output of the scada
        """
        with self.output_path.open(mode='wb') as output:
            writer = csv.writer(output)
            writer.writerows(self.saved_values)

    def generate_plcs(self):
        """
        Generates a list of tuples, the first part being the ip of a PLC,
        and the second  being a list of tags attached to that PLC.
        """
        plcs = []

        for PLC in self.intermediate_yaml['plcs']:
            if 'sensors' not in PLC:
                PLC['sensors'] = list()

            if 'actuators' not in PLC:
                PLC['actuators'] = list()

            tags = []

            tags.extend(generate_tags(PLC['sensors']))
            tags.extend(generate_tags(PLC['actuators']))

            plcs.append((PLC['public_ip'], tags))

        return plcs

    def main_loop(self, sleep=0.5, test_break=False):
        """
        The main loop of a PLC. In here all the controls will be applied.

        :param sleep:  (Default value = 0.5) Not used
        :param test_break:  (Default value = False) used for unit testing, breaks the loop after one iteration
        """
        print('DEBUG: SCADA enters main_loop')
        while True:
            while self.get_sync():
                time.sleep(0.01)

            try:
                results = []
                for plc_datum in self.plc_data:
                    plc_value = self.receive_multiple(plc_datum[1], plc_datum[0])
                    # print "plc_value received by scada from ip: " + str(plc_datum[0]) + " is " + str(plc_value)
                    results.extend(plc_value)
                self.saved_values.append(results)
            except Exception, msg:
                print(msg)
                continue

            self.set_sync(1)

            if test_break:
                break


def is_valid_file(parser_instance, arg):
    """
    Verifies whether the intermediate yaml path is valid.

    :param parser_instance: instance of argparser
    :param arg: the path to check
    """
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start everything for a scada')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))

    args = parser.parse_args()

    plc = GenericScada(intermediate_yaml_path=Path(args.intermediate_yaml))
