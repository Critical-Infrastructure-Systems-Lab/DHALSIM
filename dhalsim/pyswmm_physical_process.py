import argparse
import csv
import os
import signal
import logging
from datetime import datetime
import random
import pandas as pd
import progressbar
import sqlite3
import sys
import time
from pathlib import Path

from dhalsim.parser.file_generator import BatchReadmeGenerator, GeneralReadmeGenerator
from dhalsim.py3_logger import get_logger
import yaml

from decimal import Decimal


class Error(Exception):
    """Base class for exceptions in this module."""


class DatabaseError(Error):
    """Raised when not being able to connect to the database"""


class PhysicalPlant:

    WAIT_FOR_FLAG = 0.005
    """Amount of times to wait for a flag """

    DB_TRIES = 10
    """Amount of times a db query will retry on a exception"""

    def __init__(self, intermediate_yaml):
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        self.intermediate_yaml = intermediate_yaml

        with self.intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

        logging.getLogger('wntr').setLevel(logging.WARNING)
        self.logger = get_logger(self.data['log_level'])

        self.ground_truth_path = Path(self.data["output_path"]) / "ground_truth.csv"
        self.ground_truth_path.touch(exist_ok=True)

        # Use of prepared statements
        self._name = 'plant'
        self._path = self.data["db_path"]
        self._value = 'value'
        self._what = ()

        self._init_what()

        if not self._what:
            raise ValueError('Primary key not found.')
        else:
            self._init_get_query()
            self._init_set_query()

        # connection to the database
        self.db_path = self.data["db_path"]

        # get simulator: WNTR or epynet. This will impact how the controls, actuator status, and results are handled
        self.simulator = self.data["simulator"]

        self.db_update_string = "UPDATE plant SET value = ? WHERE name = ?"

        self.db_sleep_time = random.uniform(0.01, 0.1)
        self.logger.info("DB Sleep time: " + str(self.db_sleep_time))

    def interrupt(self, sig, frame):
        self.finish()
        self.logger.info("Simulation ended.")
        sys.exit(0)

    def finish(self):
        #self.write_results(self.results_list)
        end_time = datetime.now()

        #GeneralReadmeGenerator(self.intermediate_yaml, self.data['start_time'],
        #                       end_time, False, self.master_time, self.wn, self.simulation_step).write_readme()
        sys.exit(0)

    def _init_what(self):
        """Save a ordered tuple of pk field names in self._what."""
        query = "PRAGMA table_info(%s)" % self._name

        with sqlite3.connect(self._path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query)
                table_info = cursor.fetchall()

                # last tuple element
                pks = []
                for field in table_info:
                    if field[-1] > 0:
                        pks.append(field)

                if not pks:
                    self.logger.error('Please provide at least 1 primary key. Has sqlite DB been initialized?.'
                                      ' Aborting')
                    sys.exit(1)
                else:
                    # sort by pk order
                    pks.sort(key=lambda x: x[5])

                    what_list = []
                    for pk in pks:
                        what_list.append(pk[1])

                    self._what = tuple(what_list)

            except sqlite3.Error as e:
                self.logger.error('Error initializing the sqlite DB. Exiting. Error: ' + str(e))
                sys.exit(1)

    def _init_set_query(self):
        """Use prepared statements."""

        set_query = 'UPDATE %s SET %s = ? WHERE %s = ?' % (
            self._name,
            self._value,
            self._what[0])

        # for composite pk
        for pk in self._what[1:]:
            set_query += ' AND %s = ?' % (
                pk)

        self._set_query = set_query

    def _init_get_query(self):
        """Use prepared statement."""

        get_query = 'SELECT %s FROM %s WHERE %s = ?' % (
            self._value,
            self._name,
            self._what[0])

        # for composite pk
        for pk in self._what[1:]:
            get_query += ' AND %s = ?' % (
                pk)

        self._get_query = get_query

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
        #"UPDATE sync SET flag=2"
        self.db_query("UPDATE sync SET flag=?", True, (int(flag),))

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
                with sqlite3.connect(self.data["db_path"]) as conn:
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
        raise DatabaseError("Failed to execute db query in database")

    def get_plcs_ready(self, flag):
        """
        Checks whether all PLCs have finished their loop.
        :return: boolean whether all PLCs have finished
        """
        res = self.db_query("""SELECT count(*) FROM sync WHERE flag != ?""", False, (str(flag),))
        return int(res) == 0

    def simulate_with_pyswmm(self):

        #########
        # We check that all PLCs updated their local caches and local CPPPO
        while not self.get_plcs_ready(1):
            time.sleep(self.WAIT_FOR_FLAG)

        # Notify the PLCs they can start receiving remote values
        self.set_sync(2)

        # Wait for the PLCs to apply control logic
        while not self.get_plcs_ready(3):
            time.sleep(self.WAIT_FOR_FLAG)
        #########


        # !!! Run the pyswmm simulation
        # step_results = call_simulation
        # Updates the SQLite DB
        #self.update_catchments(step_results)



        #########
        # Set sync flags for nodes
        # Don't delete this line, simulation will get stuck
        self.set_sync(0)

        # these times should be obtained from the INP file. "internal_epynet_step" is the pyswmm step time
        #simulation_time = simulation_time + internal_epynet_step
        conn = sqlite3.connect(self.data["db_path"])
        c = conn.cursor()
        c.execute("REPLACE INTO master_time (id, time) VALUES(1, ?)", (str(self.master_time),))
        conn.commit()

