import argparse
import os.path

from basePLC import BasePLC
from datetime import datetime
from decimal import Decimal
import time
import threading
import sys
import yaml

intermediate_abs_path = '/home/chizzy/Documents/VM16_SSHFS_MNT/dhalsim/examples/wadi_topology/intermediate.yaml'


# plc1_log_path = 'plc1.log'
# todo: make intermediate yaml location not hardcoded

def get_arguments():
    parser = argparse.ArgumentParser(description='Script for individual PLCs')
    parser.add_argument("--index", "-i", help="Index of the PLC in intermediate yaml")
    parser.add_argument("--week", "-w", help="Week index of the simulation")
    parser.add_argument("--yaml", "-y", help="Path of intermediate yaml")
    return parser.parse_args()


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
            if tag:
                if tag != "":
                    tags.append((tag, 1))

    return tags


def create_controls(controls_list):
    ret = []
    for control in controls_list:
        if control["type"] == "Above":
            ret.append(AboveControl(control["actuator"], control["action"], control["dependant"], control["value"]))
        if control["type"] == "Below":
            ret.append(BelowControl(control["actuator"], control["action"], control["dependant"], control["value"]))
        if control["type"] == "Time":
            ret.append(TimeControl(control["actuator"], control["action"], control["value"]))

    return ret


class GenericPLC(BasePLC):

    def __init__(self, intermediate_yaml_path, yaml_index, week_index):
        self.yaml_index = yaml_index
        self.week_index = week_index
        self.local_time = 0

        with open(os.path.abspath(intermediate_yaml_path)) as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.intermediate_plc = self.intermediate_yaml["plcs"][self.yaml_index]

        self.intermediate_controls = self.intermediate_plc['controls']

        self.controls = create_controls(self.intermediate_controls)

        # Create state from db values
        state = {
            'name': self.intermediate_yaml['db_name'],
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
            'address': self.intermediate_plc['ip'],
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

        print "DEBUG INIT: " + self.intermediate_plc['name']
        print "state = " + str(state)
        print "plc_protocol = " + str(plc_protocol)

        super(GenericPLC, self).__init__(name=self.intermediate_plc['name'],
                                         state=state, protocol=plc_protocol)

    def pre_loop(self):
        print 'DEBUG: ' + self.intermediate_plc['name'] + ' enters pre_loop'

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
                               self.intermediate_plc['ip'])
        self.startup()

    # def get_attack_dict(self, path, name):
    #     with open(path) as config_file:
    #         attack_file = yaml.load(config_file, Loader=yaml.FullLoader)
    #
    #     for attack in attack_file['attacks']:
    #         if name == attack['name']:
    #             return attack

    def main_loop(self):
        print('DEBUG: ' + self.intermediate_plc['name'] + ' enters main_loop')
        while True:
            try:
                self.local_time += 1

                for control in self.controls:
                    control.apply(self)

                time.sleep(0.25)

            except Exception:
                continue



if __name__ == "__main__":
    # Get arguments from commandline
    args = get_arguments()
    # Get index and week index from commandline
    if args.index:
        plc_index = int(args.index)
        print "PLC INDEX: " + str(plc_index)
    else:
        raise IOError

    if args.week:
        w_index = int(args.week)
        print "WEEK INDEX: " + str(w_index)
    else:
        w_index = 0

    if args.yaml:
        yaml_path = args.yaml
    else:
        yaml_path = intermediate_abs_path

    plc = GenericPLC(
        intermediate_yaml_path=yaml_path,
        yaml_index=plc_index,
        week_index=w_index)
