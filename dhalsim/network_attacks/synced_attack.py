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


class SyncedAttack(metaclass=ABCMeta):
    """
    This class can be used to make an attack script.
    It provides a lot of useful function.
    It has a function that is called on every iteration of the simulation.
    It also processes the trigger of this attack.
    It sets the `state` to 1 and calls :meth:`~dhalsim.network_attacks.synced_attack.SyncedAttack.setup` when the
    attack should go from not running to running.
    It sets the `state` to 0 and calls :meth:`~dhalsim.network_attacks.synced_attack.SyncedAttack.teardown`when the
    attack should go from  running to not running.

    :param intermediate_yaml_path: The path to the intermediate yaml file.
       This is where all the information is that a attacker needs to know.
    :type intermediate_yaml_path: Path

    :param yaml_index: The intermediate yaml has a list of network attacks.
       This number is the index of this attack.
    :type yaml_index: int
    :type sync: bool Flag to indicate if the sync is handled by this module. If false, another module should do the sync
    """

    DB_TRIES = 10
    """Amount of times a db query will retry on a exception"""

    def __init__(self, intermediate_yaml_path: Path, yaml_index: int, sync: bool = True):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.intermediate_yaml_path = intermediate_yaml_path
        self.yaml_index = yaml_index

        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.logger = get_logger(self.intermediate_yaml['log_level'])

        # Get the attack that we are from the intermediate YAML
        self.intermediate_attack = self.intermediate_yaml["network_attacks"][self.yaml_index]

        # Get the PLC which is the target of this attack
        for plc in self.intermediate_yaml['plcs']:
            if plc['name'] == self.intermediate_attack['target']:
                self.intermediate_plc = plc

        if self.intermediate_attack['target'].lower() == 'scada':
            self.intermediate_plc = self.intermediate_yaml['scada']

        self.attacker_ip = self.intermediate_attack['local_ip']
        self.target_plc_ip = self.intermediate_plc['local_ip']

        # Direction is an optional parameter, present in naive_mitm and simple_dos
        if 'direction' in self.intermediate_attack:
            self.direction = self.intermediate_attack['direction']
        else:
            self.direction = 'None'

        self.state = 0
        self.db_sleep_time = random.uniform(0.01, 0.1)

        self.sync = sync

    def sigint_handler(self, sig, frame):
        """Interrupt handler for attacker being stoped"""
        self.logger.debug("{name} attacker shutdown".format(name=self.intermediate_attack["name"]))
        self.interrupt()
        sys.exit(0)

    def receive_tag(self, tag: str) -> float:
        """
        This function will receive a given tag from its corresponding PLC

        When the corresponding PLC is the PLC that we are targeting with our attack , we perform
        a receive on the local PLC IP address. Otherwise, the receive will be performed on the public
        IP address of the PLC.

        :param tag: The tag we want to receive
        :return: The value of the tag
        """
        target_plc = None

        for plc in self.intermediate_yaml['plcs']:
            if tag in plc['actuators'] + plc['sensors']:
                target_plc = plc
                break

        cmd = ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address']
        if target_plc['name'] == self.intermediate_plc['name']:
            cmd.append(str(target_plc['local_ip']) + ":44818")
        else:
            cmd.append(str(target_plc['public_ip']) + ":44818")
        cmd.append(f"{tag}:1")

        try:
            client = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)

            # client.communicate is blocking
            raw_out = client.communicate()

            # Value is stored as first tuple element between a pair of square brackets
            word = raw_out[0]
            value = word[(word.find(b'[') + 1):word.find(b']')]
            return float(value)

        except Exception as error:
            print('ERROR enip _receive: ', error.with_traceback())

    def check_trigger(self) -> bool:
        """
        Check if the trigger given is satisfied
        A trigger looks like this for a trigger basted on time:

        .. code-block:: yaml

            trigger:
              type: time
              start: 15
              end: 40

        A trigger looks like one of these for a trigger basted on a sensor value:

        .. code-block:: yaml

            trigger:
              type: above
              sensor: TANK
              value: 0.16


        .. code-block:: yaml

            trigger:
              type: below
              sensor: TANK
              value: 0.16


        .. code-block:: yaml

            trigger:
              type: between
              sensor: T2
              lower_value: 0.10
              upper_value: 0.16

        :return: Boolean indicating whether or not to run the attack
        """
        if self.intermediate_attack['trigger']['type'] == "time":
            start = self.intermediate_attack['trigger']['start']
            end = self.intermediate_attack['trigger']['end']
            if start <= self.get_master_clock() <= end:
                return True
            else:
                return False
        elif self.intermediate_attack['trigger']['type'] == "above":
            value = self.intermediate_attack['trigger']['value']
            sensor_value = self.receive_tag(self.intermediate_attack['trigger']['sensor'])
            print("sensor_value:", sensor_value, ", value:", value)
            return sensor_value >= value
        elif self.intermediate_attack['trigger']['type'] == "below":
            value = self.intermediate_attack['trigger']['value']
            sensor_value = self.receive_tag(self.intermediate_attack['trigger']['sensor'])
            return sensor_value <= value
        elif self.intermediate_attack['trigger']['type'] == "between":
            lower_value = self.intermediate_attack['trigger']['lower_value']
            upper_value = self.intermediate_attack['trigger']['upper_value']
            sensor_value = self.receive_tag(self.intermediate_attack['trigger']['sensor'])
            return lower_value <= sensor_value <= upper_value
        else:
            return False

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

    def main_loop(self):
        """
        The main loop of an attack.
        """
        while True:
            if self.sync:
                # flag = 0 means a physical process finished a new iteration
                while not self.get_sync(0):
                    pass

                run = self.check_trigger()
                self.set_attack_flag(run)
                if self.state == 0:
                    if run:
                        self.state = 1
                        self.setup()
                elif self.state == 1 and (not run):
                    self.state = 0
                    self.teardown()

                # We have to keep the same state machine as PLCs
                self.set_sync(1)

                self.attack_step()

                while not self.get_sync(2):
                    pass

                self.set_sync(3)

    @abstractmethod
    def attack_step(self):
        """
        This function is the function that will run for every iteration.
        This function needs to be overwritten.
        """

    @abstractmethod
    def setup(self):
        """
        This function sets up an attack
        This should be called when an attack should run, for example when
        a trigger triggers
        """

    @abstractmethod
    def teardown(self):
        """
        This function stops the attack correctly
        This should be called when attack should stop, for example when a
        trigger is not met anymore
        """

    def interrupt(self):
        """
        This function is the function that will bee called when there is a interrupt.
        This function needs to be overwritten if you want to do any cleanup on a interrupt.
        """
