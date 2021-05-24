import yaml
import sqlite3

from abc import ABCMeta


class SyncedAttack(metaclass=ABCMeta):
    def __init__(self, intermediate_yaml_path, yaml_index):
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

    def set_sync(self, flag):
        """
        Set this attacks sync flag in the sync table. When this is 1, the physical process
        knows this attack finished the requested iteration.

        :param flag: True for sync to 1, false for sync to 0
        """
        self.cur.execute("UPDATE sync SET flag=? WHERE name IS ?",
                         (int(flag), self.intermediate_plc["name"],))
        self.conn.commit()

    def main_loop(self, sleep=0.05):
        """
        The main loop of an attack.

        :param sleep:  (Default value = 0.05) Currently not used
        """
        while True:
            self.attack_step()
            self.set_sync(1)
            # time.sleep(sleep)

    def attack_step(self):
        """
        This function is the function that will run for every iteration.
        This function needs to be overwritten
        """
        print("This function should be overwritten!")