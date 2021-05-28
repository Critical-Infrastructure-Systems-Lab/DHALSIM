import os
import tempfile
from pathlib import Path

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

        self.batch_mode = 'batch_simulations' in self.config_data

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
        # If path not provided, then create default
        if not path:
            # If running in batch mode, output to batch folder
            if self.batch_mode:
                path = 'output/batch_' + str(self.batch_index)
            # Else just output
            else:
                path = 'output'
        else:
            # If running in batch mode, output to batch folder
            if self.batch_mode:
                path += '/batch_' + str(self.batch_index)
        return (self.config_path.parent / path).absolute()

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
    def mininet_cli(self):
        """
        Load the mininet cli boolean. This is either `true` or `false`.

        :return: boolean of mininet cli
        :rtype: boolean
        """
        return self.get_boolean("mininet_cli", False)

    @property
    def batch_simulations(self):
        """
        Load the number of batch simulations, and verify that it is a number

        :return: number of batch simulations
        :rtype: int
        """
        simulations = self.config_data['batch_simulations']

        if type(simulations) != int:
            raise InvalidValueError("'batch_simulations' must be an integer")

        return simulations

    @property
    def iterations(self):
        """
        Load the simulation iterations, and verify that it is a number

        :return: number of simulation iterations
        :rtype: int
        """
        iterations = self.config_data['iterations']

        if type(iterations) != int:
            raise InvalidValueError("'iterations' must be an integer")

        return iterations

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

    def generate_temporary_dirs(self):
        """Generates the temporary directory and yaml/db paths"""
        # Create temp directory and intermediate yaml files in /tmp/
        temp_directory = tempfile.mkdtemp(prefix='dhalsim_')
        # Change read permissions in tempdir
        os.chmod(temp_directory, 0o777)
        self.yaml_path = Path(temp_directory + '/intermediate.yaml')
        self.db_path = temp_directory + '/dhalsim.sqlite'

    def generate_intermediate_yaml(self):
        """Writes the intermediate.yaml file to include all options specified in the config, the plc's and their
        data, and all valves/pumps/tanks etc.

        :return: the path to the yaml file
        :rtype: Path
        """
        self.generate_temporary_dirs()

        # Begin with PLC data specified in CPA file
        yaml_data = self.cpa_data
        # Add path and database information
        yaml_data['inp_file'] = str(self.inp_file)
        yaml_data['cpa_file'] = str(self.cpa_file)
        yaml_data['output_path'] = str(self.output_path)
        yaml_data['db_path'] = self.db_path
        yaml_data['network_topology_type'] = self.network_topology_type

        # Add batch mode parameters
        if self.batch_mode:
            yaml_data['batch_index'] = self.batch_index
            yaml_data['batch_simulations'] = self.batch_simulations
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
            yaml_data['iterations'] = self.iterations

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
        yaml_data = self.generate_attacks(yaml_data)

        # Write data to yaml file
        with self.yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(yaml_data, intermediate_yaml)

        return self.yaml_path
