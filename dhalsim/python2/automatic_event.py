import argparse
import os
import signal
import subprocess
import sys
import py2_logger
from pathlib import Path

from automatic_node import NodeControl


class Error(Exception):
    """Base class for exceptions in this module."""


class NoSuchEvent(Error):
    """Raised when an undefined event is configured or the configuration file is empty"""


class EventControl(NodeControl):
    """This class is started for an event. It starts a network event."""

    def __init__(self, intermediate_yaml, event_index):
        super(EventControl, self).__init__(intermediate_yaml)
        self.event_index = event_index
        self.output_path = Path(self.data["output_path"])
        self.tcp_dump_process = None
        self.attacker_process = None
        self.this_event_data = self.data["network_events"][self.event_index]
        self.logger = py2_logger.get_logger(self.data['log_level'])
        self.logger.debug('Network event index: ' + str(event_index))

    def terminate(self):
        """This function stops the event process."""

        self.logger.debug("Terminating event process")
        self.event_process.send_signal(signal.SIGINT)
        self.event_process.wait()
        if self.event_process.poll() is None:
            self.event_process.terminate()
        if self.event_process.poll() is None:
            self.event_process.kill()

    def main(self):
        """This function starts event process and then waits for the network event to finish."""

        self.event_process = self.start_event()

        while self.event_process.poll() is None:
            pass

        self.terminate()

    def start_event(self):
        """Starts the event process."""
        generic_event = None
        if self.this_event_data['type'] == 'packet_loss':
            generic_event = Path(__file__).parent.parent.absolute() / "network_events" / "packet_loss.py"
        else:
            raise NoSuchEvent("Event {event} does not exists.".format(event=self.this_event_data['type']))

        cmd = ["python3", str(generic_event), str(self.intermediate_yaml), str(self.event_index)]

        # Network events are run at switches
        switch_process = subprocess.Popen(cmd, shell=False, stderr=sys.stderr, stdout=sys.stdout)
        return switch_process


def is_valid_file(parser_instance, arg):
    """Verifies whether the intermediate yaml path is valid."""
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start everything for a network event')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument(dest="index", help="Index of PLC in intermediate yaml", type=int,
                        metavar="N")

    args = parser.parse_args()
    event_control = EventControl(Path(args.intermediate_yaml), args.index)
    event_control.main()