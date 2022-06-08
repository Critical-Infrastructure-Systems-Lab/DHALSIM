import yaml
import sqlite3
import sys
import signal
import time
import random

from dhalsim.py3_logger import get_logger
from pathlib import Path
from netfilterqueue import NetfilterQueue
from abc import ABCMeta, abstractmethod

class Error(Exception):
    """Base class for exceptions in this module."""


class DatabaseError(Error):
    """Raised when not being able to connect to the database"""


class PacketQueue(metaclass=ABCMeta):
    """
    Currently, the Netfilterqueue library in Python3 does not support running in threads, using blocking calls.
    We will use this class to launch a subprocess that handles the packets in the queue.
    """

    DB_TRIES = 10
    """Amount of times a db query will retry on a exception"""

    def __init__(self,  intermediate_yaml_path: Path, yaml_index: int, queue_number: int):

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.queue_number = queue_number
        self.yaml_index = yaml_index
        self.nfqueue = None

        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.logger = get_logger(self.intermediate_yaml['log_level'])

        # Get the attack that we are from the intermediate YAML
        self.intermediate_attack = self.intermediate_yaml["network_attacks"][self.yaml_index]
        self.db_sleep_time = random.uniform(0.01, 0.1)

    def main_loop(self):
        self.logger.debug('Parent NF Class launched')
        self.nfqueue = NetfilterQueue()
        self.nfqueue.bind(self.queue_number, self.capture)
        try:
            self.logger.debug('Queue bound to number' + str(self.queue_number) + ' , running queue now')
            self.nfqueue.run()
        except Exception as exc:
            if self.nfqueue:
                self.nfqueue.unbind()
            sys.exit(0)

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
        self.logger.error(
            "Failed to connect to db. Tried {i} times.".format(i=self.DB_TRIES))
        raise DatabaseError("Failed to get master clock from database")

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

    @abstractmethod
    def capture(self, pkt):
        """
        method that handles what to do with the packets sent to the NFQueue
        :param pkt: The captured packet.
        """

    def interrupt(self):
        if self.nfqueue:
            self.nfqueue.unbind()

    def sigint_handler(self, sig, frame):
        """Interrupt handler for attacker being stoped"""
        self.logger.debug("{name} NfQueue shutdown".format(name=self.intermediate_attack["name"]))
        self.interrupt()
        sys.exit(0)


