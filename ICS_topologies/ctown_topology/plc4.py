from minicps.devices import PLC
from utils import PLC4_DATA, STATE, PLC4_PROTOCOL
from utils import T3, PLC4_ADDR
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time

logging.basicConfig(filename='plc4_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc4=_log_path = 'plc4.log'

def write_output(saved_tank_levels):
    print 'DEBUG plc4 shutdown'
    with open('output/plc4_saved_tank_levels_received.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(saved_tank_levels)
    exit(0)

class PLC4(PLC):

    def pre_loop(self):
        print 'DEBUG: plc4 enters pre_loop'
        self.local_time = 0

    def main_loop(self):

        saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        while True:
            try:
                self.t3 = Decimal(self.get(T3))
                self.local_time += 1
                saved_tank_levels.append([self.local_time, datetime.now(), self.t3])

                print("Tank Level %f " % self.t3)
                print("ITERATION %d ------------- " % self.local_time)
                self.send(T4, self.t3, PLC4_ADDR)

            except KeyboardInterrupt:
                write_output(saved_tank_levels)

if __name__ == "__main__":
    plc4 = PLC4(
        name='plc4',
        state=STATE,
        protocol=PLC4_PROTOCOL,
        memory=PLC4_DATA,
        disk=PLC4_DATA)