import signal
import sys
from abc import ABCMeta, abstractmethod

import yaml


class NodeControl:
    """
    This class is started for a ndoe. It can start all the subprocess and terminate them again.
    """
    __metaclass__ = ABCMeta

    def __init__(self, intermediate_yaml):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.intermediate_yaml = intermediate_yaml

        with self.intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

    def sigint_handler(self, sig, frame):
        """
        Interrupt handler for :class:`~signal.SIGINT` and :class:`~signal.SIGINT`.
        """
        self.terminate()
        sys.exit(0)

    @abstractmethod
    def terminate(self):
        """
        This function should stop all the child processes. Its also called on the interrupt.
        """

    @abstractmethod
    def main(self):
        """
        This function should start all the child processes.
        """
