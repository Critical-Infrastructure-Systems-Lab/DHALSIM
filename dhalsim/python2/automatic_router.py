import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

from automatic_node import NodeControl
from dhalsim.py3_logger import get_logger

empty_loc = '/dev/null'


class RouterControl(NodeControl):
    """
    This class is started for a router. It starts a tcpdump process.
    """

    def __init__(self, intermediate_yaml, router_name):
        super(RouterControl, self).__init__(intermediate_yaml)

        self.output_path = Path(self.data["output_path"])
        self.logger = get_logger(self.data['log_level'])
        self.process_tcp_dump = None
        self.router_name = router_name
        self.interface_name = str(router_name) + '-eth0'

    def terminate(self):
        """
        This function stops the tcp dump and the plc process.
        """
        self.logger.debug("Stopping Router tcpdump process.")

        self.process_tcp_dump.send_signal(signal.SIGINT)
        self.process_tcp_dump.wait()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.terminate()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.kill()

    def main(self):
        """
        This function starts the tcp dump and plc process and then waits for the plc
        process to finish.
        """

        self.process_tcp_dump = self.start_tcpdump_capture()

        while True:
            pass

    def start_tcpdump_capture(self):
        """
        Start a tcp dump.
        """
        pcap = self.output_path / (str(self.interface_name) + '.pcap')

        # Output is not printed to console
        no_output = open(empty_loc, 'w')
        cmd = ['tcpdump', '-i', self.interface_name, '-w', str(pcap)]
        tcp_dump = subprocess.Popen(cmd, shell=False, stderr=no_output, stdout=no_output)

        return tcp_dump


def is_valid_file(parser_instance, arg):
    """
    Verifies whether the intermediate yaml path is valid.
    """
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist.")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start everything for a plc')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument(dest="name", help="Index of PLC in intermediate yaml")

    args = parser.parse_args()
    router_control = RouterControl(Path(args.intermediate_yaml), args.name)
    router_control.main()
