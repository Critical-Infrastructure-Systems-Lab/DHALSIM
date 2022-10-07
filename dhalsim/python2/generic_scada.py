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
from decimal import Decimal

from pathlib import Path

import yaml
from basePLC import BasePLC

from py2_logger import get_logger
import threading
import thread



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

    def __init__(self, intermediate_yaml_path):
        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.logger = get_logger(self.intermediate_yaml['log_level'])

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

        self.plc_data = self.generate_plcs()
        self.saved_values = [['iteration', 'timestamp']]

        for PLC in self.intermediate_yaml['plcs']:
            if 'sensors' not in PLC:
                PLC['sensors'] = list()

            if 'actuators' not in PLC:
                PLC['actuators'] = list()
            self.saved_values[0].extend(PLC['sensors'])
            self.saved_values[0].extend(PLC['actuators'])

        self.update_cache_flag = False
        self.plcs_ready = False

        self.previous_cache = {}
        for ip in self.plc_data:
            self.previous_cache[ip] = [0] * len(self.plc_data[ip])

        self.cache = {}
        for ip in self.plc_data:
            self.cache[ip] = [0] * len(self.plc_data[ip])

        self.do_super_construction(scada_protocol, state)

    def do_super_construction(self, scada_protocol, state):
        """
        Function that performs the super constructor call to SCADAServer
        Introduced to better facilitate testing
        """
        super(GenericScada, self).__init__(name='scada', state=state, protocol=scada_protocol)

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
        self.logger.debug("SCADA shutdown")
        self.write_output()

        sys.exit(0)

    def write_output(self):
        """
        Writes the csv output of the scada
        """
        with self.output_path.open(mode='wb') as output:
            writer = csv.writer(output)
            writer.writerows(self.saved_values)

    def generate_plcs(self):
        """
        Generates a list of tuples, the first part being the ip of a PLC,
        and the second  being a list of tags attached to that PLC.
        """
        plcs = OrderedDict()

        for PLC in self.intermediate_yaml['plcs']:
            if 'sensors' not in PLC:
                PLC['sensors'] = list()

            if 'actuators' not in PLC:
                PLC['actuators'] = list()

            tags = []

            tags.extend(self.generate_tags(PLC['sensors']))
            tags.extend(self.generate_tags(PLC['actuators']))

            plcs[PLC['public_ip']] = tags

        return plcs

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
            for plc_ip in self.cache:
                # Maintain old values if there could not be uploaded
                try:
                    #self.logger.debug('polling plc {plc} for tags {tags}'.format(plc=plc_ip, tags=self.plc_data[plc_ip]))
                    values = self.receive_multiple(self.plc_data[plc_ip], plc_ip)
                    with lock:
                        self.cache[plc_ip] = values
                except Exception as e:
                    self.logger.error(
                        "PLC receive_multiple with tags {tags} from {ip} failed with exception '{e}'".format(
                            tags=self.plc_data[plc_ip],
                            ip=plc_ip, e=str(e)))
                    continue

                #self.logger.debug(
                #    "SCADA cache updated for {tags}, with value {values}, from {ip}".format(tags=self.plc_data[plc_ip],
                #                                                                             values=values,
                #                                                                             ip=plc_ip))

            time.sleep(cache_update_time)

    def main_loop(self, sleep=0.5, test_break=False):
        """
        The main loop of a PLC. In here all the controls will be applied.
        :param sleep:  (Default value = 0.5) Not used
        :param test_break:  (Default value = False) used for unit testing, breaks the loop after one iteration
        """
        self.logger.debug("SCADA enters main_loop")
        lock = None

        while True:
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
                thread.start_new_thread(self.update_cache, (lock, self.SCADA_CACHE_UPDATE_TIME))

            master_time = self.get_master_clock()
            results = [master_time, datetime.now()]
            with lock:
                for plc_ip in self.plc_data:
                    if self.cache[plc_ip]:
                        results.extend(self.cache[plc_ip])
                    else:
                        results.extend(self.previous_cache[plc_ip])

                self.previous_cache[plc_ip] = self.cache[plc_ip]

            self.saved_values.append(results)

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