import datetime
import os
from pathlib import Path
from shutil import copy

import pkg_resources
import wntr
import yaml


class BatchReadMeGenerator:
    """
    Class which deals with generating a readme for each batch.
    """

    def __init__(self, intermediate_yaml_path):
        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        # # Create directories in output folder
        # self.configuration_path = Path(self.intermediate_yaml['output_path']) / 'configuration'
        # self.input_files_path = self.configuration_path / 'input_files'
        #
        # os.makedirs(str(self.input_files_path), exist_ok=True)

    def write_batch(self, start_time, end_time, wn, master_time):
        readme.write("\n\nRan for {x} out of {y} iterations with hydraulic timestep {step}."
                     .format(x=str(master_time),
                             y=str(self.intermediate_yaml['iterations']),
                             step=str(wn.options.time.hydraulic_timestep)))

        return None
        # batch x / y
        # initial values van deze batch


class InputFilesCopier:
    def __init__(self, config_file):
        self.config_file = config_file

        with self.config_file.open(mode='r') as conf:
            self.config = yaml.load(conf, Loader=yaml.FullLoader)

        self.configuration_folder = self.config_file.parent / self.config['output_path'] / 'configuration'

    def copy_input_files(self):
        """Copies all input files, mandatory and optional ones included."""

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
            copy(self.config_file.parent / self.config['demand_patterns'],
                 self.configuration_folder / 'demand_patterns.csv')

        if 'network_loss_data' in self.config:
            copy(self.config_file.parent / self.config['network_loss_data'],
                 self.configuration_folder / 'network_loss_data.csv')

        if 'network_delay_data' in self.config:
            copy(self.config_file.parent / self.config['network_delay_data'],
                 self.configuration_folder / 'network_delay_data.csv')
