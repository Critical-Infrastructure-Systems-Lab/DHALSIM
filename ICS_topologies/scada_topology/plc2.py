from minicps.devices import PLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import PLC_SAMPLES, PLC_PERIOD_SEC
from utils import IP, T_LVL, P1_STS, P2_STS,ATT_1, ATT_2, PLC1_ADDR, PLC2_ADDR, ATT_ADDR
from utils import flag_attack_plc2, flag_attack_dos_plc2, flag_attack_communication_plc1_plc2
import time
import sqlite3
import csv
from datetime import datetime
import logging
from decimal import Decimal

logging.basicConfig(filename='plc2_debug.log', level=logging.DEBUG)
logging.debug("testing")

plc2_log_path = 'plc2.log'

class PLC2(PLC):

    def pre_loop(self):
        print 'DEBUG: plc2 enters pre_loop'
        with open(plc2_log_path, 'a') as plc2_log_file:
            plc2_log_file.write('DEBUG: plc2 enters main_loop')

    def main_loop(self):
        """plc2 main loop.
            - read flow level sensors #2
            - update interal enip server
        """

        saved_tank_levels = [["timestamp", "TANK_LEVEL"]]
        i = 0
        print 'DEBUG: plc2 enters main_loop.'
        while (True):
            i += 1

            try:
                tank_level = Decimal(self.receive(T_LVL, PLC1_ADDR))
                saved_tank_levels.append([datetime.now(), tank_level])
                msg = 'DEBUG PLC2 - receive from plc1 tank level: %f ' + str(tank_level) + '\n'
                # This will create a huge performance problem. Riccardo got a better way to do this? Opening the file outside the while resulted in this script not writing on the file
                with open(plc2_log_path, 'a') as plc2_log_file:
                    plc2_log_file.write(msg)

            except Exception, msg:
                print (msg)
                if flag_attack_dos_plc2:
                    self.set(ATT_1, 1)
                    continue
            except KeyboardInterrupt:
                with open('plc2_saved_tank_levels_received.csv', 'w') as f:
                    writer = csv.writer(f)
                    writer.writerows(saved_tank_levels)
                return

            if flag_attack_plc2 and 300 <= i <= 350:
                # only for intern plc2 attack, do not control in this interval
                self.set(ATT_1, 1)
                continue

            if not flag_attack_communication_plc1_plc2:
                self.set(ATT_1, 0)

            # CONTROL PUMP1
            if tank_level < 4:
                self.set(P1_STS, 1)

            if tank_level > 6.3:
                self.set(P1_STS, 0)

            # CONTROL PUMP2
            if tank_level < 1:
                self.set(P2_STS, 1)

            if tank_level > 4.5:
                self.set(P2_STS, 0)
            time.sleep(0.2)

        print 'DEBUG swat plc2 shutdown'


if __name__ == "__main__":
    # notice that memory init is different form disk init
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)
