import datetime
import os
from pathlib import Path
from shutil import copy

import pkg_resources
from wntr.network import WaterNetworkModel
import yaml


class BatchReadMeGenerator:
    """
    Class which deals with generating a readme for each batch.
    :param intermediate_yaml_path: contains the path to intermediate yaml
    """

    def __init__(self, intermediate_yaml_path: str):
        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        os.makedirs(str(Path(self.intermediate_yaml['config_path']).parent
                        / self.intermediate_yaml['output_path']), exist_ok=True)
        self.readme_path = Path(self.intermediate_yaml['config_path']).parent \
                           / self.intermediate_yaml['output_path'] / 'configuration'\
                           / 'batch_readme.md'

    def write_batch(self, start_time: datetime.datetime, end_time: datetime.datetime,
                    wn: WaterNetworkModel, master_time: int):
        """
        Creates a small readme for each batch.
        :param start_time: is the start time of batch
        :param end_time: is the end time of batch
        :param wn: is WNTR instance
        :param master_time: is current iteration
        """
        with open(str(self.readme_path), 'w') as readme:
            readme.write("# Auto-generated README of {file} for batch {no}"
                         .format(file=os.path.basename(str(self.intermediate_yaml['inp_file']))[:-4],
                                 no=self.intermediate_yaml['batch_index'] + 1))
            readme.write("\n\nThis is batch {x} out of {y}."
                         .format(x=self.intermediate_yaml['batch_index'] + 1,
                                 y=self.intermediate_yaml['batch_simulations']))

            # Batch specific values.
            if 'initial_tank_values' in self.intermediate_yaml:
                readme.write("\n\n## Initial tank data")
                readme.write("\n\n{data}".format(data=str(self.intermediate_yaml['initial_tank_values'])))
            if 'network_loss_values' in self.intermediate_yaml:
                readme.write("\n\n## Network loss values")
                readme.write("\n\n{data}".format(data=str(self.intermediate_yaml['network_loss_values'])))
            if 'network_delay_values' in self.intermediate_yaml:
                readme.write("\n\n## Network delay values")
                readme.write("\n\n{data}".format(data=str(self.intermediate_yaml['network_delay_values'])))

            # Information about this batch.
            readme.write("\n\n## Information about this batch")
            readme.write("\n\nRan for {x} out of {y} iterations with hydraulic timestep {step}."
                         .format(x=str(master_time),
                                 y=str(self.intermediate_yaml['iterations']),
                                 step=str(wn.options.time.hydraulic_timestep)))
            readme.write("\n\nStarted at {start} and finished at {end}."
                         .format(start=str(start_time.strftime("%Y-%m-%d %H:%M:%S")),
                                 end=str(end_time.strftime("%Y-%m-%d %H:%M:%S"))))
            readme.write("\n\nThe duration of this batch was {time}."
                         .format(time=str(end_time - start_time)))
            readme.write("\n\nFor more information with regard to this experiment, consult "
                         "```configuration/readme_experiment.md``` in the root of the output "
                         "folder.")


class InputFilesCopier:
    """
    Copies all input files.
    :param config_file: contains the location of the config file
    """

    def __init__(self, config_file: str):
        self.config_file = config_file

        with self.config_file.open(mode='r') as conf:
            self.config = yaml.load(conf, Loader=yaml.FullLoader)

        self.configuration_folder = self.config_file.parent / self.config['output_path'] / 'configuration'

    def copy_input_files(self):
        """Copies all input files, mandatory and optional ones included."""
        os.makedirs(str(self.configuration_folder), exist_ok=True)

        # Copy mandatory files.
        with open(str(self.configuration_folder / 'config.yaml'), 'w') as config_file:
            yaml.dump(self.config, config_file)

        copy(self.config_file.parent / self.config['inp_file'],
             self.configuration_folder / 'map.inp')

        # Copy optional csv files.
        if 'initial_tank_data' in self.config:
            copy(self.config_file.parent / self.config['initial_tank_data'],
                 self.configuration_folder / 'initial_tank_data.csv')

        if 'demand_patterns' in self.config:
            if 'batch_simulations' in self.config:
                os.makedirs(self.configuration_folder / 'demand_patterns', exist_ok=True)
                for batch in range(self.config['batch_simulations']):
                    copy(self.config_file.parent / self.config['demand_patterns'] / (str(batch) + ".csv"),
                         self.configuration_folder / 'demand_patterns' / (str(batch) + ".csv"))
            else:
                copy(self.config_file.parent / self.config['demand_patterns'],
                     self.configuration_folder / 'demand_patterns.csv')

        if 'network_loss_data' in self.config:
            copy(self.config_file.parent / self.config['network_loss_data'],
                 self.configuration_folder / 'network_loss_data.csv')

        if 'network_delay_data' in self.config:
            copy(self.config_file.parent / self.config['network_delay_data'],
                 self.configuration_folder / 'network_delay_data.csv')


