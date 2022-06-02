from pathlib import Path
import sys
import signal

from netfilterqueue import NetfilterQueue
import yaml
from dhalsim.py3_logger import get_logger

from abc import ABCMeta, abstractmethod


class PacketQueue(metaclass=ABCMeta):
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
        self.logger.debug('Parent NF Class launched')
        self.nfqueue = NetfilterQueue()
        self.nfqueue.bind(self.queue_number, self.capture)
        try:
            self.logger.debug('Queue bound to number' + str(self.queue_number) + ' , running queue now')
            self.nfqueue.run()
        except Exception as exc:
            if self.nfqueue:
                self.nfqueue.unbind()
            sys.exit(0)

    @abstractmethod
    def capture(self, pkt):
        """
        method that handles what to do with the packets sent to the NFQueue
        :param pkt: The captured packet.
        """

    def interrupt(self):
        if self.nfqueue:
            self.nfqueue.unbind()

    def sigint_handler(self, sig, frame):
        """Interrupt handler for attacker being stoped"""
        self.logger.debug("{name} NfQueue shutdown".format(name=self.intermediate_attack["name"]))
        self.interrupt()
        sys.exit(0)


