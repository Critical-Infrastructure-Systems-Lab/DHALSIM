import argparse
from py2_logger import logger
import os
import signal
import subprocess
import sys
from pathlib import Path

import yaml


class NodeControl:
    """
    This class is started for a plc. It starts a tcpdump and a plc process.
    """

    def __init__(self, intermediate_yaml, plc_index):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.intermediate_yaml = intermediate_yaml
        self.plc_index = plc_index

        with self.intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

        self.output_path = Path(self.data["output_path"])

        self.process_tcp_dump = None
        self.plc_process = None

        self.this_plc_data = self.data["plcs"][self.plc_index]

    def sigint_handler(self, sig, frame):
        """
        Interrupt handler for :class:`~signal.SIGINT` and :class:`~signal.SIGINT`.
        """
        self.terminate()
        sys.exit(0)

    def terminate(self):
        """
        This function stops the tcp dump and the plc process.
        """
        logger.debug("Stopping Tcp dump process on PLC...")
        # self.process_tcp_dump.kill()

        self.process_tcp_dump.send_signal(signal.SIGINT)
        self.process_tcp_dump.wait()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.terminate()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.kill()

        logger.debug("Stopping PLC...")

        self.plc_process.send_signal(signal.SIGINT)
        self.plc_process.wait()
        if self.plc_process.poll() is None:
            self.plc_process.terminate()
        if self.plc_process.poll() is None:
            self.plc_process.kill()

    def main(self):
        """
        This function starts the tcp dump and plc process and then waits for the plc
        process to finish.
        """
        self.process_tcp_dump = self.start_tcpdump_capture()

        self.plc_process = self.start_plc()

        while self.plc_process.poll() is None:
            pass

        self.terminate()

    def start_tcpdump_capture(self):
        """
        Start a tcp dump.
        """
        pcap = self.output_path / (self.this_plc_data["interface"] + '.pcap')

        # Output is not printed to console
        f = open('/dev/null', 'w')
        tcp_dump = subprocess.Popen(['tcpdump', '-i', self.this_plc_data["interface"], '-w',
                                     str(pcap)], shell=False, stderr=f, stdout=f)
        return tcp_dump

    def start_plc(self):
        """
        Start a plc process.
        """
        generic_plc_path = Path(__file__).parent.absolute() / "generic_plc.py"

        cmd = ["python2", str(generic_plc_path), str(self.intermediate_yaml), str(self.plc_index)]

        # Output is not printed to console
        f = open('/dev/null', 'w')
        plc_process = subprocess.Popen(cmd, shell=False, stderr=f, stdout=f)
        return plc_process


def is_valid_file(parser_instance, arg):
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start everything for a plc')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument(dest="index", help="Index of PLC in intermediate yaml", type=int,
                        metavar="N")

    args = parser.parse_args()
    node_control = NodeControl(Path(args.intermediate_yaml), args.index)
    node_control.main()
