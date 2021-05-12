import argparse
import os.path

from basePLC import BasePLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T0, T2, P_RAW1, V_PUB, flag_attack_plc1, PLC2_ADDR, PLC1_ADDR
from datetime import datetime
from decimal import Decimal
import time
from utils import ATT_1, ATT_2
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
    return parser.parse_args()

def generate_real_tags(sensors, actuators):
    real_tags = "("

    for sensor_tag in sensors:
        if sensor_tag != "":
            real_tags += "\n    ('" + sensor_tag + "', 1, 'REAL'),"
    for actuator_tag in actuators:
        if actuator_tag != "":
            real_tags += "\n    ('" + actuator_tag + "', 1, 'REAL'),"

    real_tags += "\n)"
    return real_tags

def generate_tags(sensors, actuators):
    tags = "("

    for sensor_tag in sensors:
        if sensor_tag != "":
            tags += "\n    ('" + sensor_tag + "', 1),"
    for actuator_tag in actuators:
        if actuator_tag != "":
            tags += "\n    ('" + actuator_tag + "', 1),"

    tags += "\n)"
    return tags


class GenericPLC(BasePLC):

    def __init__(self, name, state, protocol, memory, disk, intermediate_yaml_file, yaml_index):
        self.yaml_path = intermediate_yaml_file
        self.yaml_index = yaml_index
        super(GenericPLC, self).__init__(name, state, protocol, memory, disk)

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'

        # # We wish we could implement this as arg_parse, but we cannot overwrite the constructor
        # self.week_index = sys.argv[2]
        #
        # self.attack_flag = False
        # self.attack_dict = None
        #
        # if len(sys.argv) >= 4:
        #     self.attack_flag = sys.argv[4]
        #     self.attack_path = sys.argv[6]
        #     self.attack_name = sys.argv[8]
        #
        # if self.attack_flag:
        #     self.attack_dict = self.get_attack_dict(self.attack_path, self.attack_name)
        #     print "PLC1 running attack: " + str(self.attack_dict)
        #
        #
        # self.local_time = 0
        #
        # self.reader = True
        #
        # self.t0 = Decimal(self.get(T0))
        #
        # self.praw1 = int(self.get(P_RAW1))
        # self.vpub = int(self.get(V_PUB))
        #
        # self.p_raw_delay_timer = 0
        # self.timeout_counter = 0
        #
        # self.lock = threading.Lock()
        #
        # BasePLC.set_parameters(self, [T0, P_RAW1, V_PUB],
        #                        [self.t0, self.praw1, self.vpub], self.reader, self.lock, PLC1_ADDR)
        # self.startup()

    # def get_attack_dict(self, path, name):
    #     with open(path) as config_file:
    #         attack_file = yaml.load(config_file, Loader=yaml.FullLoader)
    #
    #     for attack in attack_file['attacks']:
    #         if name == attack['name']:
    #             return attack

    # def main_loop(self):
    #     while True:
    #         try:
    #             self.local_time += 1
    #
    #             # Reads from the DB
    #             attack_on = int(self.get(ATT_2))
    #             self.set(ATT_1, attack_on)
    #
    #             self.t0 = Decimal(self.get(T0))
    #             self.t2 = Decimal(self.receive(T2, PLC2_ADDR))
    #             print("ITERATION %d ------------- " % self.local_time)
    #             print("Tank 0 Level %f " % self.t0)
    #             print("Tank 2 Level %f " % self.t2)
    #
    #             if self.t0 < 0.256:
    #                 self.vpub = 1
    #                 self.praw1 = 0
    #
    #             if self.t0 > 0.448:
    #                 self.vpub = 0
    #
    #             if self.t2 < 0.16:
    #                 print("Opening P_RAW1")
    #                 self.praw1 = 1
    #
    #             if self.t2 > 0.32:
    #                 print("Closing P_RAW1")
    #                 self.praw1 = 0
    #
    #             # This is configured in the yaml file
    #             if self.attack_flag:
    #                 # Now ATT_2 is set in the physical_process. This in order to make more predictable the
    #                 # attack start and end time. This ATT_2 is read from the DB
    #                 if attack_on == 1:
    #                     if self.attack_dict['command'] == 'Close':
    #                         # toDo: Implement this dynamically.
    #                         # There's a horrible way of doing it with the current code. This would be much
    #                         # easier (and less horrible) if we use the general topology
    #
    #                         # pu1 and pu2 should not be hardcoded
    #                         # This object should have a list of actuators
    #                         self.praw1 = 0
    #                         self.vpub = 0
    #                     elif self.attack_dict['command'] == 'Open':
    #                         self.praw1 = 1
    #                         self.vpub = 1
    #                     elif self.attack_dict['command'] == 'Maintain':
    #                         continue
    #                     elif self.attack_dict['command'] == 'Toggle':
    #                         if self.praw1 == 1:
    #                             self.praw1 = 0
    #                         else:
    #                             self.praw1 = 1
    #
    #                         if self.vpub == 1:
    #                             self.vpub = 0
    #                         else:
    #                             self.vpub = 1
    #                     else:
    #                         print "Warning. Attack not implemented yet"
    #
    #             self.set(P_RAW1, self.praw1)
    #             self.set(V_PUB, self.vpub)
    #
    #             self.set(ATT_1, 0)
    #             time.sleep(0.1)
    #
    #         except Exception:
    #             continue


if __name__ == "__main__":
    args = get_arguments()

    with open(os.path.abspath(intermediate_abs_path)) as yaml_file:
        intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

    if args.index:
        plc_index = args.index
    else:
        raise IOError

    # Not sure why week index passed tbh
    # if args.week:
    #     week_index = args.week
    # else:
    #     week_index = 0

    STATE = {
        'name': intermediate_yaml['db_name'],
        'path': intermediate_yaml['db_path']
    }

    PLC1_SERVER = {
        'address': intermediate_yaml['plcs'][plc_index]['ip'],
        'tags': generate_real_tags(intermediate_yaml['plcs'][plc_index]['sensors'], intermediate_yaml['plcs'][plc_index]['actuators'])
    }

    PLC1_PROTOCOL = {
        'name': 'enip',
        'mode': 1,
        'server': PLC1_SERVER
    }

    NAME =  intermediate_yaml['plcs'][plc_index]['name']

    plc = GenericPLC(
        name=NAME,
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA,
        intermediate_yaml_file=intermediate_yaml,
        yaml_index=plc_index)
