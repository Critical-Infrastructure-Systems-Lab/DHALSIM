from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T_LVL, ATT_1, PLC1_ADDR, flag_attack_plc1, flag_attack_plc2, \
    flag_attack_communication_plc1_scada, flag_attack_communication_plc1_plc2, flag_attack_dos_plc2, TIME

import csv
from datetime import datetime
from decimal import Decimal

import time
import sqlite3

plc1_log_path = 'plc1.log'


class PLC1(PLC):

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'
        self.local_time = -1
        self.tank_level = Decimal(self.get(T_LVL))

    def main_loop(self):
        """plc1 main loop.
            - reads sensors value
            - drives actuators according to the control strategy
            - updates its enip server
        """
        fake_values = []
        saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]

        while True:
            try:
                self.local_time += 1
                self.tank_level = Decimal(self.get(T_LVL))
                print("Tank Level %f " % self.tank_level)
                saved_tank_levels.append([datetime.now(), self.tank_level])
                self.send(T_LVL, self.tank_level, PLC1_ADDR)

                if flag_attack_plc1:
                    if self.local_time in range(100, 200):
                        print("Attacker is appending --------------")
                        fake_values.append(self.tank_level)
                        self.set(ATT_1, 1)
                    elif self.local_time in range(250, 350):
                        print("Under Attack---------------------- ")
                        self.set(ATT_1, 2)
                        self.tank_level = fake_values[i]
                        i += 1
                    else:
                        if flag_attack_plc2 == 0 and flag_attack_communication_plc1_scada == 0 and flag_attack_communication_plc1_plc2 == 0 and flag_attack_dos_plc2 == 0:
                            self.set(ATT_1, 0)
            except KeyboardInterrupt:
                print 'DEBUG plc1 shutdown'
                with open('output/plc1_saved_tank_levels_received.csv', 'w') as f:
                    writer = csv.writer(f)
                    writer.writerows(saved_tank_levels)
                return


if __name__ == "__main__":
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)