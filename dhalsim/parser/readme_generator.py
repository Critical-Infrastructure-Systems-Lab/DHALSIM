import datetime
import os
from pathlib import Path

import pkg_resources
import wntr
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

    def write_md(self, start_time: datetime, end_time: datetime,
                 wn: wntr.network.WaterNetworkModel, master_time: int):
        """
        Writes a readme about the current experiment.
        :param start_time: starting time of experiment
        :param end_time: ending time of experiment
        :param wn: WNTR instance
        :param master_time: current iteration
        """
        readme_path = str(self.configuration_path / 'readme_experiment.md')
        open(readme_path, 'w+')

        # with open(str(self.configuration_path / 'config2.yaml'), 'w') as file:
        #     yaml.dump(self.intermediate_yaml, file)

        with open(readme_path, 'a') as readme:
            readme.write("# Automatically generated README of "
                         + os.path.basename(str(self.intermediate_yaml['inp_file']))[:-4])

            # Input files
            readme.write("\n\n## Input files")
            input_string = "\n\nInput files have been copied to {output}. In case" \
                           " ```attacks_path``` or ```batch_simulations``` was used, these files" \
                           " will be copied to the output folder as well."

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
            readme.write("\n\nAll Mininet links can be found in mininet_links.md.")

            # About this experiment
            readme.write("\n\n## About this experiment")
            readme.write("\n\nRan with DHALSIM v{version}."
                         .format(version=pkg_resources.require('dhalsim')[0].version))
            readme.write("\n\nStarted at {start} and finished at {end}"
                         .format(start=str(start_time.strftime("%Y-%m-%d %H:%M:%S")),
                                 end=str(end_time.strftime("%Y-%m-%d %H:%M:%S"))))
            readme.write("\n\nThe duration of this simulation was {time}."
                         .format(time=str(end_time - start_time)))
            readme.write("\n\nRan for {x} out of {y} iterations with hydraulic timestep {step}."
                         .format(x=str(master_time),
                                 y=str(self.intermediate_yaml['iterations']),
                                 step=str(wn.options.time.hydraulic_timestep)))
