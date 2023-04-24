import argparse
import os
import signal
import subprocess
from pathlib import Path

from automatic_node import NodeControl
from py2_logger import get_logger


class Error(Exception):
    """Base class for exceptions in this module."""


class UnsupportedSimulator(Error):
    """Raised when an unsupported simulator is launched"""


class PlantControl(NodeControl):
    """
    This class is started for a plant. It starts a simulation process.
    """

    def __init__(self, intermediate_yaml):
        super(PlantControl, self).__init__(intermediate_yaml)

        self.logger = get_logger(self.data['log_level'])

        self.simulation_process = None

    def terminate(self):
        """
        This function stops the physical process (child of this process).
        """
        self.logger.debug("Stopping plant.")
        if self.simulation_process.poll() is None:
            self.simulation_process.send_signal(signal.SIGINT)
        self.simulation_process.wait()
        if self.simulation_process.poll() is None:
            self.simulation_process.terminate()
        if self.simulation_process.poll() is None:
            self.simulation_process.kill()

    def main(self):
        """
        This function starts the physical process and then waits for the physical
        process to finish.
        """

        if self.data['simulator'] == 'wntr' or self.data['simulator'] == 'epynet':
            physical_process_path = Path(__file__).parent.absolute().parent / "physical_process.py"
        else:
            raise UnsupportedSimulator('Supported simulators are wntr, epynet')

        cmd = ["python3", str(physical_process_path), str(self.intermediate_yaml)]

        self.simulation_process = subprocess.Popen(cmd)

        while self.simulation_process.poll() is None:
            pass

        self.terminate()


def is_valid_file(parser_instance, arg):
    """
    Verifies whether the intermediate yaml path is valid.
    """
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist.")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a automatic plant')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))

    args = parser.parse_args()
    plant_control = PlantControl(Path(args.intermediate_yaml))
    plant_control.main()
