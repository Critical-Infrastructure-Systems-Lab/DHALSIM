import argparse
import os
from pathlib import Path

from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from topo.simple_topo import SimpleTopo
from initialize_experiment import ExperimentInitializer
import sys
import time
import shlex
import subprocess
import signal
from mininet.link import TCLink
import yaml
import glob


class GeneralCPS(MiniCPS):

    # def do_forward(self, node):
    #     # Pre experiment configuration, prepare routing path
    #     node.cmd('sysctl net.ipv4.ip_forward=1')
    #     node.waitOutput()
    #
    # def add_degault_gateway(self, node, gw_ip):
    #     node.cmd('route add default gw ' + gw_ip)
    #     node.waitOutput()
    #
    # def setup_network(self):
    #     r0 = self.net.get('r0')
    #     self.do_forward(r0)
    #     self.add_degault_gateway(self.net.get('plc1'), '192.168.1.254')
    #     self.add_degault_gateway(self.net.get('plc2'), '192.168.1.254')
    #     self.add_degault_gateway(self.net.get('attacker_1'), '192.168.1.254')
    #     self.add_degault_gateway(self.net.get('scada'), '192.168.2.254')
    #     self.add_degault_gateway(self.net.get('attacker_2'), '192.168.2.254')
    #     r0.cmd('ifconfig r0-eth2 192.168.2.254')
    #     r0.waitOutput()

    def __init__(self, intermediate_yaml):

        self.intermediate_yaml = intermediate_yaml

        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        topo = SimpleTopo(self.intermediate_yaml)
        self.net = Mininet(topo=topo, autoSetMacs=True, link=TCLink)

        self.net.start()

        topo.setup_network(self.net)

        # CLI(self.net)

        with self.intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

        if self.data["mininet_cli"]:
            CLI(self.net)

        self.plc_processes = None
        self.scada_process = None
        self.plant_process = None

        self.automatic_start()

        self.net.stop()

    def interrupt(self, sig, frame):
        self.finish()
        sys.exit(0)

    def automatic_start(self):

        self.plc_processes = []

        for i, plc in enumerate(self.data["plcs"]):
            node = self.net.get(plc["name"])

            automatic_plc_path = Path(__file__).parent.absolute() / "automatic_plc.py"

            cmd = ["python2", str(automatic_plc_path), str(self.intermediate_yaml), str(i)]
            self.plc_processes.append(node.popen(cmd, stderr=sys.stderr, stdout=sys.stdout))

        # self.scada_process = self.net.get('scada').popen("python2", "automatic_plc.py", "-n",
        #                                             "scada",
        #                                             stderr=sys.stderr, stdout=sys.stdout)
        print("[*] Launched the PLCs and SCADA processes")

        automatic_plant_path = Path(__file__).parent.absolute() / "automatic_plant.py"

        cmd = ["python2", str(automatic_plant_path), str(self.intermediate_yaml)]
        self.plant_process = self.net.get('plant').popen(cmd, stderr=sys.stderr, stdout=sys.stdout)

        print("[] Simulating...")
        # We wait until the simulation ends
        while self.plant_process.poll() is None:
            pass
        self.finish()

    @staticmethod
    def end_process(process):
        process.send_signal(signal.SIGINT)
        process.wait()
        if process.poll() is None:
            process.terminate()
        if process.poll() is None:
            process.kill()

    def finish(self):
        print("[*] Simulation finished")

        # self.end_process(self.scada_process)

        for plc_process in self.plc_processes:
            self.end_process(plc_process)

        if self.plant_process.poll() is None:
            self.end_process(self.plant_process)
            print("Physical Simulation process terminated")

        cmd = 'sudo pkill -f "python2 -m cpppo.server.enip"'
        subprocess.call(cmd, shell=True, stderr=sys.stderr, stdout=sys.stdout)

        self.net.stop()
        sys.exit(0)


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run experiment from intermediate yaml file')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))

    args = parser.parse_args()

    general_cps = GeneralCPS(intermediate_yaml=Path(args.intermediate_yaml))
