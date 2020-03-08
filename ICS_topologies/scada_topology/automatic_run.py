from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from topo import ScadaTopo
import sys
import time
import subprocess

automatic = 0

class Minitown(MiniCPS):
    """ Script to run the Minitown SCADA topology """

    def __init__(self, name, net):
        net.start()

        r0 = net.get('r0')
        # Pre experiment configuration, prepare routing path
        r0.cmd('sysctl net.ipv4.ip_forward=1')

        if automatic:
            self.automatic_start()
        else:
            CLI(net)
        net.stop()

    def automatic_start(self):

        subprocess.call(['rm', '-rf', 'logs/protocols_tests_enip_server'], shell=False)

        plc1 = net.get('plc1')
        plc2 = net.get('plc2')

        plc1_process = plc1.popen(sys.executable, "automatic_plc.py", "-n", "plc1")
        time.sleep(0.1)
        plc2_process = plc2.popen(sys.executable, "automatic_plc.py", "-n", "plc2")

        plant = net.get('plant')
        simulation = plant.popen("../../wntr-experiments/env/bin/python", 'minitown_process.py')

        simulation.wait()
        plc1_process.kill()
        plc2_process.kill()


if __name__ == "__main__":
    topo = ScadaTopo()
    net = Mininet(topo=topo)
    minitown_cps = Minitown(name='minitown', net=net)