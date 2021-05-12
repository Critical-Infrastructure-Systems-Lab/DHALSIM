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


class GenericPLC(BasePLC):

    def __init__(self, intermediate_yaml_path, yaml_index, week_index):
        self.yaml_index = yaml_index
        self.week_index = week_index
        self.local_time = 0

        with open(os.path.abspath(intermediate_yaml_path)) as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        # Create state from db values
        state = {
            'name': self.intermediate_yaml['db_name'],
            'path': self.intermediate_yaml['db_path']
        }

        # Create list of dependant sensors
        dependant_sensors = []
        for control in self.intermediate_yaml['plcs'][self.yaml_index]['controls']:
            if control["type"] != "Time":
                dependant_sensors.append(control["dependant"])

        # Create list of PLC sensors
        plc_sensors = self.intermediate_yaml['plcs'][self.yaml_index]['sensors']

        # Create server, real tags are generated
        plc_server = {
            'address': self.intermediate_yaml['plcs'][self.yaml_index]['ip'],
            'tags': generate_real_tags(plc_sensors,
                                       list(set(dependant_sensors) - set(plc_sensors)),
                                       self.intermediate_yaml['plcs'][self.yaml_index]['actuators'])
        }

        # Create protocol
        plc_protocol = {
            'name': 'enip',
            'mode': 1,
            'server': plc_server
        }

        # print "DEBUG INIT: " + self.intermediate_yaml['plcs'][self.yaml_index]['name']
        # print "state = " + str(state)
        # print "plc_protocol = " + str(plc_protocol)

        super(GenericPLC, self).__init__(name=self.intermediate_yaml['plcs'][self.yaml_index]['name'].lower(),
                                         state=state, protocol=plc_protocol)

    def pre_loop(self):
        print 'DEBUG: ' + self.intermediate_yaml['plcs'][self.yaml_index]['name'] + ' enters pre_loop'

        reader = True

        sensors = generate_tags(self.intermediate_yaml['plcs'][self.yaml_index]['sensors'])
        actuators = generate_tags(self.intermediate_yaml['plcs'][self.yaml_index]['actuators'])

        values = []
        for tag in sensors:
            values.append(Decimal(self.get(tag)))
        for tag in actuators:
            values.append(int(self.get(tag)))

        lock = threading.Lock()

        sensors.extend(actuators)
        print str(sensors)

        BasePLC.set_parameters(self, sensors, values, reader, lock,
                               self.intermediate_yaml['plcs'][self.yaml_index]['ip'])
        self.startup()

    # def get_attack_dict(self, path, name):
    #     with open(path) as config_file:
    #         attack_file = yaml.load(config_file, Loader=yaml.FullLoader)
    #
    #     for attack in attack_file['attacks']:
    #         if name == attack['name']:
    #             return attack

    def main_loop(self):
        print 'DEBUG: ' + self.intermediate_yaml['plcs'][self.yaml_index]['name'] + ' enters main_loop'
        while True:
            try:
                self.local_time += 1
                # self.t0 = Decimal(self.get(T0))
                # self.t2 = Decimal(self.receive(T2, PLC2_ADDR))
                # print("ITERATION %d ------------- " % self.local_time)
                # print("Tank 0 Level %f " % self.t0)
                # print("Tank 2 Level %f " % self.t2)
                #
                # if self.t0 < 0.256:
                #     self.vpub = 1
                #     self.praw1 = 0
                #
                # if self.t0 > 0.448:
                #     self.vpub = 0
                #
                # if self.t2 < 0.16:
                #     print("Opening P_RAW1")
                #     self.praw1 = 1
                #
                # if self.t2 > 0.32:
                #     print("Closing P_RAW1")
                #     self.praw1 = 0
                #
                # self.set(P_RAW1, self.praw1)
                # self.set(V_PUB, self.vpub)

                time.sleep(0.1)

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
