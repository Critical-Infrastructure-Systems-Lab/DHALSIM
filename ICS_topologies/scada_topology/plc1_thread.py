from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T_LVL, ATT_1, PLC1_ADDR, flag_attack_plc1, flag_attack_plc2, flag_attack_communication_plc1_scada, \
    flag_attack_communication_plc1_plc2, flag_attack_dos_plc2, CONTROL

import csv
import time

from datetime import datetime
from decimal import Decimal
import thread

plc1_log_path = 'plc1.log'
tank_level=3.0
# TODO: real value tag where to read/write flow sensor
class PLC1(PLC):

    def get_tank_level(self, a, b):
        while self.reader:
            global tank_level
            tank_level = Decimal(self.get(T_LVL))

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'
        self.reader = True
        thread.start_new_thread(self.get_tank_level,(0,0))

    def main_loop(self):
        iteration = 0
        fake_values = []
        i = 0
        saved_tank_levels = [["timestamp","TANK_LEVEL"]]

        while True:
            try:
                global tank_level
                saved_tank_levels.append([datetime.now(), tank_level])

                if flag_attack_plc1:
                    if iteration in range(100, 200):
                        print ("Attacker is appending --------------")
                        fake_values.append(tank_level)
                        self.set(ATT_1, 1)
                    elif iteration in range(250, 350):
                        print ("Under Attack---------------------- ")
                        self.set(ATT_1, 2)
                        tank_level = fake_values[i]
                        i += 1
                    else:
                        if flag_attack_plc2 == 0 and flag_attack_communication_plc1_scada == 0 and flag_attack_communication_plc1_plc2 == 0 and flag_attack_dos_plc2 == 0:
                            self.set(ATT_1, 0)
                self.send(T_LVL, tank_level, PLC1_ADDR)
                iteration += 1

            except KeyboardInterrupt:
                self.reader = False
                with open('output/plc1_saved_tank_levels_received.csv', 'w') as f:
                    writer = csv.writer(f)
                    writer.writerows(saved_tank_levels)
                print 'DEBUG plc1 shutdown'
                return

if __name__ == "__main__":
    # notice that memory init is different form disk init
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)