import signal
import sqlite3
import sys
import time
from abc import ABCMeta, abstractmethod
from pathlib import Path

import yaml

from dhalsim.py3_logger import get_logger


class SyncedAttack(metaclass=ABCMeta):
    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.yaml_index = yaml_index

        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.logger = get_logger(self.intermediate_yaml['log_level'])

        # Get the attack that we are from the intermediate YAML
        self.intermediate_attack = self.intermediate_yaml["network_attacks"][self.yaml_index]

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
        self.cur.execute("SELECT flag FROM sync WHERE name IS ?", (self.intermediate_attack["name"],))
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

            self.attack_step()

            self.set_sync(1)

    @abstractmethod
    def attack_step(self):
        """
        This function is the function that will run for every iteration.
        This function needs to be overwritten.
        """

    def interrupt(self):
        """
        This function is the function that will bee called when there is a interrupt.
        This function needs to be if you want to do any cleanup on a interrupt.
        """
