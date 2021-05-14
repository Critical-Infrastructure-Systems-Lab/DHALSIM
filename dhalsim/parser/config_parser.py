import logging
import os
import pathlib

import yaml

from dhalsim.parser.input_parser import InputParser

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base class for exceptions in this module."""


class EmptyConfigError(Error):
    """Raised when the configuration file is empty"""


class MissingValueError(Error):
    """Raised when there is a value missing in a configuration file"""


class ConfigParser:
    """
    Class handling the parsing of the input config data.

    :param config_path: The path to the config file of the experiment in yaml format
    :type config_path: str
    """

    def __init__(self, config_path):
        """Constructor method
        """
        self.config_path = os.path.abspath(config_path)

        logger.debug("config file: %s", config_path)
        # Load yaml data from config file
        with open(config_path) as file:
            self.config_data = yaml.load(file, Loader=yaml.FullLoader)
        # Assert config data is not empty
        if not self.config_data:
            raise EmptyConfigError
        # Create temp directory and intermediate yaml files in /tmp/
        self.yaml_path = pathlib.Path("/tmp/dhalsim/intermediate.yaml")
        self.yaml_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def inp_path(self):
        """Property for the path to the inp file

        :return: absolute path to the inp file
        :rtype: str
        """
        path = self.config_data.get("inp_file")
        if not path:
            raise MissingValueError("inp_file not in config file")
        path = os.path.join(os.path.dirname(self.config_path), path)
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(path + " is not a file")
        return path

    @property
    def cpa_path(self):
        """Property for the path to the cpa file

        :return: absolute path to the cpa file
        :rtype: str
        """
        path = self.config_data.get("cpa_file")
        if not path:
            raise MissingValueError("cpa_file not in config file")
        path = os.path.join(os.path.dirname(self.config_path), path)
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(path + " is not a file")
        return path

    @property
    def cpa_data(self):
        """Property to load the yaml data from the cpa file

        :return: data from cpa file
        """
        with open(self.cpa_path) as file:
            return yaml.load(file, Loader=yaml.FullLoader)

    def generate_intermediate_yaml(self):
        """Writes the intermediate.yaml file to include all options specified in the config, the plc's and their
        data, and all valves/pumps/tanks etc
        """
        # Begin with PLC data specified in CPA file
        yaml_data = self.cpa_data
        # Add path and database information
        yaml_data["inp_file"] = self.inp_path
        yaml_data["cpa_file"] = self.cpa_path
        yaml_data["db_path"] = "/tmp/dhalsim/dhalsim.sqlite"

        # Add options from the config_file
        if "mininet_cli" in self.config_data.keys():
            yaml_data["mininet_cli"] = self.config_data["mininet_cli"]
        else:
            yaml_data["mininet_cli"] = False

        if "simulator" in self.config_data.keys():
            yaml_data["simulator"] = self.config_data["simulator"]
        else:
            yaml_data["simulator"] = "pdd"

        if "iterations" in self.config_data.keys():
            yaml_data["iterations"] = self.config_data["iterations"]

        if "run_attack" in self.config_data.keys():
            yaml_data["run_attack"] = self.config_data["run_attack"]
        else:
            yaml_data["run_attack"] = False

        # Write data to yaml file
        with self.yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(yaml_data, intermediate_yaml)

        # todo: and initial values

        # Write values from IMP file into yaml file (controls, tanks/valves/initial values, etc.)
        InputParser(self.yaml_path).write()
