import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

from automatic_node import NodeControl


class PlcControl(NodeControl):
    """
    This class is started for a plc. It starts a tcpdump and a plc process.
    """

    def __init__(self, intermediate_yaml, plc_index):
        super(PlcControl, self).__init__(intermediate_yaml)

        self.plc_index = plc_index
        self.output_path = Path(self.data["output_path"])
        self.process_tcp_dump = None
        self.plc_process = None
        self.this_plc_data = self.data["plcs"][self.plc_index]

    def terminate(self):
        """
        This function stops the tcp dump and the plc process.
        """
        print("Stopping tcpdump process on PLC...")
        self.process_tcp_dump.send_signal(signal.SIGINT)
        self.process_tcp_dump.wait()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.terminate()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.kill()

        print("Stopping PLC...")
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
        tcp_dump = subprocess.Popen(['tcpdump', '-i', self.this_plc_data["interface"], '-w',
                                     str(pcap)], shell=False)
        return tcp_dump

    def start_plc(self):
        """
        Start a plc process.
        """
        generic_plc_path = Path(__file__).parent.absolute() / "generic_plc.py"

        cmd = ["python2", str(generic_plc_path), str(self.intermediate_yaml), str(self.plc_index)]

        plc_process = subprocess.Popen(cmd, shell=False, stderr=sys.stderr, stdout=sys.stdout)
        return plc_process


def is_valid_file(parser_instance, arg):
    """
    Verifies whether the intermediate yaml path is valid.
    """
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
    plc_control = PlcControl(Path(args.intermediate_yaml), args.index)
    plc_control.main()
