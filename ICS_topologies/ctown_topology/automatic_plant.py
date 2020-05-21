import subprocess
import argparse

class SimulationControl():
    def main(self):
        args = self.get_arguments()
        self.process_arguments(args)
        simulation = self.start_simulation()
        simulation.wait()

    def start_simulation(self):
        simulation = subprocess.Popen(["../../../wntr-experiments/bin/python", 'physical_process.py',
                                       self.simulator, self.topology, self.output])
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

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script that launches the WNTR simulation')
        parser.add_argument("--simulator", "-s",help="Type of simulation used, can be Pressure Driven (pdd) or Demand Driven (dd)")
        parser.add_argument("--topology", "-t",help="Water network topology to simulate")
        parser.add_argument("--output", "-o", help="Output file name")
        return parser.parse_args()

if __name__=="__main__":
    simulation_control = SimulationControl()
    simulation_control.main()