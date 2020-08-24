import subprocess
import argparse
import signal
import sys

class SimulationControl():
    """
    Class representing the simulation process of a plant. All the automatic_plant.py have the same pattern
    """

    def main(self):
        """
        main method of the automatic_plant
        All the automatic_plant.py scrpits follow the same pattern. They process the arguments, register the method interrupt() to handle SIGINT and SIGTERM signals.
        Later, they start the simulation, by calling the script physical_process.py
        """
        args = self.get_arguments()
        self.process_arguments(args)
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)
        self.simulation = self.start_simulation()

        while self.simulation.poll() is None:
            pass

    def interrupt(self, sig, frame):
        """
        This method is provided by the signal python library. We call the finish method that interrupts, terminates, or kills the simulation and exit
        """
        self.finish()
        sys.exit(0)

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
        simulation = subprocess.Popen(["../../../wntr-experiments/bin/python", 'physical_process.py',
                                       self.simulator, self.topology, self.output, self.week])
        return simulation

    def process_arguments(self,arg_parser):
        if arg_parser.simulator:
            self.simulator = arg_parser.simulator
        else:
            self.simulator = 'pdd'

        if arg_parser.topology:
            self.topology = arg_parser.topology
        else:
            self.topology = "ctown"

        if arg_parser.output:
            self.output = arg_parser.output
        else:
            self.output = 'default.csv'

        if arg_parser.week:
            self.week = arg_parser.week
        else:
            self.week = 0

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script that launches the WNTR simulation')
        parser.add_argument("--simulator", "-s",help="Type of simulation used, can be Pressure Driven (pdd) or Demand Driven (dd)")
        parser.add_argument("--topology", "-t",help="Water network topology to simulate")
        parser.add_argument("--output", "-o", help="Output file name")
        parser.add_argument("--week", "-w", help="Week index of the simulation")
        return parser.parse_args()

if __name__=="__main__":
    simulation_control = SimulationControl()
    simulation_control.main()