import wntr
import wntr.network.controls as controls
import re
import argparse
import yaml


class EpanetParser:

    """
    This script reads an EPANET inp file and a epanetCPA file and builds a .yaml file with the PLC logic stored in
    EPANET. In addition, the file writes an appropriate utils.py file for the MiniCPS devices and topology
    """
    def __init__(self, inp_file_path, cpa_file_path, out_path):

        if inp_file_path:
            self.inp_file_path = inp_file_path
        else:
            self.inp_file_path = "../../Demand_patterns/ctown_map_with_controls.inp"

        if cpa_file_path:
            self.cpa_file_path = cpa_file_path
        else:
            self.cpa_file_path = "../../Demand_patterns/ctown.cpa"

        if out_path:
            self.out_path = out_path
        else:
            self.out_path = 'plc_dicts.yaml'

        print(("Creating water network model with " + str(self.inp_file_path) + " file"))
        self.wn = wntr.network.WaterNetworkModel(self.inp_file_path)
        self.control_list = self.create_control_list()
        self.plc_list = self.create_plc_list()

        # topology name
        self.topology_name = "plant"

        # Network information. Hardwired for now
        self.plc_netmask = "'/24'"
        self.enip_listen_plc_addr = "'192.168.1.1'"
        self.scada_ip_addr = "'192.168.1.2'"

    def main(self):

        self.configure_plc_list()

        ### Creating the dictionary with the IP addresses of the PLCs
        plc_index = 1
        ip_string = ""

        plc_data_string = ""

        # PLC Tags
        plc_tags = []

        # PLC Servers
        plc_servers = ""

        # PLC protocols
        plc_protocols = ""



        # SCADA information
        scada_tags = "SCADA_TAGS = ("
        scada_server = "SCADA_SERVER = {\n    'address': SCADA_IP_ADDR,\n    'tags': SCADA_TAGS\n}\n"
        scada_protocol = "SCADA_PROTOCOL = {\n    'name': 'enip',\n    'mode': 1,\n    'server': SCADA_SERVER\n}\n"

        # For the DB tags, is better to refer to self.wnTR as epanet.INP and cpa files may not provide the full
        # list of pumps and valves
        # Creating the tags strings. We need to differentiate between sensor and actuator tags, because we get their
        # initial values/status in different ways from WaterNetworkModel

        # start create db_tags_method
        db_sensor_list = []
        db_actuator_list = []
        db_tags = []
        a_link_list = list(self.wn.link_name_list)
        a_node_list = list(self.wn.node_name_list)
        db_actuator_list.extend(self.get_link_list_by_type(a_link_list, 'Valve'))
        db_actuator_list.extend(self.get_link_list_by_type(a_link_list, 'Pump'))
        db_sensor_list.extend(self.get_node_list_by_type(a_node_list, 'Tank'))
        db_tags.extend(db_actuator_list)
        db_tags.extend(db_sensor_list)
        # end create db_tags_method

        tags_strings = []

        for tag in db_tags:
            tag_dict = {}
            tag_dict['name'] = tag
            tag_dict['string'] = "('" + tag + "', 1)"
            tags_strings.append(tag_dict)
            scada_tags += "\n    ('" + tag + "', 1, 'REAL'),"

        scada_tags = scada_tags + "\n)\n"

        # Control fag to sync actuators and physical process
        tag_dict = {}
        tag_dict['name'] = 'CONTROL'
        tag_dict['string'] = "('CONTROL', 1)"
        tags_strings.append(tag_dict)
        # ############# PLC ENIP address configuration

        for plc in self.plc_list:
            ip_string += "    '" + plc['PLC'].lower() + "':'10.0." + str(plc_index) + ".1',\n"

            plc_data_string += "\nPLC" + str(plc_index) + "_DATA = {\n    'TODO': 'TODO',\n}\n"
            a_plc_tag_string = "PLC" + str(plc_index) + "_TAGS = ("
            tag_string = ""
            for tag in plc['Sensors']:
                if tag != "":
                    tag_string += "\n    ('" + tag + "', 1, 'REAL'),"

            for tag in plc['Actuators']:
                if tag != "":
                    tag_string += "\n    ('" + tag + "', 1, 'REAL'),"

            for dependency in plc['Dependencies']:
                if dependency:
                    tag_string += "\n    ('" + dependency['tag'] + "', 1, 'REAL'),"

            tag_string += "\n    ('CONTROL', 1, 'REAL'),"

            a_plc_tag_string += tag_string + "\n)"
            plc_tags.append(a_plc_tag_string)

            plc_servers += "PLC" + str(
                plc_index) + "_SERVER = {\n    'address': ENIP_LISTEN_PLC_ADDR,\n    'tags': PLC" + str(
                plc_index) + "_TAGS\n}\n"
            plc_protocols += "PLC" + str(
                plc_index) + "_PROTOCOL = {\n    'name': 'enip',\n    'mode': 1,\n    'server': PLC" + str(
                plc_index) + "_SERVER\n}\n"

            plc_index += 1

        plc_data_string += "SCADA_DATA = {\n    'TODO': 'TODO',\n}\n"

        ctown_ips_prefix = "CTOWN_IPS = {\n"
        ctown_ips = ctown_ips_prefix + ip_string + "}"

        # ################## DB creation strings

        path_string = "PATH = 'plant.sqlite'"
        name_string = "NAME = '" + self.topology_name + "'"

        state_string = "STATE = {\n    'name': NAME,\n    'path': PATH\n}"

        comas = '"' * 3
        schema_string = 'SCHEMA = ' + comas + '\
        \nCREATE TABLE ' + self.topology_name + ' (\
        \n    name              TEXT NOT NULL,\
        \n    pid               INTEGER NOT NULL,\
        \n    value             TEXT,\
        \n    PRIMARY KEY (name, pid)\
        \n);\n' + comas

        db_tag_string = "SCHEMA_INIT = " + comas + "\n"
        for tag in db_sensor_list:
            db_tag_string += "    INSERT INTO " + self.topology_name + " VALUES ('" + tag + "', 1, '" + str(
                self.get_sensor_initial_value(tag)) + "');\n"

        for tag in db_actuator_list:
            db_tag_string += "    INSERT INTO " + self.topology_name + " VALUES ('" + tag + "', 1, '" + str(
                self.get_actuator_initial_value(tag)) + "');\n"

        db_tag_string += "    INSERT INTO " + self.topology_name + " VALUES ('ATT_1', 1, '0');\n"
        db_tag_string += "    INSERT INTO " + self.topology_name + " VALUES ('ATT_2', 1, '0');\n"
        db_tag_string += "    INSERT INTO " + self.topology_name + " VALUES ('CONTROL', 1, '0');\n"
        db_tag_string += comas

        # ########## Writing the utils file ########################################3
        # Erase the file contents
        utils_file = open("utils.py", "w")
        utils_file.write("")
        utils_file.close()

        utils_file = open("utils.py", "a")
        for tag in tags_strings:
            utils_file.write(tag['name'] + " = " + tag['string'] + "\n")

        utils_file.write("\nplc_netmask = " + self.plc_netmask + "\n")
        utils_file.write("ENIP_LISTEN_PLC_ADDR = " + self.enip_listen_plc_addr + "\n")
        utils_file.write("SCADA_IP_ADDR = " + self.scada_ip_addr + "\n")

        utils_file.write("\n" + ctown_ips + "\n")
        utils_file.write(plc_data_string + "\n")

        for plc in plc_tags:
            utils_file.write("\n" + plc + "\n")

        utils_file.write("\n" + scada_tags)

        # this is only temporal. With the revamp of the attacks, this will be done differently
        utils_file.write("\nflag_attack_communication_plc1_plc2_replay_empty = 0\n")
        utils_file.write("flag_attack_plc1 = 0\n")
        utils_file.write("flag_attack_communication_plc1_plc2 = 0\n")
        utils_file.write("ATT_1 = ('ATT_1', 1)\n")
        utils_file.write("ATT_2 = ('ATT_2', 1)\n")
        utils_file.write("\n" + plc_servers)
        utils_file.write("\n" + scada_server)
        utils_file.write("\n" + plc_protocols)
        utils_file.write("\n" + scada_protocol)
        utils_file.write("\n" + path_string)
        utils_file.write("\n" + name_string + "\n")
        utils_file.write("\n" + state_string + "\n")
        utils_file.write("\n" + schema_string + "\n")
        utils_file.write("\n" + db_tag_string)

        utils_file.close()

        with open(self.out_path, 'w') as outfile:
            yaml.dump(self.plc_list, outfile, default_flow_style=True)

    def configure_plc_list(self):
        for i in range(len(self.plc_list)):
            self.plc_list[i] = self.set_control_list_in_plc(self.plc_list[i], self.control_list)
        self.set_dependencies_list_in_plc(self.plc_list)

    def get_control_rule_with_tag(self, a_tag):
        for control in self.control_list:
            if a_tag in control['actuator_tag']:
                return control

    def create_control_list(self):
        control_list = []
        for control in self.wn.intermediate_controls():
            control_dict = {}
            control_dict['tank_tag'] = control[1].condition.name.split(":")[0]
            control_dict['operator'] = control[1].condition.name.split("level")[1][0:2]
            control_dict['value'] = control[1].condition.name.split("=")[1]
            control_dict['actuator_tag'] = str(control[1].actions()[0].target()[0])
            control_dict['actuator_value'] = str(control[1].actions()[0]).split("to")[1].strip()
            control_list.append(control_dict)
        return control_list

    def create_plc_list(self):
        section_exp = re.compile(r'\[(.*)\]')
        plc_exp = re.compile(r'^PLC')
        plcs = []
        nodes_section = False
        with open(self.cpa_file_path, 'r') as file_object:
                for line in file_object:
                    if section_exp.match(line) and line == '[CYBERNODES]\n':
                        nodes_section=True
                        continue
                    if section_exp.match(line) and line != '[CYBERNODES]\n':
                        nodes_section=False
                    if nodes_section and line[0] != ";":
                        nodes=line.split(",")
                        if plc_exp.match(nodes[0].strip()):
                            plc_dict = {}
                            plc_dict['PLC'] = nodes[0].strip()
                            plc_dict['Sensors'] = nodes[1].strip().split(" ")
                            plc_dict['Actuators'] = nodes[2].strip().split(" ")
                            plc_dict['Controls'] = []
                            plcs.append(plc_dict)
        return plcs

    def set_control_list_in_plc(self, a_plc_dict, a_control_list):
        plc_controls = []
        for actuator in a_plc_dict['Actuators']:
            for control in a_control_list:
                if actuator == control['actuator_tag']:
                    plc_controls.append(control)
        a_plc_dict['Controls'] = plc_controls
        return a_plc_dict

    def set_dependencies_list_in_plc(self, a_plc_list):
        for plc in a_plc_list:
            dependencies_list = []
            tag_set = set()
            for control in plc['Controls']:
                tag_set.add(control['tank_tag'])
            if tag_set:
                for tag in tag_set:
                    for target_plc in a_plc_list:
                        if plc == target_plc:
                            continue
                        for sensor in target_plc['Sensors']:
                            if tag == sensor:
                                dependency_dict = {}
                                dependency_dict['tag'] = tag
                                dependency_dict['PLC'] = target_plc['PLC']
                                dependencies_list.append(dependency_dict)
            plc['Dependencies'] = dependencies_list

    def get_sensor_initial_value(self, sensor_tag):
        return self.wn.get_node(sensor_tag).init_level

    def get_actuator_initial_value(self, actuator_tag):
        if type(self.wn.get_link(actuator_tag).status) is int:
            return self.wn.get_link(actuator_tag).status
        else:
            return self.wn.get_link(actuator_tag).status.value

    def get_link_list_by_type(self, a_list, a_type):
        result = []
        for link in a_list:
            if self.wn.get_link(link).link_type == a_type:
                result.append(str(link))
        return result

    def get_node_list_by_type(self, a_list, a_type):
        result = []
        for node in a_list:
            if self.wn.get_node(node).node_type == a_type:
                result.append(str(node))
        return result


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Script that parses an EPANET inp and epanetCPA file to build PLC behaviour')
    parser.add_argument("--inp", "-i",help="Path to the EPANET inp file")
    parser.add_argument("--cpa", "-a", help="Path to the epanetCPA file")
    parser.add_argument("--out", "-o", help="Path of the output utils file")

    args = parser.parse_args()
    parser = EpanetParser(args.inp, args.cpa, args.out)
    parser.main()