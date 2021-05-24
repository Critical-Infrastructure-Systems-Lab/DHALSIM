import argparse
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

import yaml
from minicps.mcps import MiniCPS
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from py2_logger import get_logger
from topo.simple_topo import SimpleTopo
from topo.complex_topo import ComplexTopo


class GeneralCPS(MiniCPS):
    """
    This class can run a experiment from a intermediate yaml file

    :param intermediate_yaml: The path to the intermediate yaml file
    :type intermediate_yaml: Path
    """
    def __init__(self, intermediate_yaml):
        # Create logs directory in working directory
        try:
            os.mkdir('logs')
        except OSError:
            pass

        self.intermediate_yaml = intermediate_yaml

        with self.intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

        self.logger = get_logger(self.data['log_level'])

        if self.data['log_level'] == 'debug':
            logging.getLogger('mininet').setLevel(logging.DEBUG)
        else:
            logging.getLogger('mininet').setLevel(logging.WARNING)

        # Create directory output path
        try:
            os.makedirs(str(Path(self.data["output_path"])))
        except OSError:
            pass

        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        if self.data["network_topology_type"].lower() == "complex":
            topo = ComplexTopo(self.intermediate_yaml)
        else:
            topo = SimpleTopo(self.intermediate_yaml)

        self.net = Mininet(topo=topo, autoSetMacs=True, link=TCLink)

        self.net.start()

        topo.setup_network(self.net)

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
        """
        Interrupt handler for :class:`~signal.SIGINT` and :class:`~signal.SIGINT`.
        """
        self.finish()
        sys.exit(0)

    def automatic_start(self):
        """
        This starts all the processes for plcs, etc.
        """
        self.plc_processes = []

        automatic_plc_path = Path(__file__).parent.absolute() / "automatic_plc.py"
        for i, plc in enumerate(self.data["plcs"]):
            node = self.net.get(plc["name"])
            cmd = ["python2", str(automatic_plc_path), str(self.intermediate_yaml), str(i)]
            self.plc_processes.append(node.popen(cmd, stderr=sys.stderr, stdout=sys.stdout))

        automatic_scada_path = Path(__file__).parent.absolute() / "automatic_scada.py"
        scada_cmd = ["python2", str(automatic_scada_path), str(self.intermediate_yaml)]
        self.scada_process = self.net.get('scada').popen(scada_cmd, stderr=sys.stderr, stdout=sys.stdout)

        self.logger.info("Launched the PLCs and SCADA processes")

        automatic_plant_path = Path(__file__).parent.absolute() / "automatic_plant.py"

        cmd = ["python2", str(automatic_plant_path), str(self.intermediate_yaml)]
        self.plant_process = self.net.get('plant').popen(cmd, stderr=sys.stderr, stdout=sys.stdout)

        self.logger.info("Simulating...")
        # We wait until the simulation ends
        while self.plant_process.poll() is None:
            pass
        self.finish()

    @staticmethod
    def end_process(process):
        """
        End a process.

        :param process: the process to end
        """
        process.send_signal(signal.SIGINT)
        process.wait()
        if process.poll() is None:
            process.terminate()
        if process.poll() is None:
            process.kill()

    def finish(self):
        """
        Terminate the plcs, physical process, mininet, and remaining processes that
        automatic run spawned.
        """
        self.logger.info("Simulation finished")
        try:
            self.end_process(self.scada_process)
        except Exception, msg:
            self.logger.error("Exception shutting down SCADA: " + str(msg))

        for plc_process in self.plc_processes:
            try:
                self.end_process(plc_process)
            except:
                continue

        if self.plant_process.poll() is None:
            self.logger.info("Physical simulation process terminated")
            self.end_process(self.plant_process)

        cmd = 'sudo pkill -f "python2 -m cpppo.server.enip"'
        subprocess.call(cmd, shell=True, stderr=sys.stderr, stdout=sys.stdout)

        self.net.stop()
        sys.exit(0)


def is_valid_file(parser_instance, arg):
    """Verifies whether the intermediate yaml path is valid"""
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run experiment from intermediate yaml file')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))

    args = parser.parse_args()

    general_cps = GeneralCPS(intermediate_yaml=Path(args.intermediate_yaml))