class ReadMeGenerator:
    """
    Class which deals with generating a readme.
    :param intermediate_yaml_path: contains the path to intermediate yaml
    :type intermediate_yaml_path: str
    :param links: contains all Mininet links
    :type links: list of links
    """

    def __init__(self, intermediate_yaml_path: str):
        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

    def get_value(self, parameter: str) -> str:
        """
        Gets the value of a required parameter.
        :param parameter: to find the value of
        :return: human readable string
        """
        return "\n\n" + parameter + ": " + str(self.intermediate_yaml[parameter])

    def get_optional(self, parameter: str) -> str:
        """
        Gets the value of an optional parameter.
        :param parameter: to find the value of
        :return: human readable string
        """
        if parameter in self.intermediate_yaml:
            return self.get_value(parameter)
        else:
            return "\n\n" + parameter + ": None"

    def checkbox(self, parameter: str) -> str:
        """
        Returns a string with a checkbox, checked if parameter is used, otherwise unchecked.
        :param parameter: parameter to evaluate
        :return: complete string with checkbox in it
        """
        if parameter in self.intermediate_yaml:
            if len(self.intermediate_yaml[parameter]) > 0:
                return "\n\n- [x] {para}".format(para=parameter)

        return "\n\n- [ ] {para}".format(para=parameter)

    def write_readme(self, start_time: datetime.datetime, end_time: datetime.datetime,
                     batch: bool, master_time: int, wn: WaterNetworkModel):
        """
        Writes a readme about the current experiment.
        :param start_time: starting time of experiment
        :param end_time: ending time of experiment
        :param batch: bool whether this was batch mode
        :param master_time: current master time
        :param wn: instance of WaterNetworkModel
        """
        if 'batch_simulations' in self.intermediate_yaml:
            configuration_folder = Path(self.intermediate_yaml['config_path']).parent \
                                   / Path(self.intermediate_yaml['output_path']).parent \
                                   / 'configuration'
        else:
            configuration_folder = Path(self.intermediate_yaml['config_path']).parent \
                                   / self.intermediate_yaml['output_path'] / 'configuration'

        readme_path = str(configuration_folder / 'general_readme.md')

        # Create directories in output folder
        os.makedirs(str(configuration_folder), exist_ok=True)

        with open(readme_path, 'w') as readme:
            readme.write("# Auto-generated README of {file}"
                         .format(file=os.path.basename(str(self.intermediate_yaml['inp_file']))[:-4]))

            # Input files
            readme.write("\n\n## Input files")
            input_string = "\n\nInput files have been copied to ```{output}```. In case" \
                           " any extra files were used, these files will be copied to the" \
                           " /output/configuration folder as well."

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
            readme.write(self.get_optional('batch_simulations'))

            # Extra data
            readme.write("\n\n## Extra parameters")
            readme.write(self.checkbox('initial_tank_data'))
            readme.write(self.checkbox('demand_patterns'))
            readme.write(self.checkbox('network_loss_data'))
            readme.write(self.checkbox('network_delay_data'))
            readme.write(self.checkbox('network_attacks'))

            if not batch:
                if 'initial_tank_values' in self.intermediate_yaml:
                    readme.write("\n\n## Initial tank data")
                    readme.write("\n\n{data}".format(data=str(self.intermediate_yaml['initial_tank_values'])))
                if 'network_loss_values' in self.intermediate_yaml:
                    readme.write("\n\n## Network loss values")
                    readme.write("\n\n{data}".format(data=str(self.intermediate_yaml['network_loss_values'])))
                if 'network_delay_values' in self.intermediate_yaml:
                    readme.write("\n\n## Network delay values")
                    readme.write("\n\n{data}".format(data=str(self.intermediate_yaml['network_delay_values'])))

            # About this experiment
            readme.write("\n\n## About this experiment")
            readme.write("\n\nRan with DHALSIM v{version}."
                         .format(version=str(pkg_resources.require('dhalsim')[0].version)))

            if not batch:
                readme.write("\n\nRan for {x} out of {y} iterations with hydraulic timestep {step}."
                             .format(x=str(master_time),
                                     y=str(self.intermediate_yaml['iterations']),
                                     step=str(wn.options.time.hydraulic_timestep)))

            readme.write("\n\nStarted at {start} and finished at {end}."
                         .format(start=str(start_time.strftime("%Y-%m-%d %H:%M:%S")),
                                 end=str(end_time.strftime("%Y-%m-%d %H:%M:%S"))))
            readme.write("\n\nThe duration of this simulation was {time}."
                         .format(time=str(end_time - start_time)))
