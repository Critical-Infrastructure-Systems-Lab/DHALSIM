import signal
import sqlite3
import subprocess
import sys
import time
from abc import ABCMeta, abstractmethod
from pathlib import Path

import yaml

from dhalsim.py3_logger import get_logger


class SyncedAttack(metaclass=ABCMeta):
    """
    This class can be used to make an attack script. It provides a lot of useful function.
    It has a function that is called on every iteration of the simulation.
    It also processes the trigger of this attack. It sets the `state` to 1 and calls :meth:`~dhalsim.network_attacks.synced_attack.SyncedAttack.setup` when the
    attack should go from not running to running. It sets the `state` to 0 and calls :meth:`~dhalsim.network_attacks.synced_attack.SyncedAttack.teardown`when the
    attack should go from  running to not running.

    :param intermediate_yaml_path: The path to the intermediate yaml file.
    This is where all the information is that a attacker needs to know.
    :type intermediate_yaml_path: Path
    :param yaml_index: The intermediate yaml has a list of network attacks.
    This number is the index of this attack.
    :type yaml_index: int
    """

    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

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

        self.attacker_ip = self.intermediate_attack['local_ip']
        self.target_plc_ip = self.intermediate_plc['local_ip']

        self.state = 0

        # Initialize database connection
        self.initialize_db()

    def sigint_handler(self, sig, frame):
        """Interrupt handler for attacker being stoped"""
        self.logger.debug("{name} attacker shutdown".format(name=self.intermediate_attack["name"]))
        self.interrupt()
        sys.exit(0)

    def initialize_db(self):
        """
        Function that initializes attacker connection to the database
        """
        self.conn = sqlite3.connect(self.intermediate_yaml["db_path"])
        self.cur = self.conn.cursor()

    def get_master_clock(self):
        """
        Get the value of the master clock of the physical process through the database.

        :return: Iteration in the physical process
        """
        # Fetch master_time
        self.cur.execute("SELECT time FROM master_time WHERE id IS 1")
        master_time = self.cur.fetchone()[0]
        return master_time

    def get_sync(self):
        """
        Get the sync flag of this attack.

        :return: False if physical process wants the attack to do a iteration, True if not.
        """
        self.cur.execute("SELECT flag FROM sync WHERE name IS ?",
                         (self.intermediate_attack["name"],))
        flag = bool(self.cur.fetchone()[0])
        return flag

    def set_sync(self, flag):
        """
        Set this attacks sync flag in the sync table. When this is 1, the physical process
        knows this attack finished the requested iteration.

        :param flag: True for sync to 1, false for sync to 0
        """
        self.cur.execute("UPDATE sync SET flag=? WHERE name IS ?",
                         (int(flag), self.intermediate_attack["name"],))
        self.conn.commit()

    def main_loop(self):
        """
        The main loop of an attack.
        """
        while True:
            while self.get_sync():
                # print(pd.read_sql_query("SELECT * FROM sync;", self.conn))
                time.sleep(0.01)

            run = self.check_trigger()
            if self.state == 0:
                if run:
                    self.state = 1
                    self.setup()
            elif self.state == 1:
                if not run:
                    self.state = 0
                    self.teardown()

            self.attack_step()

            self.set_sync(1)

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
        This function needs to be if you want to do any cleanup on a interrupt.
        """
