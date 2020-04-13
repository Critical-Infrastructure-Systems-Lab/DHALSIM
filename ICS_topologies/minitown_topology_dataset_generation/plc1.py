from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T_LVL, ATT_1, PLC1_ADDR, flag_attack_plc1, flag_attack_plc2, flag_attack_communication_plc1_scada, \
    flag_attack_communication_plc1_plc2, flag_attack_dos_plc2, CONTROL

import csv
import time

from datetime import datetime
from decimal import Decimal
import thread
tank_level=3.0

def write_output(saved_tank_levels):
    print 'DEBUG plc1 shutdown'
    with open('output/plc1_saved_tank_levels_received.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(saved_tank_levels)
    exit(0)

class PLC1(PLC):

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'

    def main_loop(self):
        """plc1 main loop.
            - reads sensors value
            - drives actuators according to the control strategy
            - updates its enip server
        """
        saved_tank_levels = ["timestamp", "TANK_LEVEL"]

        while True:
            try:
                self.tank_level = Decimal(self.get(T_LVL))
                saved_tank_levels.append([datetime.now(), tank_level])
                self.send(T_LVL, self.tank_level, PLC1_ADDR)
            except KeyboardInterrupt:
                write_output(saved_tank_levels)
                return


if __name__ == "__main__":
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)