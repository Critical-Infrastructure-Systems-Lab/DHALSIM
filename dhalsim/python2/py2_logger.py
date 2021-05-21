import logging
import sys
from pathlib import Path

import yaml


def generate_logger(yaml_path: Path):
    with yaml_path.open() as yaml_file:
        yaml_data = yaml.load(yaml_file, Loader=yaml.FullLoader)

    logging_level = yaml_data['log_level']
    logging_format = '%(asctime)s - %(levelname)s @ %(filename)s: %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging_level, format=logging_format, datefmt='%H:%M:%S')
    return logging.getLogger('py2_logger')
