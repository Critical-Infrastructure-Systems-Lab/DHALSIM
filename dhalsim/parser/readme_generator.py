import os
from pathlib import Path

import yaml
from mdutils import MdUtils


class ReadMeGenerator:
    """
    Class which deals with generating a readme.
    """

    def __init__(self, intermediate_yaml_path):
        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        # Create directories in output folder
        self.configuration_path = Path(self.intermediate_yaml['output_path']) / 'configuration'
        self.input_files_path = self.configuration_path / 'input_files'

        os.makedirs(str(self.input_files_path), exist_ok=True)

    def write_md(self):
