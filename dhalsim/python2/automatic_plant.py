import os
import subprocess
import argparse
import signal
import sys
from os.path import expanduser
import shlex
from pathlib import Path


class SimulationControl:
    """
    Class representing the simulation process of a plant. All the automatic_plant.py have the same pattern
    """

    def __init__(self, intermediate_yaml):
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        self.intermediate_yaml = intermediate_yaml

        self.simulation = self.start_simulation()

        while self.simulation.poll() is None:
            pass

    def interrupt(self, sig, frame):
        """
        This method is provided by the signal python library. We call the finish method that interrupts, terminates, or kills the simulation and exit
        """
        self.finish()
        sys.exit(1)

    def finish(self):
        """
        All the subprocesses launched in this Digital Twin follow the same pattern to ensure that they finish before continuing with the finishing of the parent process
        """
        self.simulation.send_signal(signal.SIGINT)
        self.simulation.wait()
        if self.simulation.poll() is None:
            self.simulation.terminate()
        if self.simulation.poll() is None:
            self.simulation.kill()

    def start_simulation(self):
        """
        This method uses a Python3.6 virtual environment where WNTR simulator is installed to run the simulation of a model.
        By default WNTR is run using the PDD model and the output file is a .csv file called "physical_process.csv"
        :return: An object representing the simulation process
        """
        physical_process_path = Path(__file__).parent.absolute().parent / "physical_process.py"

        cmd = ["python3", str(physical_process_path), str(self.intermediate_yaml)]

        simulation = subprocess.Popen(cmd)
        return simulation


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a automatic plant')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))

    args = parser.parse_args()

    simulation_control = SimulationControl(Path(args.intermediate_yaml))
