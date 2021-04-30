import logging
import os
import sys
import yaml

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class EmptyConfigError(Error):
    """Raised when the input value is too small"""
    pass


class MissingValueError(Error):
    """Raised when the input value is too small"""
    pass


class ConfigParser():
    def __init__(self, config_path):

        self.config_path = os.path.abspath(config_path)

        logger.debug("config file: %s", config_path)

        with open(config_path) as f:
            self.config_data = yaml.load(f, Loader=yaml.FullLoader)

        if not self.config_data:
            raise EmptyConfigError

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

    @property
    def cpa_path(self):
        path = self.config_data.get("cpa_file")
        if not path:
            raise MissingValueError("cpa_file not in config file")
        path = os.path.join(os.path.dirname(self.config_path), path)
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError("%s is not a file", path)
        return path

    @property
    def cpa_data(self):
        with open(self.cpa_path) as f:
            return yaml.load(f, Loader=yaml.FullLoader)


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    parser = ConfigParser(sys.argv[1])
    print(parser.inp_path)
