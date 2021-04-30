import logging
import os
import sys
import yaml

logger = logging.getLogger(__name__)


class ConfigParser():
    def __init__(self, config_path):

        config_path = os.path.abspath(config_path)

        logger.debug("config file: %s", config_path)

        with open(config_path) as f:
            self.config_data = yaml.load(f, Loader=yaml.FullLoader)

        self.inp_path = self.config_data.get("inp_file")
        self.inp_path = os.path.join(os.path.dirname(config_path), self.inp_path)
        self.inp_path = os.path.abspath(self.inp_path)

        logger.debug("inp file: %s", self.inp_path)

        cpa_path = self.config_data.get("cpa_file")
        cpa_path = os.path.join(os.path.dirname(config_path), cpa_path)
        cpa_path = os.path.abspath(cpa_path)

        logger.debug("cpa file: %s", cpa_path)

        with open(cpa_path) as f:
            self.cpa_data = yaml.load(f, Loader=yaml.FullLoader)

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    parser = ConfigParser(sys.argv[1])