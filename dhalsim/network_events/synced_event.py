import random
import signal
import sqlite3
import subprocess
import sys
import time
from abc import ABCMeta, abstractmethod
from pathlib import Path

import yaml

from dhalsim.py3_logger import get_logger


class Error(Exception):
    """Base class for exceptions in this module."""


class DatabaseError(Error):
    """Raised when not being able to connect to the database"""


class UnsupportedTrigger(Error):
    """ Raised when a trigger othen that time is used with a network event"""


class SyncedEvent(metaclass=ABCMeta):
    """
    This class can be used to make a network event script.
    It provides a lot of useful function.
    It has a function that is called on every iteration of the simulation.
    It also processes the trigger of this event.
    It sets the `state` to 1 and calls :meth:`~dhalsim.network_events.synced_event.SyncedEvent.setup` when the
    event should go from not running to running.
    It sets the `state` to 0 and calls :meth:`~dhalsim.network_events.synced_event.SyncedEvent.teardown`when the
    event should go from  running to not running.

    :param intermediate_yaml_path: The path to the intermediate yaml file.
       This is where all the information is that a event needs to know.
    :type intermediate_yaml_path: Path

    :param yaml_index: The intermediate yaml has a list of event events.
       This number is the index of this event.
    :type yaml_index: int
    """

    DB_TRIES = 10
    """Amount of times a db query will retry on a exception"""

    DB_SLEEP_TIME = random.uniform(0.01, 0.1)
    """Amount of time a db query will wait before retrying"""

    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.yaml_index = yaml_index

        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.logger = get_logger(self.intermediate_yaml['log_level'])

        # Get the event that we are from the intermediate YAML
        self.intermediate_event = self.intermediate_yaml["network_events"][self.yaml_index]

        self.state = 0

        # Initialize database connection
        self.initialize_db()

    def main_loop(self):
        """
        The main loop of an event.
        """
        while True:
            while self.get_sync():
                time.sleep(0.01)

            run = self.check_trigger()
            self.set_event_flag(run)
            if self.state == 0:
                if run:
                    self.state = 1
                    self.setup()
            elif self.state == 1 and (not run):
                self.state = 0
                self.teardown()

            self.event_step()

            self.set_sync(1)

    def sigint_handler(self, sig, frame):
        """Interrupt handler for event being stoped"""
        self.logger.debug("{name} event shutdown".format(name=self.intermediate_event["name"]))
        self.interrupt()
        sys.exit(0)

    def initialize_db(self):
        """
        Function that initializes event connection to the database
        """
        self.conn = sqlite3.connect(self.intermediate_yaml["db_path"])
        self.cur = self.conn.cursor()

    def db_query(self, query, parameters=None):
        """
        Execute a query on the database
        On a :code:`sqlite3.OperationalError` it will retry with a max of :code:`DB_TRIES` tries.
        Before it reties, it will sleep for :code:`DB_SLEEP_TIME` seconds.
        This is necessary because of the limited concurrency in SQLite.

        :param query: The SQL query to execute in the db
        :type query: str

        :param parameters: The parameters to put in the query. This must be a tuple.

        :raise DatabaseError: When a :code:`sqlite3.OperationalError` is still raised after
           :code:`DB_TRIES` tries.
        """
        for i in range(self.DB_TRIES):
            try:
                if parameters:
                    self.cur.execute(query, parameters)
                else:
                    self.cur.execute(query)
                return
            except sqlite3.OperationalError as exc:
                self.logger.debug(
                    "Failed to connect to db with exception {exc}. Trying {i} more times.".format(
                        exc=exc, i=self.DB_TRIES - i - 1))
                time.sleep(self.DB_SLEEP_TIME)
        self.logger.error(
            "Failed to connect to db. Tried {i} times.".format(i=self.DB_TRIES))
        raise DatabaseError("Failed to get master clock from database")

    def get_master_clock(self) -> int:
        """
        Get the value of the master clock of the physical process through the database.

        :return: Iteration in the physical process
        """
        # Fetch master_time
        self.db_query("SELECT time FROM master_time WHERE id IS 1")
        master_time = self.cur.fetchone()[0]
        return master_time

    def check_trigger(self) -> bool:
        """
        Check if the trigger given is satisfied
        A trigger looks like this for a trigger basted on time:

        .. code-block:: yaml

            trigger:
              type: time
              start: 15
              end: 40

        :return: Boolean indicating whether or not to run the event
        """

        # todo: Add a validation, the only trigger valid wit this event is time
        if self.intermediate_event['trigger']['type'] == "time":
            start = self.intermediate_event['trigger']['start']
            end = self.intermediate_event['trigger']['end']
            if start <= self.get_master_clock() <= end:
                return True
            else:
                return False
        else:
            raise UnsupportedTrigger("Network events only support time type trigger")

    def get_sync(self) -> bool:
        """
        Get the sync flag of this event.

        :return: False if physical process wants the event to do a iteration, True if not.
        """
        self.db_query("SELECT flag FROM sync WHERE name IS ?", (self.intermediate_event["name"],))
        flag = bool(self.cur.fetchone()[0])
        return flag

    def set_sync(self, flag):
        """
        Set this events sync flag in the sync table. When this is 1, the physical process
        knows this event finished the requested iteration.

        :param flag: True for sync to 1, false for sync to 0
        """
        self.db_query("UPDATE sync SET flag=? WHERE name IS ?", (int(flag), self.intermediate_event["name"],))
        self.conn.commit()

    def set_event_flag(self, flag):
        """
        Set a flag in the event table. When it is 1, we know that the event with the
        provided name is currently running. When it is 0, it is not.

        :param flag: True for running to 1, false for running to 0
        """
        self.db_query("UPDATE event SET flag=? WHERE name IS ?", (int(flag), self.intermediate_event['name']))
        self.conn.commit()

    @abstractmethod
    def event_step(self):
        """
        This function is the function that will run for every iteration.
        This function needs to be overwritten.
        """

    @abstractmethod
    def setup(self):
        """
        This function sets up an event
        This should be called when an event should run, for example when
        a trigger triggers
        """

    @abstractmethod
    def teardown(self):
        """
        This function stops the event correctly
        This should be called when event should stop, for example when a
        trigger is not met anymore
        """

    def interrupt(self):
        """
        This function is the function that will bee called when there is a interrupt.
        This function needs to be overwritten if you want to do any cleanup on a interrupt.
        """
