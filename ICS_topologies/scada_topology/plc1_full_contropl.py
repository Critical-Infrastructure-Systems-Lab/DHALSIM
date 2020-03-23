from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import PLC_PERIOD_SEC, PLC_SAMPLES, PP_PERIOD_SEC
from utils import IP, T_LVL, ATT_1, PLC2_ADDR, PLC1_ADDR, flag_attack_plc1, flag_attack_plc2, flag_attack_communication_plc1_scada, flag_attack_communication_plc1_plc2, flag_attack_dos_plc2
from utils import IP, T_LVL, P1_STS, P2_STS,ATT_1, ATT_2, PLC1_ADDR, PLC2_ADDR, ATT_ADDR

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
        iteration = 0
        fake_values = []
        i = 0
        saved_tank_levels = [["timestamp","TANK_LEVEL"]]

        while (True):
            try:
                tank_level = Decimal(self.get(T_LVL))
                saved_tank_levels.append([datetime.now(), tank_level])
                #print 'DEBUG plc1 tank_level: %f' % tank_level
                # This will create a huge performance problem. Riccardo got a better way to do this? Opening the file outside the while resulted in this script not writing on the file
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
                iteration += 1
            except KeyboardInterrupt:
                with open('output/plc1_saved_tank_levels_received.csv', 'w') as f:
                    writer = csv.writer(f)
                    writer.writerows(saved_tank_levels)
                return
        print 'DEBUG plc1 shutdown'


if __name__ == "__main__":
    # notice that memory init is different form disk init
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)