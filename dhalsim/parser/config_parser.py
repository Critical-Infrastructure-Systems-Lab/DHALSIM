import logging
import sys
from pathlib import Path

import pandas as pd
import yaml

from dhalsim.parser.input_parser import InputParser


class Error(Exception):
    """Base class for exceptions in this module."""


class EmptyConfigError(Error):
    """Raised when the configuration file is empty"""


class MissingValueError(Error):
    """Raised when there is a value missing in a configuration file"""


class InvalidValueError(Error):
    """Raised when there is a invalid value in a configuration file"""


class DuplicateValueError(Error):
    """Raised when there is a duplicate plc value in the cpa file"""


class NoSuchPlc(Error):
    """Raised when an attack targets a PLC that does not exist"""

class NoSuchTag(Error):
    """Raised when an attack targets a tag the target PLC does not have"""


class ConfigParser:
    """
    Class handling the parsing of the input config data.

    :param config_path: The path to the config file of the experiment in yaml format
    :type config_path: Path
    """

    def __init__(self, config_path: Path):
        """Constructor method"""
        self.batch_index = None
        self.config_path = config_path.absolute()

        # Load yaml data from config file
        with config_path.open(mode='r') as file:
            self.config_data = yaml.load(file, Loader=yaml.FullLoader)

        # Assert config data is not empty
        if not self.config_data:
            raise EmptyConfigError

        # Create temp directory and intermediate yaml files in /tmp/
        self.yaml_path = Path("/tmp/dhalsim/intermediate.yaml")
        self.yaml_path.parent.mkdir(parents=True, exist_ok=True)

    def get_path(self, path_input):
        """
        Function that returns a given path if it exists

        :param path_input: Path that should be returned
        :type path_input: str
        :return: absolute path to the file
        :rtype: Path
        """
        path = self.config_data.get(path_input)
        if not path:
            raise MissingValueError(path_input + " not in config file.")
        path = (self.config_path.parent / path).absolute()
        if not path.is_file():
            raise FileNotFoundError(str(path) + " is not a file.")
        return path

    @property
    def output_path(self):
        """
        Property for the path to the output folder.
        ``output`` by default.

        :return: absolute path to the output folder
        :rtype: Path
        """
        path = self.config_data.get('output_path')
        if not path:
            path = 'output'
        path = (self.config_path.parent / path).absolute()
        return path

    @property
    def inp_file(self):
        """
        Property for the path to the inp file.

        :return: absolute path to the inp file
        :rtype: Path
        """
        return self.get_path('inp_file')

    @property
    def cpa_file(self):
        """
        Property for the path to the cpa file.

        :return: absolute path to the cpa file
        :rtype: Path
        """
        return self.get_path('cpa_file')

    @property
    def initial_tank_data(self):
        """
        Property for the path to the initial tank data file.

        :return: absolute path to the initial tank data file
        :rtype: Path
        """
        return self.get_path('initial_tank_data')

    @property
    def network_loss_data(self):
        """
        Property for the path to the network loss data file.

        :return: absolute path to the inp file
        :rtype: Path
        """
        return self.get_path('network_loss_data')

    @property
    def network_delay_data(self):
        """
        Property for the path to the network delay data file.

        :return: absolute path to the inp file
        :rtype: Path
        """
        return self.get_path('network_delay_data')

    @property
    def demand_patterns(self):
        """
        Function that returns path to demand pattern csv

        :return: absolute path to the demand pattern csv
        :rtype: Path
        """
        path = self.config_data.get('demand_patterns')
        if not path:
            raise MissingValueError("demand_patterns not in config file.")

        # If running in batch mode, then have to use batch index in name
        if self.batch_mode:
            path = str(path) + str(self.batch_index) + '.csv'

        path = (self.config_path.parent / path).absolute()
        if not path.is_file():
            raise FileNotFoundError(str(path) + " is not a file.")
        return path

    @property
    def cpa_data(self):
        """Property to load the yaml data from the cpa file.

        :return: data from cpa file
        """
        with self.get_path('cpa_file').open() as file:
            cpa = yaml.load(file, Loader=yaml.FullLoader)

        # Verification of plc data
        plcs = cpa.get('plcs')
        if not plcs:
            raise MissingValueError("PLCs section not present in cpa_file.")

        # Check for plc names (and check for duplicates)
        plc_list = []
        for plc in plcs:
            if not plc.get('name'):
                raise MissingValueError("PLC in cpa file missing a name.")
            else:
                plc_list.append(plc.get('name'))

        if len(plc_list) != len(set(plc_list)):
            raise DuplicateValueError
        return cpa

    @property
    def attacks_data(self):
        """
        Property to load attacks from the attacks file specified in the config file

        :return: data from the attack file
        """
        with self.get_path('attacks_path').open(mode='r') as attacks_description:
            attacks = yaml.safe_load(attacks_description)

        return attacks

    @property
    def network_topology_type(self):
        """
        Load the type of topology. This is either `simple` or `complex`.

        :return: the type of the topology
        :rtype: str
        """
        if not 'network_topology_type' in self.config_data:
            return 'simple'

        network_type = self.config_data["network_topology_type"]

        if type(network_type) != str:
            raise InvalidValueError("network_topology_type must be simple or complex.")
        if network_type.lower() != 'simple' and network_type.lower() != 'complex':
            raise InvalidValueError("network_topology_type must be simple or complex.")

        return network_type.lower()

    def generate_device_attacks(self, yaml_data):
        """
        This function will add device attacks to the appropriate PLCs in the intermediate yaml

        :param yaml_data: The YAML data without the device attacks
        """
        for device_attack in self.attacks_data['device_attacks']:
            for plc in yaml_data['plcs']:
                if device_attack['actuator'] in plc['actuators']:
                    if 'attacks' not in plc.keys():
                        plc['attacks'] = []
                    plc['attacks'].append(device_attack)
                    break
        return yaml_data


    def get_boolean(self, config_str, default_value):
        """
        Load the config_str. This is either `true` or `false`.

        :param config_str: name of config value in config file
        :type config_str: str
        :param default_value: default value of the boolean
        :type default_value: bool
        :return: boolean of config_str
        :rtype: boolean
        """
        if config_str not in self.config_data:
            return default_value

        config_boolean = self.config_data[config_str]

        if type(config_boolean) != bool:
            raise InvalidValueError("batch_mode must be a boolean (true or false)")

        return config_boolean

    @property
    def batch_mode(self):
        """
        Load the batch mode boolean. This is either `true` or `false`.

        :return: boolean of batch mode boolean
        :rtype: boolean
        """
        return self.get_boolean('batch_mode', False)

    @property
    def mininet_cli(self):
        """
        Load the mininet cli boolean. This is either `true` or `false`.

        :return: boolean of mininet cli
        :rtype: boolean
        """
        return self.get_boolean("mininet_cli", False)

    def generate_attacks(self, yaml_data):
        if 'run_attack' in self.config_data.keys() and self.config_data['run_attack']:
            if 'device_attacks' in self.attacks_data.keys():
                for device_attack in self.attacks_data['device_attacks']:
                    for plc in yaml_data['plcs']:
                        if set(device_attack['actuators']).issubset(set(plc['actuators'])):
                            if 'attacks' not in plc.keys():
                                plc['attacks'] = []
                            plc['attacks'].append(device_attack)
                            break
        return yaml_data

    def generate_network_attacks(self, network_attacks):
        """
        This function will add device attacks to the appropriate PLCs in the intermediate yaml

        :param network_attacks: The YAML data of the network attacks
        """
        for network_attack in network_attacks:
            if "name" not in network_attack:
                raise MissingValueError("No name specified an network attack")

            # Check existence and validity of network attack type
            if "type" not in network_attack:
                raise MissingValueError("No type specified for network attack {name}".format(name=network_attack["name"]))
            network_attack['type'] = network_attack['type'].lower()
            if network_attack['type'] not in ['mitm']:
                raise InvalidValueError(f"{network_attack['type']} is not a valid network attack type")

            # Check existence and validity of target PLC
            if "target" not in network_attack:
                raise MissingValueError("No target specified for network attack {name}".format(name=network_attack["name"]))
            target = network_attack['target']
            target_plc = None
            for plc in self.cpa_data.get("plcs"):
                if plc['name'] == target:
                    target_plc = plc
                    break
            if not target_plc:
                raise NoSuchPlc("PLC {plc} does not exists".format(plc=target))

            if "trigger" not in network_attack:
                raise MissingValueError("No trigger specified for network attack {name}".format(name=network_attack["name"]))

            if "type" not in network_attack["trigger"]:
                raise MissingValueError("No trigger type specified for network attack {name}".format(name=network_attack["name"]))

            network_attack["trigger"]["type"] = network_attack["trigger"]["type"].lower()

            if network_attack["trigger"]["type"] == 'time':
                if "start" not in network_attack["trigger"]:
                    raise MissingValueError("No start time specified for network attack {name}".format(name=network_attack["name"]))
                if "end" not in network_attack["trigger"]:
                    raise MissingValueError("No end time specified for network attack {name}".format(name=network_attack["name"]))
            elif network_attack["trigger"]["type"] == 'between':
                if "lower_value" not in network_attack["trigger"]:
                    raise MissingValueError("No lower_value specified for network attack {name}".format(name=network_attack["name"]))
                if "upper_value" not in network_attack["trigger"]:
                    raise MissingValueError("No upper_value specified for network attack {name}".format(name=network_attack["name"]))
            elif network_attack["trigger"]["type"] == 'above' or network_attack["trigger"]["type"] == 'below':
                if "value" not in network_attack["trigger"]:
                    raise MissingValueError("No value specified for network attack {name}".format(name=network_attack["name"]))
            else:
                raise InvalidValueError("Trigger type should be either 'time', 'between', 'above' or 'below' for network attack {name}".format(name=network_attack["name"]))

            # Check existence of tags on target PLC
            tags = []
            for tag in network_attack['tags']:
                tags.append(tag['tag'])
            if not set(tags).issubset(set(target_plc['actuators'] + target_plc['sensors'])):
                raise NoSuchTag(f"PLC {target_plc['name']} does not have all the tags specified.")

        return network_attacks

    def generate_intermediate_yaml(self):
        """Writes the intermediate.yaml file to include all options specified in the config, the plc's and their
        data, and all valves/pumps/tanks etc.

        :return: the path to the yaml file
        :rtype: Path
        """
        # Begin with PLC data specified in CPA file
        yaml_data = self.cpa_data
        # Add path and database information
        yaml_data['inp_file'] = str(self.inp_file)
        yaml_data['cpa_file'] = str(self.cpa_file)
        yaml_data['output_path'] = str(self.output_path)
        yaml_data['db_path'] = "/tmp/dhalsim/dhalsim.sqlite"
        yaml_data['network_topology_type'] = self.network_topology_type
        # Add batch mode parameters
        yaml_data['batch_mode'] = self.batch_mode
        if yaml_data['batch_mode']:
            yaml_data['batch_index'] = self.batch_index
        # Initial physical values
        if 'initial_tank_data' in self.config_data:
            yaml_data['initial_tank_data'] = str(self.initial_tank_data)
        if 'demand_patterns' in self.config_data:
            yaml_data['demand_patterns_data'] = str(self.demand_patterns)
        # Add network loss parameters
        if 'network_loss_data' in self.config_data:
            yaml_data['network_loss_data'] = str(self.network_loss_data)
        # Add network delay parameters
        if 'network_delay_data' in self.config_data:
            yaml_data['network_delay_data'] = str(self.network_delay_data)
        # Mininet cli parameter
        yaml_data['mininet_cli'] = self.mininet_cli

        if 'simulator' in self.config_data:
            yaml_data['simulator'] = self.config_data['simulator']
        else:
            yaml_data['simulator'] = 'pdd'

        # Note: if iterations not present then default value will be written in InputParser
        if 'iterations' in self.config_data:
            yaml_data['iterations'] = self.config_data['iterations']

        # Log level
        if 'log_level' in self.config_data:
            if self.config_data['log_level'] in ['debug', 'info', 'warning', 'error', 'critical']:
                yaml_data['log_level'] = self.config_data['log_level']
            else:
                raise InvalidValueError("Invalid log_level value.")
        else:
            yaml_data['log_level'] = 'info'

        # Write values from IMP file into yaml file (controls, tanks/valves/initial values, etc.)
        yaml_data = InputParser(yaml_data).write()

        # Parse the device attacks from the config file
        if "attacks_path" in self.config_data.keys():
            if self.attacks_data is not None:
                if 'device_attacks' in self.attacks_data.keys():
                    yaml_data = self.generate_device_attacks(yaml_data)
                if "network_attacks" in self.attacks_data.keys():
                    yaml_data["network_attacks"] = self.generate_network_attacks(self.attacks_data["network_attacks"])

        # Write data to yaml file
        with self.yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(yaml_data, intermediate_yaml)

        return self.yaml_path
