import os
from pathlib import Path

import yaml


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

    def get_value(self, parameter: str):
        """
        Gets the value of a required parameter.
        :param parameter: to find the value of
        :return: human readable string
        """
        return "\n\n" + parameter + ": " + str(self.intermediate_yaml[parameter])

    def get_optional(self, parameter: str):
        """
        Gets the value of an optional parameter.
        :param parameter: to find the value of
        :return: human readable string
        """
        if parameter in self.intermediate_yaml:
            return self.get_value(parameter)
        else:
            return "\n\n" + parameter + ": None"
