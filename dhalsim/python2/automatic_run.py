import argparse
import logging
import os
import signal
import subprocess
import sys
from dhalsim.py3_logger import get_logger
from pathlib import Path

import yaml
from datetime import datetime
from minicps.mcps import MiniCPS
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink

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

        self.net = Mininet(topo=topo, autoSetMacs=False, link=TCLink)

        self.net.start()

        topo.setup_network(self.net)

        with self.intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

        if self.data["mininet_cli"]:
            CLI(self.net)

        self.plc_processes = None
        self.scada_process = None
        self.plant_process = None
        self.attacker_processes = None
        self.network_event_processes = None
        self.router_processes = None

        self.automatic_start()

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

        self.router_processes = []
        if 'plcs' in self.data:
            automatic_router_path = Path(__file__).parent.absolute() / "automatic_router.py"

            for plc in self.data["plcs"]:
                node = self.net.get(plc['gateway_name'])
                cmd = ["python3", str(automatic_router_path), str(self.intermediate_yaml), str(plc['gateway_name'])]
                self.router_processes.append(node.popen(cmd, stderr=sys.stderr, stdout=sys.stdout))

        self.logger.info('Launched router processes')

        self.plc_processes = []
        if "plcs" in self.data:
            automatic_plc_path = Path(__file__).parent.absolute() / "automatic_plc.py"
            for i, plc in enumerate(self.data["plcs"]):
                node = self.net.get(plc["name"])
                cmd = ["python3", str(automatic_plc_path), str(self.intermediate_yaml), str(i)]
                self.plc_processes.append(node.popen(cmd, stderr=sys.stderr, stdout=sys.stdout))

        self.logger.info("Launched the PLCs processes.")

        automatic_scada_path = Path(__file__).parent.absolute() / "automatic_scada.py"
        scada_cmd = ["python3", str(automatic_scada_path), str(self.intermediate_yaml)]
        self.scada_process = self.net.get('scada').popen(scada_cmd, stderr=sys.stderr, stdout=sys.stdout)

        automatic_router_path = Path(__file__).parent.absolute() / "automatic_router.py"
        node = self.net.get(self.data['scada']['gateway_name'])
        cmd = ["python3", str(automatic_router_path), str(self.intermediate_yaml), str(self.data['scada']['gateway_name'])]
        self.router_processes.append(node.popen(cmd, stderr=sys.stderr, stdout=sys.stdout))

        self.logger.info("Launched the SCADA process.")

        self.attacker_processes = []
        if "network_attacks" in self.data:
            automatic_attacker_path = Path(__file__).parent.absolute() / "automatic_attacker.py"
            for i, attacker in enumerate(self.data["network_attacks"]):
                node = self.net.get(attacker["name"][0:9])
                cmd = ["python3", str(automatic_attacker_path), str(self.intermediate_yaml), str(i)]
                self.attacker_processes.append(node.popen(cmd, stderr=sys.stderr, stdout=sys.stdout))

        self.logger.debug("Launched the attackers processes.")

        self.network_event_processes = []
        if 'network_events' in self.data:
            automatic_event = Path(__file__).parent.absolute() / "automatic_event.py"
            node_name = None
            for i, event in enumerate(self.data['network_events']):
                target_node = event['target']
                if target_node == 'scada':
                    self.logger.debug('Network event in SCADA link')
                    node_name = self.data['scada']['switch_name']
                else:
                    for plc in self.data['plcs']:
                        if target_node == plc['name']:
                            self.logger.debug('Network event in link to ' + str(plc['name']))
                            node_name = plc['switch_name']

                node = self.net.get(node_name)
                # Network events have effect on network interfaces;
                # in addition to the node, we also need the network interface
                event_interface_name = self.get_network_event_interface_name(target_node, node_name)

                cmd = ["python3", str(automatic_event), str(self.intermediate_yaml), str(i), event_interface_name]
                self.network_event_processes.append(node.popen(cmd, stderr=sys.stderr, stdout=sys.stdout))

        self.logger.info("Launched the event processes.")
        automatic_plant_path = Path(__file__).parent.absolute() / "automatic_plant.py"

        cmd = ["python3", str(automatic_plant_path), str(self.intermediate_yaml)]
        self.plant_process = subprocess.Popen(cmd, stderr=sys.stderr, stdout=sys.stdout)

        self.logger.debug("Launched the plant processes.")
        self.poll_processes()
        self.finish()

    def get_network_event_interface_name(self, target, source):
        for link in self.net.links:
            # example: PLC1-eth0<->s2-eth2
            link_source = str(link).split('-')[0]

            if link_source == target:
                switch_name = str(link).split('-')[2].split('>')[-1]
                interface_name = str(link).split('-')[-1]
                # todo: We are only supporting cases where a PLC has only 1 interface. ALL our cases so far, but still
                return str(switch_name + '-' + interface_name)

    def poll_processes(self):
        """Polls for all processes and finishes if one closes"""
        processes = []
        processes.extend(self.plc_processes)
        processes.extend(self.attacker_processes)
        processes.extend(self.router_processes)
        processes.append(self.scada_process)
        processes.append(self.plant_process)

        # We wait until the simulation ends
        while True:
            for process in processes:
                if process.poll() is None:
                    pass
                else:
                    self.logger.debug("process has finished, stopping simulation...")
                    return

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
        self.logger.info("Simulation finished.")

        self.write_mininet_links()

        if self.scada_process.poll() is None:
            try:
                self.end_process(self.scada_process)
            except Exception as msg:
                self.logger.error("Exception shutting down SCADA: " + str(msg))

        for plc_process in self.plc_processes:
            if plc_process.poll() is None:
                try:
                    self.end_process(plc_process)
                except Exception as msg:
                    self.logger.error("Exception shutting down plc: " + str(msg))

        for attacker in self.attacker_processes:
            if attacker.poll() is None:
                try:
                    self.end_process(attacker)
                except Exception as msg:
                    self.logger.error("Exception shutting down attacker: " + str(msg))

        for event in self.network_event_processes:
            if event.poll() is None:
                try:
                    self.end_process(event)
                except Exception as msg:
                    self.logger.error("Exception shutting down event: " + str(msg))

        for router in self.router_processes:
            if router.poll() is None:
                try:
                    self.end_process(router)
                except Exception as msg:
                    self.logger.error("Exception shutting down event: " + str(msg))

        if self.plant_process.poll() is None:
            try:
                self.end_process(self.plant_process)
            except Exception as msg:
                self.logger.error("Exception shutting down plant_process: " + str(msg))

        cmd = 'sudo pkill -f "python3 -m cpppo.server.enip"'
        subprocess.call(cmd, shell=True, stderr=sys.stderr, stdout=sys.stdout)

        self.net.stop()
        sys.exit(0)

    def write_mininet_links(self):
        """Writes mininet links file."""
        if 'batch_simulations' in self.data:
            links_path = (Path(self.data['config_path']).parent / self.data['output_path']).parent / 'configuration'
        else:
            links_path = Path(self.data['config_path']).parent / self.data['output_path'] / 'configuration'

        if not os.path.exists(str(links_path)):
            os.makedirs(str(links_path))

        with open(str(links_path / 'mininet_links.md'), 'w') as links_file:
            links_file.write("# Mininet Links")
            for link in self.net.links:
                links_file.write("\n\n" + str(link))


def is_valid_file(parser_instance, arg):
    """Verifies whether the intermediate yaml path is valid"""
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist.")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run experiment from intermediate yaml file')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))

    args = parser.parse_args()

    general_cps = GeneralCPS(intermediate_yaml=Path(args.intermediate_yaml))
