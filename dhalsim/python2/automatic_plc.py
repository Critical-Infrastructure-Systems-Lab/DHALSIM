import os
import subprocess
import time
import sys
import argparse
import signal
import shlex
import yaml
from pathlib import Path


class NodeControl:

    def __init__(self, intermediate_yaml, plc_index):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.intermediate_yaml = intermediate_yaml
        self.plc_index = plc_index

        with self.intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

        self.this_plc_data = self.data["plcs"][self.plc_index]

    def sigint_handler(self, sig, frame):
        self.terminate()
        sys.exit(0)

    def terminate(self):
        print "Stopping Tcp dump process on PLC..."
        # self.process_tcp_dump.kill()

        self.process_tcp_dump.send_signal(signal.SIGINT)
        self.process_tcp_dump.wait()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.terminate()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.kill()

        print "Stopping PLC..."
        self.plc_process.send_signal(signal.SIGINT)
        self.plc_process.wait()
        if self.plc_process.poll() is None:
            self.plc_process.terminate()
        if self.plc_process.poll() is None:
            self.plc_process.kill()

    def main(self):
        self.interface_name = self.this_plc_data["interface"]
        self.delete_log()
        self.process_tcp_dump = self.start_tcpdump_capture()

        self.plc_process = self.start_plc()

        while self.plc_process.poll() is None:
            pass

        self.terminate()

    def delete_log(self):
        subprocess.call(['rm', '-rf', self.this_plc_data["name"] + '.log'])

    def start_tcpdump_capture(self):
        pcap = self.interface_name + '.pcap'
        tcp_dump = subprocess.Popen(['tcpdump', '-i', self.interface_name, '-w', 'output/' + pcap], shell=False)
        return tcp_dump

    def start_plc(self):
        cmd = ["python2", "generic_plc.py", str(self.intermediate_yaml), str(self.plc_index)]

        plc_process = subprocess.Popen(cmd, shell=False, stderr=sys.stderr, stdout=sys.stdout)
        return plc_process


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start everything for a plc')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument(dest="index", help="Index of PLC in intermediate yaml", type=int, metavar="N")

    args = parser.parse_args()
    node_control = NodeControl(Path(args.intermediate_yaml), args.index)
    node_control.main()
