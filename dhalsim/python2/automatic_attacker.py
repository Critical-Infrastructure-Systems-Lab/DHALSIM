import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

from automatic_node import NodeControl


class Error(Exception):
    """Base class for exceptions in this module."""


class NoSuchAttack(Error):
    """Raised when the configuration file is empty"""


class AttackerControl(NodeControl):
    """This class is started for a attacker. It starts a tcpdump and a network attack."""

    def __init__(self, intermediate_yaml, attacker_index):
        super(AttackerControl, self).__init__(intermediate_yaml)

        self.attacker_index = attacker_index
        self.output_path = Path(self.data["output_path"])
        self.tcp_dump_process = None
        self.attacker_process = None
        self.this_attacker_data = self.data["network_attacks"][self.attacker_index]

    def terminate(self):
        """This function stops the tcp dump and the attack network attack."""
        print("Stopping tcpdump process on attacker...")
        self.tcp_dump_process.send_signal(signal.SIGINT)
        self.tcp_dump_process.wait()
        if self.tcp_dump_process.poll() is None:
            self.tcp_dump_process.terminate()
        if self.tcp_dump_process.poll() is None:
            self.tcp_dump_process.kill()

        print("Stopping attacker...")
        self.attacker_process.send_signal(signal.SIGINT)
        self.attacker_process.wait()
        if self.attacker_process.poll() is None:
            self.attacker_process.terminate()
        if self.attacker_process.poll() is None:
            self.attacker_process.kill()

    def main(self):
        """This function starts the tcp dump and plc process and then waits for the network attack to finish."""
        self.tcp_dump_process = self.start_tcpdump_capture()

        self.attacker_process = self.start_attack()

        while self.attacker_process.poll() is None:
            pass

        self.terminate()

    def start_tcpdump_capture(self):
        """Start a tcp dump."""
        pcap = self.output_path / (self.this_attacker_data["interface"] + '.pcap')
        tcp_dump = subprocess.Popen(['tcpdump', '-i', self.this_attacker_data["interface"], '-w',
                                     str(pcap)], shell=False)
        return tcp_dump

    def start_attack(self):
        """Start a attack process."""
        generic_plc_path = None
        if self.this_attacker_data['type'] == 'mitm':
            generic_plc_path = Path(__file__).parent.parent.absolute() / "network_attacks" / "mitm_attack.py"
        elif self.this_attacker_data['type'] == 'naive':
            generic_plc_path = Path(__file__).parent.parent.absolute() / "network_attacks" / "naive_attack.py"
        else:
            raise NoSuchAttack("Attack {attack} does not exists.".format(attack=self.this_attacker_data['type']))

        cmd = ["python3", str(generic_plc_path), str(self.intermediate_yaml), str(self.attacker_index)]

        plc_process = subprocess.Popen(cmd, shell=False, stderr=sys.stderr, stdout=sys.stdout)
        return plc_process


def is_valid_file(parser_instance, arg):
    """Verifies whether the intermediate yaml path is valid."""
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start everything for a attacker')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument(dest="index", help="Index of PLC in intermediate yaml", type=int,
                        metavar="N")

    args = parser.parse_args()
    attacker_control = AttackerControl(Path(args.intermediate_yaml), args.index)
    attacker_control.main()
