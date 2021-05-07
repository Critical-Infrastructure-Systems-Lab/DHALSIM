from dhalsim.python2.basePLC import BasePLC
from utils import *
from datetime import datetime
from decimal import Decimal
import time
import threading
import yaml
import sys
import argparse


class PLC(BasePLC):
    def pre_loop(self):

        self.name = sys.argv[2]
        self.week_index = sys.argv[4]
        self.plc_dict_path = sys.argv[6]
        lastPLC = sys.argv[8]

        # This is a list of dictionaries with keys 'tag' and 'value'
        self.tags_to_get = []

        # The list of tags to send is handled different, because they are not required for the control logic.
        # (We do not take decisions based on this, we simply perform self.get and self.send on them)
        self.tags_to_send = []
        self.values_to_send = []

        self.tags_to_receive = []

        self.local_time = 0

        print("Pre-loop")
        self.plc_dict = self.get_plc_dict()
        if self.plc_dict == None:
            print("No valid PLC found, aborting")
            sys.exit(1)

        self.verify_list()
        self.populate_tag_list('Sensors')

        # These values need to be send using the thread
        self.tags_to_send.extend(self.plc_dict['Sensors'])
        self.tags_to_send.extend(self.plc_dict['Actuators'])

        # this wil populate self.tags_to_receive. This is a list of dictionaries with 'tag', 'node', and 'value'
        self.populate_dependencies()

        self.converted_tags_to_send = []

        # Initialize the values to send them
        for tag in self.tags_to_send:
            converted_tag = self.convert_tag_to_enip_tag(tag)
            self.converted_tags_to_send.append(converted_tag)
            self.values_to_send.append(Decimal(self.get(converted_tag)))

        if self.name != "SCADA" or self.name != "scada":
            # If we are a SCADA we don't need a reader thread
            # Flag used to stop the thread
            self.reader = True
            isScada = False
        else:
            self.reader = False
            isScada = True

        path = self.name + "_received_values.csv"
        self.received_values = ["iteration", "timestamp"]
        self.received_values.extend(self.tags_to_send)

        self.lock = threading.Lock()

        BasePLC.set_parameters(self, path, self.received_values, self.converted_tags_to_send, self.values_to_send, self.reader,
                               self.lock, ENIP_LISTEN_PLC_ADDR, lastPLC, self.week_index, isScada)
        self.startup()

    def populate_tag_list(self, tag_type):

        # Populate and initialize the tag list
        for tag in self.plc_dict[tag_type]:
            tag_dict = {}
            tag_dict['tag'] = tag
            tag_dict['value'] = Decimal(self.get(eval(tag_dict['tag'])))
            self.tags_to_get.append(tag_dict)

    def populate_dependencies(self):
        """
        Dependencies are tags that this PLC does not have. This means the PLC needs to request using ENIP/Modbus
        the tag to a different PLC or node
        :return:
        """
        for dependency in self.plc_dict['Dependencies']:
            dependency_dict = {}
            dependency_dict['tag'] = dependency['tag']
            dependency_dict['node'] = dependency['PLC'].lower()
            dependency_dict['value'] = self.receive(eval(dependency_dict['tag']), CTOWN_IPS[dependency_dict['node']])
            self.tags_to_receive.append(dependency_dict)

    def convert_tag_to_enip_tag(self, tag):
        """
        This method should be deprecated, and instead use eval()
        :param tag:
        :return:
        """
        return (tag, 1)

    def verify_list(self):
        """
        This method is used to verify that there is no sensor or actuator as ''
        :return:
        """
        for sensor in self.plc_dict['Sensors']:
            if sensor == "":
                self.plc_dict['Sensors'].remove(sensor)
        for actuator in self.plc_dict['Actuators']:
            if actuator == "":
                self.plc_dict['Actuators'].remove(actuator)

    def get_plc_dict(self):
        """
        Given a list of PLC dicts, returns the PLC of this instance. As defined by self.name
        :return:
        """
        with open(self.plc_dict_path, 'r') as plc_file:
            plc_dicts = yaml.full_load(plc_file)

        for plc in plc_dicts:
            if plc['PLC'] == self.name.upper():
                return plc

        return None

    def update_actuators(self):
        """
        This method applies the control logic in the PLC. Control logic is defined in plc_dict['controls']
        to apply the control logic, we need to check for all the actuators, if a specific rule criteria is matched.
        If this is the case, we apply the actuator_value on such actuator
        """
        for actuator in self.plc_dict['Actuators']:
            rules = self.get_control_rules_by_actuator(actuator)
            for rule in rules:
                #Need to check this
                value = self.get_value_for_rule(rule)
                #print("Found value " + str(value))
                if self.check_condition(value, rule['operator'], rule['value']):
                    #print "Condition applies because tag " + str(rule['tank_tag']) + " has value " + str(value) + " " +\
                    #      str(rule['operator']) + " than " + str(rule['value'])
                    if rule['actuator_value'] == 'Open':
                        #print("Opening " + str(rule['actuator_tag']))
                        #print("Eval value " + str(eval(rule['actuator_tag'])))
                        self.set(eval(rule['actuator_tag']), int(1))
                    if rule['actuator_value'] == 'Closed':
                        #print("Closing " + str(rule['actuator_tag']))
                        self.set(eval(rule['actuator_tag']), int(0))

    def get_value_for_rule(self, a_rule):
        """
        This method finds the value that needs to be evaluated in this rule
        :param a_rule:
        :return:
        """
        for tag in self.tags_to_get:
            if tag['tag'] == a_rule['tank_tag']:
                return tag['value']

        for tag in self.tags_to_receive:
            if tag['tag'] == a_rule['tank_tag']:
                #print(tag['value'])
                return tag['value']

    def check_condition(self, current_value, operator, limit):
        """
        This method checks is a condition is True, in order to trigger an actuator action
        :param current_value: The current value measured by the PLC
        :param operator: The operator as stored in the control rules
        :param limit: The limit thaea
        t triggers the action
        :return: True if the condition is met. False otherwise
        """
        if operator == '<=':
            if current_value < Decimal(limit):
                return True
        elif operator == '>=':
            if current_value > Decimal(limit):
                return True
        else:
            return False

    def get_control_rules_by_actuator(self, an_actuator):
        """
        This method returns all the control rules that apply to an actuator. A specific control rule only changes the
        state of one actuator
        :param an_actuator:
        :return:
        """
        control_rules = []
        for control in self.plc_dict['Controls']:
            if control['actuator_tag'].upper() == an_actuator.upper():
                control_rules.append(control)
        return control_rules

    def main_loop(self):
        """
        The main loop of a PLC should follow the scan process. 1) Get inputs. 2) Apply control logic 3) Update actuators.
        Inputs can be local self.tags_to_get or remote self.tags_to_receive
        Control logic is composed of a series of simple if control rules
        Actuators are always local
        Sending actuator/sensor information is already handled by pre_loop configuration and BasePLC
        """
        print("Main loop")
        while True:
            try:
                #toDo Implement control flag
                #toDo Implement attacks infrastructure
                self.local_time += 1
                result_list = [self.local_time, datetime.now()]

                # 1) Get inputs
                for tag in self.tags_to_get:
                    tag['value'] = Decimal(self.get(eval(tag['tag'])))

                for tag in self.tags_to_receive:
                    tag['value'] = Decimal(self.receive(eval(tag['tag']), CTOWN_IPS[tag['node']]))

                # 2) Apply control logic, using the current buffered system state
                self.update_actuators()

                time.sleep(0.05)
            except Exception as e:
                print("Exception!")
                print(e)
                time.sleep(0.01)
                continue


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Script that represents PLC/SCADA node in a DHALSIM topology')
    parser.add_argument("--name", "-n", help="Name of the node")
    parser.add_argument("--week", "-w", help="Week index in case demand customization flag is enabled")
    parser.add_argument("--dict", "-d", help="Path of the dictionaries configuration file")
    parser.add_argument("--last", "-l", help="Flag that indicates if this is the last PLC. The last PLC moves the"
                                             "output files into the right output folder")

    args = parser.parse_args()

    plc_name = args.name
    plc_protocol = eval(plc_name.upper()+ "_PROTOCOL")
    plc_data = eval(plc_name.upper() + "_DATA")

    plc1 = PLC(
        name=plc_name,
        state=STATE,
        protocol=plc_protocol,
        memory=plc_data,
        disk=plc_data)