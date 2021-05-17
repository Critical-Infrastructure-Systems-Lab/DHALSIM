import argparse
import os.path
import sqlite3
import signal
import sys
import time
from decimal import Decimal
from pathlib import Path

import yaml

from basePLC import BasePLC


class Error(Exception):
    """Base class for exceptions in this module."""


class TagDoesNotExist(Error):
    """Raised when tag you are looking for does not exist"""


class InvalidControlValue(Error):
    """Raised when tag you are looking for does not exist"""


def generate_real_tags(tanks, pumps, valves):
    real_tags = []

    for tank in tanks:
        if tank != "":
            real_tags.append((tank["name"], 1, 'REAL'))
    for pump in pumps:
        if pump != "":
            real_tags.append((pump["name"], 1, 'REAL'))
    for valve in valves:
        if valve != "":
            real_tags.append((valve["name"], 1, 'REAL'))

    return tuple(real_tags)


def generate_tags(taggable):
    tags = []

    if taggable:
        for tag in taggable:
            if tag and tag != "":
                tags.append((tag, 1))

    return tags


class GenericScada(BasePLC):
    """This class represents a scada. This scada knows what plcs it is collecting data from by reading the
    yaml file at intermediate_yaml_path and looking at the plcs.
    """

    def __init__(self, intermediate_yaml_path):
        self.local_time = 0

        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        # connection to the database
        self.conn = sqlite3.connect(self.intermediate_yaml["db_path"])
        self.cur = self.conn.cursor()

        self.output_path = Path(self.intermediate_yaml["output_path"]) / "scada_values.csv"

        # Create state from db values
        state = {
            'name': "plant",
            'path': self.intermediate_yaml['db_path']
        }

        # Create server, real tags are generated
        scada_server = {
            'address': self.intermediate_yaml['scada']['ip'],
            'tags': generate_real_tags(self.intermediate_yaml['tanks'],
                                       self.intermediate_yaml['pumps'],
                                       self.intermediate_yaml['valves'])
        }

        # Create protocol
        scada_protocol = {
            'name': 'enip',
            'mode': 1,
            'server': scada_server
        }

        # print "DEBUG SCADA INIT"
        # print "state = " + str(state)
        # print "scada_protocol = " + str(scada_protocol)

        super(GenericScada, self).__init__(name='scada', state=state, protocol=scada_protocol)

    def pre_loop(self, sleep=0.5):
        """The pre loop of a SCADA. In which setup actions are started

        :param sleep:  (Default value = 0.5) The time to sleep after setting everything up
        """
        print('DEBUG: SCADA enters pre_loop')

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        time.sleep(sleep)

    def get_tag(self, tag):
        """
        Get the value of a tag that is connected to this plc or over the network.

        :param tag: The tag to get
        :return: Value of that tag
        :rtype: int
        :raise: TagDoesNotExist if tag cannot be found
        """
        if tag in self.intermediate_plc["sensors"] or tag in self.intermediate_plc["actuators"]:
            return Decimal(self.get((tag, 1)))

        for i, plc_data in enumerate(self.intermediate_yaml["plcs"]):
            if i == self.yaml_index:
                continue
            if tag in plc_data["sensors"] or tag in plc_data["actuators"]:
                received = Decimal(self.receive((tag, 1), plc_data["ip"]))
                return received
        raise TagDoesNotExist(tag)

    def set_tag(self, tag, value):
        """
        Set a tag that is connected to this plc to a value.

        :param tag: Which tag to set
        :type tag: str
        :param value: value to set the Tag to
        :raise: TagDoesNotExist if tag is not connected to this plc
        """
        if isinstance(value, basestring) and value.lower() == "closed":
            value = 0
        elif isinstance(value, basestring) and value.lower() == "open":
            value = 1
        else:
            raise InvalidControlValue(value)

        if tag in self.intermediate_plc["sensors"] or tag in self.intermediate_plc["actuators"]:
            self.set((tag, 1), value)
        else:
            raise TagDoesNotExist(tag + " cannot be set from " + self.intermediate_plc["name"])

    def get_master_clock(self):
        """
        Get the value of the master clock of the physical process through the database
        :return: Iteration in the physical process
        """
        # Fetch master_time
        self.cur.execute("SELECT time FROM master_time WHERE id IS 1")
        master_time = self.cur.fetchone()[0]
        return master_time

    def get_sync(self):
        """
        Get the sync flag of this plc.

        :return: False if physical process wants the plc to do a iteration, True if not.
        """
        self.cur.execute("SELECT flag FROM sync WHERE name IS ?", (self.intermediate_plc["name"],))
        flag = bool(self.cur.fetchone()[0])
        return flag

    def set_sync(self, flag):
        """
        Set this plcs sync flag in the sync table. When this is 1, the physical process
        knows this plc finished the requested iteration.

        :param flag: True for sync to 1, false for sync to 0

        """

        self.cur.execute("UPDATE sync SET flag=? WHERE name IS ?",
                         (int(flag), self.intermediate_plc["name"],))
        self.conn.commit()

    def sigint_handler(self, sig, frame):
        print 'DEBUG SCADA shutdown'
        self.write_output()
        sys.exit(0)

    def main_loop(self, sleep=0.5):
        """
        The main loop of a PLC. In here all the controls will be applied.

        :param sleep:  (Default value = 0.5) Not used

        """
        print('DEBUG: ' + self.intermediate_plc['name'] + ' enters main_loop')
        while True:
            while self.get_sync():
                pass

            self.local_time += 1

            for control in self.controls:
                control.apply(self)

            self.set_sync(1)

            # time.sleep(0.05)


def is_valid_file(parser_instance, arg):
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
