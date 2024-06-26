import argparse
import csv
import os.path
import random
import signal
import sqlite3
import sys
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import yaml
from basePLC import BasePLC

from dhalsim import py3_logger
import threading
import pandas as pd


class Error(Exception):
    """Base class for exceptions in this module."""


class TagDoesNotExist(Error):
    """Raised when tag you are looking for does not exist"""


class InvalidControlValue(Error):
    """Raised when tag you are looking for does not exist"""


class DatabaseError(Error):
    """Raised when not being able to connect to the database"""


class GenericScada(BasePLC):
    """
    This class represents a scada. This scada knows what plcs it is collecting data from by reading the
    yaml file at intermediate_yaml_path and looking at the plcs.
    """

    DB_TRIES = 10
    """Amount of times a db query will retry on a exception"""

    SCADA_CACHE_UPDATE_TIME = 2
    """ Time in seconds the SCADA server updates its cache"""

    PLC_UPDATE_TIMEOUT_TICK = 0.2
    """ Time in seconds the SCADA server waits to update a PLC cache"""

    PLC_UPDATE_TIMEOUT_TICKS_NUMBER = 29
    """ Number of ticks to wait for PLC update"""


    def __init__(self, intermediate_yaml_path):
        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.logger = py3_logger.get_logger(self.intermediate_yaml['log_level'])
        self.output_path = Path(self.intermediate_yaml["output_path"]) / "scada_values.csv"
        self.output_path.touch(exist_ok=True)

        # Create state from db values
        state = {
            'name': "plant",
            'path': self.intermediate_yaml['db_path']
        }

        # Create server, real tags are generated
        scada_server = {
            'address': self.intermediate_yaml['scada']['local_ip'],
            'tags': self.generate_real_tags(self.intermediate_yaml['plcs'])
        }

        # Create protocol
        scada_protocol = {
            'name': 'enip',
            'mode': 1,
            'server': scada_server
        }

        # Simple data has PLC tags, without the index (T101, 1) becomes T101
        self.plc_data, self.simple_plc_data  = self.generate_plcs()

        for PLC in self.intermediate_yaml['plcs']:
            if 'sensors' not in PLC:
                PLC['sensors'] = list()

            if 'actuators' not in PLC:
                PLC['actuators'] = list()

        self.update_cache_flag = False
        self.plcs_ready = False

        columns_list = ['iteration', 'timestamp']
        columns_list.extend(self.get_scada_tags())


        self.cache = pd.DataFrame(columns=columns_list)
        self.cache.loc[0] = 0

        self.updated_plc = {}

        # Flag used to ensure that we do not have empty rows in the scada_values.csv file
        for ip in self.plc_data:
            self.updated_plc[ip] = False

        self.scada_run = True

        self.do_super_construction(scada_protocol, state)

    def do_super_construction(self, scada_protocol, state):
        """
        Function that performs the super constructor call to SCADAServer
        Introduced to better facilitate testing
        """
        super(GenericScada, self).__init__(name='scada', state=state, protocol=scada_protocol)

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

        # self.logger.debug('SCADA tags: ' + str(aux_scada_tags))
        return aux_scada_tags

    @staticmethod
    def generate_real_tags(plcs):
        """
        Generates real tags with all sensors and actuators attached to plcs in the network.
        :param plcs: list of plcs
        """
        real_tags = []

        for plc in plcs:
            if 'sensors' not in plc:
                plc['sensors'] = list()

            if 'actuators' not in plc:
                plc['actuators'] = list()

            for sensor in plc['sensors']:
                if sensor != "":
                    real_tags.append((sensor, 1, 'REAL'))
            for actuator in plc['actuators']:
                if actuator != "":
                    real_tags.append((actuator, 1, 'REAL'))

        return tuple(real_tags)

    @staticmethod
    def generate_tags(taggable):
        """
        Generates tags from a list of taggable entities (sensor or actuator)
        :param taggable: a list of strings containing names of things like tanks, pumps, and valves
        """
        tags = []

        if taggable:
            for tag in taggable:
                if tag and tag != "":
                    tags.append((tag, 1))

        return tags

    def pre_loop(self, sleep=0.5):
        """
        The pre loop of a SCADA. In which setup actions are started.
        :param sleep:  (Default value = 0.5) The time to sleep after setting everything up
        """
        self.logger.debug('SCADA enters pre_loop')
        self.db_sleep_time = random.uniform(0.01, 0.1)

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.keep_updating_flag = True
        self.cache_update_process = None

        time.sleep(sleep)

    def db_query(self, query, write=False, parameters=None):
        """
        Execute a query on the database
        On a :code:`sqlite3.OperationalError` it will retry with a max of :code:`DB_TRIES` tries.
        Before it reties, it will sleep for :code:`DB_SLEEP_TIME` seconds.
        This is necessary because of the limited concurrency in SQLite.
        :param query: The SQL query to execute in the db
        :type query: str
        :param write: Boolean flag to indicate if this query will write into the database
        :param parameters: The parameters to put in the query. This must be a tuple.
        :raise DatabaseError: When a :code:`sqlite3.OperationalError` is still raised after
           :code:`DB_TRIES` tries.
        """
        for i in range(self.DB_TRIES):
            try:
                with sqlite3.connect(self.intermediate_yaml["db_path"]) as conn:
                    cur = conn.cursor()
                    if parameters:
                        cur.execute(query, parameters)
                    else:
                        cur.execute(query)
                    conn.commit()

                    if not write:
                        return cur.fetchone()[0]
                    else:
                        return
            except sqlite3.OperationalError as exc:
                self.logger.info(
                    "Failed to connect to db with exception {exc}. Trying {i} more times.".format(
                        exc=exc, i=self.DB_TRIES - i - 1))
                time.sleep(self.db_sleep_time)

        self.logger.error("Failed to connect to db. Tried {i} times.".format(i=self.DB_TRIES))
        raise DatabaseError("Failed to get master clock from database")

    def get_sync(self, flag):
        """
        Get the sync flag of this plc.
        On a :code:`sqlite3.OperationalError` it will retry with a max of :code:`DB_TRIES` tries.
        Before it reties, it will sleep for :code:`DB_SLEEP_TIME` seconds.
        :return: False if physical process wants the plc to do a iteration, True if not.
        :raise DatabaseError: When a :code:`sqlite3.OperationalError` is still raised after
           :code:`DB_TRIES` tries.
        """
        res = self.db_query("SELECT flag FROM sync WHERE name IS ?", False, ('scada',))
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
        self.db_query("UPDATE sync SET flag=? WHERE name IS ?", True, (int(flag), 'scada',))

    def stop_cache_update(self):
        self.update_cache_flag = False

    def sigint_handler(self, sig, frame):
        """
        Shutdown protocol for the scada, writes the output before exiting.
        """
        self.stop_cache_update()
        self.write_output()
        self.scada_run = False
        self.logger.debug("SCADA shutdown")
        sys.exit(0)

    def write_output(self):
        """
        Writes the csv output of the scada
        """
        results = self.cache        
        results.to_csv(self.output_path, index=False)

    def generate_plcs(self):
        """
        Generates a list of tuples, the first part being the ip of a PLC,
        and the second  being a list of tags attached to that PLC.
        """
        plcs = OrderedDict()
        plcs_simple_tags = OrderedDict()

        for PLC in self.intermediate_yaml['plcs']:
            if 'sensors' not in PLC:
                PLC['sensors'] = list()

            if 'actuators' not in PLC:
                PLC['actuators'] = list()

            tags = []
            simple_tags = []

            tags.extend(self.generate_tags(PLC['sensors']))
            tags.extend(self.generate_tags(PLC['actuators']))

            simple_tags.extend(PLC['sensors'])
            simple_tags.extend(PLC['actuators'])

            plcs[PLC['public_ip']] = tags
            plcs_simple_tags[PLC['public_ip']] = simple_tags

        return plcs, plcs_simple_tags

    def get_master_clock(self):
        """
        Get the value of the master clock of the physical process through the database.
        On a :code:`sqlite3.OperationalError` it will retry with a max of :code:`DB_TRIES` tries.
        Before it reties, it will sleep for :code:`DB_SLEEP_TIME` seconds.
        :return: Iteration in the physical process.
        :raise DatabaseError: When a :code:`sqlite3.OperationalError` is still raised after
           :code:`DB_TRIES` tries.
        """
        master_time = self.db_query("SELECT time FROM master_time WHERE id IS 1", False, None)
        return master_time

    def update_cache(self, lock, cache_update_time):
        """
        Update the cache of the scada by receiving all the required tags.
        When something cannot be received, the previous values are used.
        """

        while self.update_cache_flag:
            for plc_ip in self.plc_data:
                try:                
                    values = self.receive_multiple(self.plc_data[plc_ip], plc_ip)                    
                    values_float = [float(x) for x in values]
                    if len(values_float) == len(self.simple_plc_data[plc_ip]):
                        with lock: 
                            clock = int(self.get_master_clock())
                            self.cache.loc[clock, self.simple_plc_data[plc_ip]] = values_float
                            self.cache.loc[clock, 'iteration'] = clock
                            self.updated_plc[plc_ip] = True
                except Exception as e:
                    self.logger.error(
                        "PLC receive_multiple with tags {tags} from {ip} failed with exception '{e}'".format(
                            tags=self.plc_data[plc_ip],
                            ip=plc_ip, e=str(e)))
                    if self.update_cache_flag:
                        continue
                    else:
                        return

                #self.logger.debug(
                #    "SCADA cache updated for {tags}, with value {values}, from {ip}".format(tags=self.plc_data[plc_ip],
                #                                                                             values=values,
                #                                                                             ip=plc_ip))

            time.sleep(cache_update_time)

    def get_plc_updated_flags(self):
        # self.logger.debug(self.updated_plc)
        return all(value == True for value in self.updated_plc.values())

    def main_loop(self, sleep=0.5, test_break=False):
        """
        The main loop of a PLC. In here all the controls will be applied.
        :param sleep:  (Default value = 0.5) Not used
        :param test_break:  (Default value = False) used for unit testing, breaks the loop after one iteration
        """
        self.logger.debug("SCADA enters main_loop")
        lock = None

        while self.scada_run:
            while not self.get_sync(0):
                time.sleep(self.db_sleep_time)

            self.set_sync(1)

            while not self.get_sync(2):
                pass

            if not self.plcs_ready:
                self.plcs_ready = True
                self.update_cache_flag = True
                self.logger.debug("SCADA starting update cache thread")
                lock = threading.Lock()
                self.cache_thread = threading.Thread(target=self.update_cache,
                                                     args=[lock, self.SCADA_CACHE_UPDATE_TIME], daemon=True)
                self.cache_thread.start()

                # Wait one scada update time 
                time.sleep(self.SCADA_CACHE_UPDATE_TIME)

            for retry in range(self.PLC_UPDATE_TIMEOUT_TICKS_NUMBER):
                if self.get_plc_updated_flags(): 
                    break
                else:
                    # self.logger.debug(f'Waiting for plcs to be updated, tick {retry}')           
                    time.sleep(self.PLC_UPDATE_TIMEOUT_TICK)

            # self.logger.debug('Finished waiting')  
            master_time = datetime.now()
            clock = int(self.get_master_clock())
            self.cache.loc[clock, 'timestamp'] = master_time

            for ip in self.plc_data:
                if self.cache.loc[clock, self.simple_plc_data[ip]].isnull().any():
                    # If any PLC values are empty, use previous value
                    self.cache.loc[clock, self.simple_plc_data[ip]] = self.cache.loc[clock-1, self.simple_plc_data[ip]]
                self.updated_plc[ip] = False

            # Save scada_values.csv when needed
            if 'saving_interval' in self.intermediate_yaml and master_time != 0 and \
                master_time % self.intermediate_yaml['saving_interval'] == 0:
                self.write_output()

            self.set_sync(3)

            if test_break:
                break

def is_valid_file(parser_instance, arg):
    """
    Verifies whether the intermediate yaml path is valid.
    :param parser_instance: instance of argparser
    :param arg: the path to check
    """
    if not os.path.exists(arg):
        parser_instance.error(arg + " does not exist.")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start everything for a scada')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))

    args = parser.parse_args()

    plc = GenericScada(intermediate_yaml_path=Path(args.intermediate_yaml))