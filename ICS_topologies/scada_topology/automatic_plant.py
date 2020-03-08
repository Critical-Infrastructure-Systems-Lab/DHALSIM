import subprocess

class SimulationControl():
    def main(self):
        simulation = self.start_simulation()
        simulation.wait()

    def start_simulation(self):
        simulation = subprocess.Popen(["../../wntr-experiments/env/bin/python", 'minitown_process.py'])
        return simulation

if __name__=="__main__":
    simulation_control = SimulationControl()
    simulation_control.main()