from dhalsim.py3_logger import logger
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
        self.config_path = config_path.absolute()

        logger.debug("config file: %s", str(config_path))

        # Load yaml data from config file
        with config_path.open(mode='r') as file:
            self.config_data = yaml.load(file, Loader=yaml.FullLoader)

        # Assert config data is not empty
        if not self.config_data:
            raise EmptyConfigError

        # Create temp directory and intermediate yaml files in /tmp/
        self.yaml_path = Path("/tmp/dhalsim/intermediate.yaml")
        self.yaml_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def inp_path(self):
        """Property for the path to the inp file

        :return: absolute path to the inp file
        :rtype: Path
        """
        path = self.config_data.get("inp_file")
        if not path:
            raise MissingValueError("inp_file not in config file")
        path = (self.config_path.parent / path).absolute()
        if not path.is_file():
            raise FileNotFoundError(str(path) + " is not a file")
        return path

    @property
    def cpa_path(self):
        """Property for the path to the cpa file

        :return: absolute path to the cpa file
        :rtype: Path
        """
        path = self.config_data.get("cpa_file")
        if not path:
            raise MissingValueError("cpa_file not in config file")
        path = (self.config_path.parent / path).absolute()
        if not path.is_file():
            raise FileNotFoundError(str(path) + " is not a file")
        return path

    @property
    def output_path(self):
        """Property for the path to the output folder
        ``output`` by default

        :return: absolute path to the output folder
        :rtype: Path
        """
        path = self.config_data.get("output_path")
        if not path:
            path = "output"
        path = (self.config_path.parent / path).absolute()
        return path

    @property
    def cpa_data(self):
        """Property to load the yaml data from the cpa file

        :return: data from cpa file
        """
        with self.cpa_path.open() as file:
            cpa = yaml.load(file, Loader=yaml.FullLoader)

        # Verification of plc data
        plcs = cpa.get("plcs")
        if not plcs:
            raise MissingValueError("PLCs section not present in cpa_file")

        # Check for plc names (and check for duplicates)
        plc_list = []
        for plc in plcs:
            if not plc.get("name"):
                raise MissingValueError("PLC in cpa file missing a name")
            else:
                plc_list.append(plc.get("name"))

        if len(plc_list) != len(set(plc_list)):
            raise DuplicateValueError
        return cpa

    @property
    def network_topology_type(self):
        """
        Load the type of topology. This is either `simple` or `complex`.

        :return: the type of the topology
        :rtype: str
        """
        if not "network_topology_type" in self.config_data:
            return "simple"

        network_type = self.config_data["network_topology_type"]

        if type(network_type) != str:
            raise InvalidValueError("network_topology_type must be simple or complex")
        if network_type.lower() != "simple" and network_type.lower() != "complex":
            raise InvalidValueError("network_topology_type must be simple or complex")

        return network_type.lower()

    def generate_intermediate_yaml(self):
        """Writes the intermediate.yaml file to include all options specified in the config, the plc's and their
        data, and all valves/pumps/tanks etc

        :return: the path to the yaml file
        :rtype: Path
        """
        # Begin with PLC data specified in CPA file
        yaml_data = self.cpa_data
        # Add path and database information
        yaml_data["inp_file"] = str(self.inp_path)
        yaml_data["cpa_file"] = str(self.cpa_path)
        yaml_data["output_path"] = str(self.output_path)
        yaml_data["db_path"] = "/tmp/dhalsim/dhalsim.sqlite"
        yaml_data["network_topology_type"] = self.network_topology_type

        # Add options from the config_file
        if "mininet_cli" in self.config_data.keys():
            yaml_data["mininet_cli"] = self.config_data["mininet_cli"]
        else:
            yaml_data["mininet_cli"] = False
        if "simulator" in self.config_data.keys():
            yaml_data["simulator"] = self.config_data["simulator"]
        else:
            yaml_data["simulator"] = "pdd"
        # Note: if iterations not present then default value will be written in InputParser
        if "iterations" in self.config_data.keys():
            yaml_data["iterations"] = self.config_data["iterations"]

        # Write data to yaml file
        with self.yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(yaml_data, intermediate_yaml)

        # Write values from IMP file into yaml file (controls, tanks/valves/initial values, etc.)
        InputParser(self.yaml_path).write()

        return self.yaml_path
