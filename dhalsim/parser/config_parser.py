import logging
import os
import sys
import yaml

from dhalsim.parser.plc_config import PlcConfig

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class EmptyConfigError(Error):
    """Raised when the configuration file is empty"""
    pass


class MissingValueError(Error):
    """Raised when there is a value missing in a configuration file"""
    pass


class ConfigParser:
    def __init__(self, config_path):
        #Set path to the configuration file
        self.config_path = os.path.abspath(config_path)

        logger.debug("config file: %s", config_path)
        #Load yaml data from config file
        with open(config_path) as f:
            self.config_data = yaml.load(f, Loader=yaml.FullLoader)
        #Assert config data is not empty
        if not self.config_data:
            raise EmptyConfigError

    #Property for the path to the inp file
    @property
    def inp_path(self):
        path = self.config_data.get("inp_file")
        if not path:
            raise MissingValueError("inp_file not in config file")
        path = os.path.join(os.path.dirname(self.config_path), path)
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError("%s is not a file", path)
        return path

    #Property for the path to the cpa file
    @property
    def cpa_path(self):
        path = self.config_data.get("cpa_file")
        if not path:
            raise MissingValueError("cpa_file not in config file")
        path = os.path.join(os.path.dirname(self.config_path), path)
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(path + " is not a file")
        return path

    #Property to load the yaml data from the cpa file
    @property
    def cpa_data(self):
        with open(self.cpa_path) as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    #Returns a list of plc configs
    def generate_plc_configs(self):
        plcs = self.cpa_data.get("plcs")

        plc_config_list = []

        if plcs:
            for plc in plcs:
                name = plc.get("name")
                if not name:
                    raise MissingValueError("plc is missing a name")

                sensor_list = []
                sensors = plc.get("sensors")
                if sensors:
                    for sensor in sensors:
                        sensor_list.append(sensor)

                actuator_list = []
                actuators = plc.get("actuators")
                if actuators:
                    for actuator in actuators:
                        actuator_list.append(actuator)

                plc_config_list.append(PlcConfig(name, sensor_list, actuator_list))

        return plc_config_list



if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    parser = ConfigParser(sys.argv[1])
    parser.generate_plc_configs()
