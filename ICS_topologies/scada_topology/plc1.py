from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import PLC_PERIOD_SEC, PLC_SAMPLES, PP_PERIOD_SEC
from utils import IP, T_LVL, ATT_1, PLC2_ADDR, PLC1_ADDR, flag_attack_plc1

import csv
from datetime import datetime
from decimal import Decimal

import time
import sqlite3

plc1_log_path = 'plc1.log'

# TODO: real value tag where to read/write flow sensor
class PLC1(PLC):

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'

    def main_loop(self):
        """plc1 main loop.
            - reads sensors value
            - drives actuators according to the control strategy
            - updates its enip server
        """
        #print 'DEBUG: plc1 enters main_loop.'
        with open(plc1_log_path, 'a') as plc1_log_file:
            plc1_log_file.write('DEBUG: plc1 enters main_loop')

        iteration = 0
        fake_values = []
        i = 0
        saved_tank_levels = [["timestamp","TANK_LEVEL"]]

        while (True):
            try:
                tank_level = Decimal(self.get(T_LVL))
                saved_tank_levels.append([datetime.now(), tank_level])
                #print 'DEBUG plc1 tank_level: %f' % tank_level
                msg = 'PLC1: Tank ' + str(tank_level) + '\n'
                # This will create a huge performance problem. Riccardo got a better way to do this? Opening the file outside the while resulted in this script not writing on the file
                with open(plc1_log_path, 'a') as plc1_log_file:
                    plc1_log_file.write(msg)

                if flag_attack_plc1:
                    if iteration in range(100, 200):
                        print ("Attacker is appending --------------")
                        fake_values.append(tank_level)
                    elif iteration in range(250, 350):
                        print ("Under Attack---------------------- ")
                        self.set(ATT_1, 1)
                        tank_level = fake_values[i]
                        i += 1
                    else:
                        self.set(ATT_1, 0)

                self.send(T_LVL, tank_level, PLC1_ADDR)
                iteration += 1
            except KeyboardInterrupt:
                with open('plc1_saved_tank_levels_received.csv', 'w') as f:
                    writer = csv.writer(f)
                    writer.writerows(saved_tank_levels)
                return
            time.sleep(0.2)
        print 'DEBUG plc1 shutdown'


if __name__ == "__main__":
    # notice that memory init is different form disk init
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)