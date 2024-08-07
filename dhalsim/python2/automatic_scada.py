import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

from automatic_node import NodeControl
from dhalsim.py3_logger import get_logger

empty_loc = '/dev/null'


class ScadaControl(NodeControl):
    """
    This class is started for a scada. It starts a tcpdump and a scada process.
    """

    PROCESS_TIMEOUT = 1.0
    """Timeout between sending SIGINT, SIGTERM, and a SIGKILL"""

    def __init__(self, intermediate_yaml):
        super(ScadaControl, self).__init__(intermediate_yaml)

        self.logger = get_logger(self.data['log_level'])

        self.output_path = Path(self.data["output_path"])
        self.process_tcp_dump = None
        self.scada_process = None

    def terminate_process(self, process):
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        try:
            process.wait(self.PROCESS_TIMEOUT)
        except subprocess.TimeoutExpired:
            if process.poll() is None:
                process.terminate()
            if process.poll() is None:
                process.kill()

    def terminate(self):
        """
        This function stops the tcp dump and the plc process.
        """
        self.logger.debug("Stopping tcpdump process on SCADA.")
        self.terminate_process(self.process_tcp_dump)
        self.logger.debug("Tcpdump process stopped on SCADA.")

        self.logger.debug("Stopping SCADA.")
        self.terminate_process(self.scada_process)
        self.logger.debug("SCADA stopped on automatic SCADA")

    def main(self):
        """
        This function starts the tcp dump and scada process and then waits for the scada
        process to finish.
        """
        self.process_tcp_dump = self.start_tcpdump_capture()

        self.scada_process = self.start_scada()

        while self.scada_process.poll() is None:
            pass

        self.terminate()

    def start_tcpdump_capture(self):
        """
        Start a tcp dump.
        """
        pcap = self.output_path / "scada-eth0.pcap"

        # Output is not printed to console
        no_output = open(empty_loc, 'w')
        tcp_dump = subprocess.Popen(['tcpdump', '-i', self.data["scada"]["interface"], '-w',
                                     str(pcap)], shell=False, stdout=no_output, stderr=no_output)
        return tcp_dump

    def start_scada(self):
        """
        Start a scada process.
        """
        generic_scada_path = Path(__file__).parent.absolute() / "generic_scada.py"

        if self.data['log_level'] == 'debug':
            err_put = sys.stderr
            out_put = sys.stdout
        else:
            err_put = open(empty_loc, 'w')
            out_put = open(empty_loc, 'w')
        cmd = ["python3", str(generic_scada_path), str(self.intermediate_yaml)]
        scada_process = subprocess.Popen(cmd, shell=False, stderr=err_put, stdout=out_put)
        return scada_process


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

    args = parser.parse_args()
    scada = ScadaControl(Path(args.intermediate_yaml))
    scada.main()
