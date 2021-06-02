import os
import sys
import tempfile
from pathlib import Path

import yaml
from yamlinclude import YamlIncludeConstructor
from schema import Schema, Or, And, Use, Optional, SchemaError, Regex

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
        self.yaml_path = None
        self.db_path = None

        self.config_path = config_path.absolute()

        YamlIncludeConstructor.add_to_loader_class(loader_class=yaml.FullLoader, base_dir=config_path.absolute().parent)

        try:
            self.data = self.apply_schema(self.config_path)
        except SchemaError as exc:
            sys.exit(exc.code)

        self.batch_mode = 'batch_simulations' in self.data

    @staticmethod
    def apply_schema(config_path: Path) -> dict:
        data = ConfigParser.load_yaml(config_path)
        data = ConfigParser.path_schema(data, config_path)
        return ConfigParser.validate_schema(data)

    @staticmethod
    def path_schema(data: dict, config_path: Path) -> dict:
        return Schema(
            And(
                {
                    'inp_file': And(
                        Use(Path),
                        Use(lambda p: config_path.absolute().parent / p),
                        Path.is_file,
                        Schema(lambda f: f.suffix == '.inp', error="Suffix of inp_file should be .inp")),
                    Optional('output_path', default=config_path.absolute().parent / 'output'): And(
                        Use(str),
                        Use(Path),
                        Use(lambda p: config_path.absolute().parent / p),
                    ),
                    Optional('initial_tank_data'): And(
                        Use(Path),
                        Use(lambda p: config_path.absolute().parent / p),
                        Path.is_file,
                        Schema(lambda f: f.suffix == '.csv', error="Suffix of initial_tank_data should be .csv")),
                    Optional('demand_patterns'): And(
                        Use(Path),
                        Use(lambda p: config_path.absolute().parent / p),
                        Path.exists,
                        Or(
                            Path.is_dir,
                            Schema(lambda f: f.suffix == '.csv', error="Suffix of demand_patterns should be .csv"))),
                    Optional('network_loss_data'): And(
                        Use(Path),
                        Use(lambda p: config_path.absolute().parent / p),
                        Path.is_file,
                        Schema(lambda f: f.suffix == '.csv', error="Suffix of network_loss_data should be .csv")),
                    Optional('network_delay_data'): And(
                        Use(Path),
                        Use(lambda p: config_path.absolute().parent / p),
                        Path.is_file,
                        Schema(lambda f: f.suffix == '.csv', error="Suffix of network_delay_data should be .csv")),
                    str: object
                }
            )
        ).validate(data)

    @staticmethod
    def load_yaml(path: Path) -> dict:
        try:
            with path.open(mode='r') as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
            return data
        except FileNotFoundError as exc:
            sys.exit(f"File not found: {exc.filename}")

    @staticmethod
    def validate_schema(data: dict) -> dict:
        string_pattern = Regex(r'^[a-zA-Z0-9_]+$', error="Error in string: '{}', Can only have a-z, A-Z, 0-9, and _")

        attacks_schema = Schema({
            str: object
        })

        plc_schema = Schema([{
            'name': string_pattern,
            Optional('sensors'): [string_pattern],
            Optional('actuators'): [string_pattern]
        }])

        config_schema = Schema({
            'plcs': plc_schema,
            'inp_file': Path,
            Optional('network_topology_type', default='simple'): And(
                str,
                Use(str.lower),
                Or('complex', 'simple')),
            'output_path': Path,
            'iterations': And(
                int,
                Schema(lambda i: i > 0, error='iterations must be positive')),
            Optional('mininet_cli', default=False): bool,
            Optional('log_level', default='info'): And(
                str,
                Use(str.lower),
                Or('debug', 'info', 'warning', 'error', 'critical')),
            Optional('simulator', default='pdd'): And(
                str,
                Use(str.lower),
                Or('pdd', 'dd')),
            Optional('run_attack', default=True): bool,
            Optional('attacks'): attacks_schema,
            Optional('batch_simulations'): And(
                int,
                Schema(lambda i: i > 0, error='batch_simulations must be positive')),
            Optional('initial_tank_data'): Path,
            Optional('demand_patterns'): Path,
            Optional('network_loss_data'): Path,
            Optional('network_delay_data'): Path,
        })

        return config_schema.validate(data)

    @property
    def output_path(self):
        """
        Property for the path to the output folder.
        ``output`` by default.

        :return: absolute path to the output folder
        :rtype: Path
        """
        path = self.data.get('output_path')
        if self.batch_mode:
            path /= 'batch_' + str(self.batch_index)
        return path

    @property
    def demand_patterns(self):
        """
        Function that returns path to demand pattern csv

        :return: absolute path to the demand pattern csv
        :rtype: Path
        """
        path = self.data.get('demand_patterns')

        # If running in batch mode, then have to use batch index in name
        if self.batch_mode:
            path /= str(self.batch_index) + '.csv'

        if not path.is_file():
            raise FileNotFoundError(str(path) + " is not a file.")
        return path

    def generate_attacks(self, yaml_data):
        if self.data.get('run_attack'):
            if self.data.get('attacks'):
                for device_attack in self.data.get('attacks').get('device_attacks'):
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

        yaml_data = {}

        # Begin with PLC data specified in CPA file
        yaml_data['plcs'] = self.data.get('plcs')
        # Add path and database information
        yaml_data['inp_file'] = str(self.data.get('inp_file'))
        yaml_data['output_path'] = str(self.output_path)
        yaml_data['db_path'] = self.db_path
        yaml_data['network_topology_type'] = self.data.get('network_topology_type')

        # Add batch mode parameters
        if self.batch_mode:
            yaml_data['batch_index'] = self.batch_index
            yaml_data['batch_simulations'] = self.data.get('batch_simulations')
        # Initial physical values
        if 'initial_tank_data' in self.data:
            yaml_data['initial_tank_data'] = str(self.data.get('initial_tank_data'))
        if 'demand_patterns' in self.data:
            yaml_data['demand_patterns_data'] = str(self.demand_patterns)
        # Add network loss parameters
        if 'network_loss_data' in self.data:
            yaml_data['network_loss_data'] = str(self.data.get('network_loss_data'))
        # Add network delay parameters
        if 'network_delay_data' in self.data:
            yaml_data['network_delay_data'] = str(self.data.get('network_delay_data'))
        # Mininet cli parameter
        yaml_data['mininet_cli'] = self.data.get('mininet_cli')

        # Simulator
        yaml_data['simulator'] = self.data['simulator']

        # Note: if iterations not present then default value will be written in InputParser
        yaml_data['iterations'] = self.data['iterations']

        # Log level
        yaml_data['log_level'] = self.data['log_level']

        # Write values from IMP file into yaml file (controls, tanks/valves/initial values, etc.)
        yaml_data = InputParser(yaml_data).write()

        # Parse the device attacks from the config file
        yaml_data = self.generate_attacks(yaml_data)

        # Write data to yaml file
        with self.yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(yaml_data, intermediate_yaml)

        return self.yaml_path
