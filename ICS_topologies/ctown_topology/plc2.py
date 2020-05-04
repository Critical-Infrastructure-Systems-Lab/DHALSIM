from minicps.devices import PLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import T1, PLC2_ADDR
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time

logging.basicConfig(filename='plc2_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc2_log_path = 'plc2.log'

def write_output(saved_tank_levels):
    print 'DEBUG plc2 shutdown'
    with open('output/plc2_saved_tank_levels_received.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(saved_tank_levels)
    exit(0)

class PLC2(PLC):

    def pre_loop(self):
        print 'DEBUG: plc2 enters pre_loop'
        self.local_time = 0

    def main_loop(self):

        saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        while True:
            try:
                self.t1 = Decimal(self.get(T1))
                self.local_time += 1
                saved_tank_levels.append([self.local_time, datetime.now(), self.t1])

                print("Tank Level 1 %f " % self.t1)
                print("ITERATION %d ------------- " % self.local_time)
                self.send(T1, self.t1, PLC2_ADDR)

            except KeyboardInterrupt:
                write_output(saved_tank_levels)

if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)