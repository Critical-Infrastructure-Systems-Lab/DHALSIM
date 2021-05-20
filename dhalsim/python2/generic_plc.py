import argparse
import os.path
import sqlite3
import threading
import time
from decimal import Decimal
from pathlib import Path

import yaml

from basePLC import BasePLC
from control import AboveControl, BelowControl, TimeControl


class Error(Exception):
    """Base class for exceptions in this module."""


class TagDoesNotExist(Error):
    """Raised when tag you are looking for does not exist"""


class InvalidControlValue(Error):
    """Raised when tag you are looking for does not exist"""


def generate_real_tags(sensors, dependants, actuators):
    real_tags = []

    for sensor_tag in sensors:
        if sensor_tag != "":
            real_tags.append((sensor_tag, 1, 'REAL'))
    for dependant_tag in dependants:
        if dependant_tag != "":
            real_tags.append((dependant_tag, 1, 'REAL'))
    for actuator_tag in actuators:
        if actuator_tag != "":
            real_tags.append((actuator_tag, 1, 'REAL'))

    return tuple(real_tags)


def generate_tags(taggable):
    tags = []

    if taggable:
        for tag in taggable:
            if tag and tag != "":
                tags.append((tag, 1))

    return tags


def create_controls(controls_list):
    ret = []
    for control in controls_list:
        if control["type"].lower() == "above":
            control_instance = AboveControl(control["actuator"], control["action"],
                                            control["dependant"],
                                            control["value"])
            ret.append(control_instance)
        if control["type"].lower() == "below":
            control_instance = BelowControl(control["actuator"], control["action"],
                                            control["dependant"],
                                            control["value"])
            ret.append(control_instance)
        if control["type"].lower() == "time":
            control_instance = TimeControl(control["actuator"], control["action"], control["value"])
            ret.append(control_instance)
    return ret


class GenericPLC(BasePLC):
    """
    This class represents a plc. This plc knows what it is connected to by reading the
    yaml file at intermediate_yaml_path and looking at index yaml_index in the plcs section.
    """

    def __init__(self, intermediate_yaml_path, yaml_index):
        self.yaml_index = yaml_index
        self.local_time = 0

        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.intermediate_plc = self.intermediate_yaml["plcs"][self.yaml_index]

        if 'sensors' not in self.intermediate_plc:
            self.intermediate_plc['sensors'] = list()

        if 'actuators' not in self.intermediate_plc:
            self.intermediate_plc['actuators'] = list()

        # connection to the database
        self.conn = sqlite3.connect(self.intermediate_yaml["db_path"])
        self.cur = self.conn.cursor()

        self.intermediate_controls = self.intermediate_plc['controls']

        self.controls = create_controls(self.intermediate_controls)
        # print(self.controls)
        # Create state from db values
        state = {
            'name': "plant",
            'path': self.intermediate_yaml['db_path']
        }

        # Create list of dependant sensors
        dependant_sensors = []
        for control in self.intermediate_controls:
            if control["type"] != "Time":
                dependant_sensors.append(control["dependant"])

        # Create list of PLC sensors
        plc_sensors = self.intermediate_plc['sensors']

        # Create server, real tags are generated
        plc_server = {
            'address': self.intermediate_plc['local_ip'],
            'tags': generate_real_tags(plc_sensors,
                                       list(set(dependant_sensors) - set(plc_sensors)),
                                       self.intermediate_plc['actuators'])
        }

        # Create protocol
        plc_protocol = {
            'name': 'enip',
            'mode': 1,
            'server': plc_server
        }

        # print "DEBUG INIT: " + self.intermediate_plc['name']
        # print "state = " + str(state)
        # print "plc_protocol = " + str(plc_protocol)

        super(GenericPLC, self).__init__(name=self.intermediate_plc['name'],
                                         state=state, protocol=plc_protocol)

    def pre_loop(self, sleep=0.5):
        """
        The pre loop of a PLC. In everything is setup. Like starting the sending thread through
        the :class:`~dhalsim.python2.basePLC` class.

        :param sleep:  (Default value = 0.5) The time to sleep after setting everything up
        """
        print('DEBUG: ' + self.intermediate_plc['name'] + ' enters pre_loop')

        reader = True

        sensors = generate_tags(self.intermediate_plc['sensors'])
        actuators = generate_tags(self.intermediate_plc['actuators'])

        values = []
        for tag in sensors:
            values.append(Decimal(self.get(tag)))
        for tag in actuators:
            values.append(int(self.get(tag)))

        lock = threading.Lock()

        sensors.extend(actuators)

        BasePLC.set_parameters(self, sensors, values, reader, lock,
                               self.intermediate_plc['local_ip'])
        self.startup()

        time.sleep(sleep)

    def get_tag(self, tag):
        """
        Get the value of a tag that is connected to this PLC or over the network.

        :param tag: The tag to get
        :type tag: str
        :return: value of that tag
        :rtype: int
        :raise: TagDoesNotExist if tag cannot be found
        """
        if tag in self.intermediate_plc["sensors"] or tag in self.intermediate_plc["actuators"]:
            return Decimal(self.get((tag, 1)))

        for i, plc_data in enumerate(self.intermediate_yaml["plcs"]):
            if i == self.yaml_index:
                continue
            if tag in plc_data["sensors"] or tag in plc_data["actuators"]:
                received = Decimal(self.receive((tag, 1), plc_data["public_ip"]))
                return received
        raise TagDoesNotExist(tag)

    def set_tag(self, tag, value):
        """
        Set a tag that is connected to this PLC to a value.

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
        Get the value of the master clock of the physical process through the database.

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

    def main_loop(self, sleep=0.5):
        """
        The main loop of a PLC. In here all the controls will be applied.

        :param sleep:  (Default value = 0.5) Not used
        """
        print('DEBUG: ' + self.intermediate_plc['name'] + ' enters main_loop')
        while True:
            while self.get_sync():
                pass

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
    parser = argparse.ArgumentParser(description='Start everything for a plc')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument(dest="index", help="Index of PLC in intermediate yaml", type=int,
                        metavar="N")

    args = parser.parse_args()

    plc = GenericPLC(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index)
