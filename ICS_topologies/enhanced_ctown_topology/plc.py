from basePLC import BasePLC
from utils import *
from datetime import datetime
from decimal import Decimal
import time
import threading
import yaml
import sys


class PLC(BasePLC):
    def pre_loop(self):

        # toDO: We will handle initialization using argparse in __main__ and then pass these parameters to pre_loop
        self.name = sys.argv[1]
        self.week_index = sys.argv[2]
        self.plc_dict_path = sys.argv[3]

        print "Pre-loop"
        with open(self.plc_dict_path, 'r') as plc_file:
            plc_dicts = yaml.full_load(plc_file)
        self.plc_dict = self.get_plc_dict(plc_dicts)
        print self.plc_dict

        self.verify_list()

        self.tags_to_get = []
        self.values_to_get = []

        self.tags_to_send = []
        self.values_to_send = []

        self.tags_to_receive = []

        # These values are obtained locally
        # Tags that are meant to be GET and SEND should be handled differently
        self.tags_to_get.extend(self.plc_dict['Sensors'])


        # These values need to be send using the thread
        self.tags_to_send.extend(self.plc_dict['Sensors'])
        self.tags_to_send.extend(self.plc_dict['Actuators'])

        for dependency in self.plc_dict['Dependencies']:
            self.tags_to_receive.extend(dependency['tag'])

        self.converted_tags_to_send = []

        # Initialize the values to send them
        for tag in self.tags_to_send:
            converted_tag = self.convert_tag_to_enip_tag(tag)
            self.converted_tags_to_send.append(converted_tag)
            self.values_to_send.append(self.get(converted_tag))

        if self.name != "SCADA" or self.name != "scada":
            # If we are a SCADA we don't need a reader thread
            # Flag used to stop the thread
            self.reader = True
            isScada = False
        else:
            self.reader = False
            isScada = True

        path = self.name + "_received_values.csv"
        self.received_values = [["iteration", "timestamp"]]
        self.received_values.extend(self.tags_to_send)
        self.received_values.extend(self.tags_to_send)
        self.received_values.extend(self.tags_to_receive)

        self.lock = threading.Lock()

        #toDo: How to get the lastPLC?
        lastPLC = False

        print(str(self.tags_to_send))
        print(str(self.converted_tags_to_send))

        # Here we could call BasePLC.setParameters()
        BasePLC.set_parameters(self, path, self.received_values, self.converted_tags_to_send, self.values_to_send, self.reader,
                               self.lock, ENIP_LISTEN_PLC_ADDR, lastPLC, self.week_index, isScada)
        #sys.exit()
        self.startup()

    def convert_tag_to_enip_tag(self, tag):
        return (tag, 1)

    def verify_list(self):
        for sensor in self.plc_dict['Sensors']:
            if sensor == "":
                self.plc_dict['Sensors'].remove(sensor)
        for actuator in self.plc_dict['Actuators']:
            if actuator == "":
                self.plc_dict['Actuators'].remove(actuator)



    def get_plc_dict(self, plc_list):
        for plc in plc_list:
            if plc['PLC'] == self.name.upper():
                return plc

    def main_loop(self):
        print "Main loop"

if __name__ == "__main__":
    plc1 = PLC(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)