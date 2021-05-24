import sqlite3
import time
from abc import ABCMeta, abstractmethod
from pathlib import Path

import yaml


class SyncedAttack(metaclass=ABCMeta):
    def __init__(self, intermediate_yaml_path: Path, yaml_index: int):
        self.yaml_index = yaml_index

        with intermediate_yaml_path.open() as yaml_file:
            self.intermediate_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        # Get the attack that we are from the intermediate YAML
        self.intermediate_attack = self.intermediate_yaml["network_attacks"][self.yaml_index]

        # Initialize database connection
        self.initialize_db()

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
                time.sleep(0.01)

            self.attack_step()

            self.set_sync(1)

    @abstractmethod
    def attack_step(self):
        """
        This function is the function that will run for every iteration.
        This function needs to be overwritten
        """
