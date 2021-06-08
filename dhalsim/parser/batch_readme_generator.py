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
