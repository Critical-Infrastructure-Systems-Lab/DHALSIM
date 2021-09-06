import os

from dhalsim.network_events.synced_event import SyncedEvent
import argparse
from pathlib import Path


class PacketLoss(SyncedEvent):
    """
    This is a packet loss network event. This event will use tq at a switch link that causes the indicated
    percentage of packets to be lost at the link.

    :param intermediate_yaml_path: The path to the intermediate YAML file
    :param yaml_index: The index of the event in the intermediate YAML
    """

    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        super().__init__(intermediate_yaml_path, yaml_index)
        self.thread = None
        self.server = None
        self.run_thread = False
        self.tags = {}

    def setup(self):
        self.logger.info("Setting up network event")

    def teardown(self):
        self.logger.info("Tear down network event")

    def interrupt(self):
        """
        This function will be called when we want to stop the event. It calls the teardown
        function if the event is in state 1 (running)
        """
        if self.state == 1:
            self.teardown()

    def event_step(self):
        """This function just passes, as there is no required action in an event step."""
        pass


def is_valid_file(parser_instance, arg):
    """Verifies whether the intermediate yaml path is valid."""
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start everything for an event')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument(dest="index", help="Index of the network event in intermediate yaml",
                        type=int,
                        metavar="N")

    args = parser.parse_args()

    event = PacketLoss(intermediate_yaml_path=Path(args.intermediate_yaml), yaml_index=args.index)
    event.main_loop()