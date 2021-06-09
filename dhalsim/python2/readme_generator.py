import datetime
import os
from pathlib import Path
from shutil import copy

import pkg_resources
import yaml


class ReadMeGenerator:
    """
    Class which deals with generating a readme.
    """

    def __init__(self, intermediate_yaml_path, links):
        self.links = links

        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

    def get_value(self, parameter):
        """
        Gets the value of a required parameter.
        :param parameter: to find the value of
        :return: human readable string
        """
        return "\n\n" + parameter + ": " + str(self.intermediate_yaml[parameter])

    def get_optional(self, parameter):
        """
        Gets the value of an optional parameter.
        :param parameter: to find the value of
        :type parameter: str
        :return: human readable string
        :rtype: str
        """
        if parameter in self.intermediate_yaml:
            return self.get_value(parameter)
        else:
            return "\n\n" + parameter + ": None"

    def write_readme(self, start_time, end_time):
        """
        Writes a readme about the current experiment.
        :param start_time: starting time of experiment
        :type start_time: datetime
        :param end_time: ending time of experiment
        :type end_time: datetime
        """
        if 'batch_simulations' in self.intermediate_yaml:
            configuration_folder = Path(self.intermediate_yaml['config_path']).parent \
                                   / Path(self.intermediate_yaml['output_path']).parent \
                                   / 'configuration'
        else:
            configuration_folder = Path(self.intermediate_yaml['config_path']).parent \
                                   / self.intermediate_yaml['output_path'] / 'configuration'

        readme_path = str(configuration_folder / 'readme_experiment.md')
        # open(configuration_folder, 'w+')

        # Create directories in output folder
        if not os.path.exists(str(configuration_folder)):
            os.makedirs(str(configuration_folder))

        with open(readme_path, 'w') as readme:
            readme.write("# Auto-generated README of {file}"
                         .format(file=os.path.basename(str(self.intermediate_yaml['inp_file']))[:-4]))

            # Input files
            readme.write("\n\n## Input files")
            input_string = "\n\nInput files have been copied to {output}. In case" \
                           " any extra files were used, these files will be copied to the" \
                           " output folder as well."

            # We want to write this readme to the root directory of the original output folder.
            if 'batch_simulations' in self.intermediate_yaml:
                readme.write(input_string
                             .format(output=str(Path(self.intermediate_yaml['output_path'])
                                                .parent)))
            else:
                readme.write(input_string.format(output=self.intermediate_yaml['output_path']))

            # Configuration parameters
            readme.write("\n\n## Configuration parameters")
            readme.write(self.get_value('iterations'))
            readme.write(self.get_value('network_topology_type'))
            readme.write(self.get_value('mininet_cli'))
            readme.write(self.get_value('log_level'))
            readme.write(self.get_value('simulator'))
            readme.write(self.get_optional('attacks_path'))
            readme.write(self.get_optional('batch_simulations'))

            # Mininet links
            readme.write("\n\n## Mininet links")
            for link in self.links:
                readme.write("\n\n" + str(link))

            # About this experiment
            readme.write("\n\n## About this experiment")
            readme.write("\n\nRan with DHALSIM v{version}."
                         .format(version=self.intermediate_yaml['dhalsim_version']))
            readme.write("\n\nStarted at {start} and finished at {end}."
                         .format(start=str(start_time.strftime("%Y-%m-%d %H:%M:%S")),
                                 end=str(end_time.strftime("%Y-%m-%d %H:%M:%S"))))
            readme.write("\n\nThe duration of this simulation was {time}."
                         .format(time=str(end_time - start_time)))
