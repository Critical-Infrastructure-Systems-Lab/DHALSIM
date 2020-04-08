from minicps.devices import PLC
from utils import PLC9_DATA, STATE, PLC9_PROTOCOL
from utils import T7, PLC9_ADDR
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time

logging.basicConfig(filename='plc9_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc9_log_path = 'plc9.log'

def write_output(saved_tank_levels):
    print 'DEBUG plc9 shutdown'
    with open('output/plc9_saved_tank_levels_received.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(saved_tank_levels)
    exit(0)

class PLC9(PLC):

    def pre_loop(self):
        print 'DEBUG: plc9 enters pre_loop'
        self.local_time = 0

    def main_loop(self):

        saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        while True:
            try:
                self.t7 = Decimal(self.get(T7))
                self.local_time += 1
                saved_tank_levels.append([self.local_time, datetime.now(), self.t7])

                print("Tank Level %f " % self.t7)
                print("Applying control")
                print("ITERATION %d ------------- " % self.local_time)
                self.send(T7, self.t7, PLC9_ADDR)

            except KeyboardInterrupt:
                write_output(saved_tank_levels)

if __name__ == "__main__":
    plc9 = PLC9(
        name='plc9',
        state=STATE,
        protocol=PLC9_PROTOCOL,
        memory=PLC9_DATA,
        disk=PLC9_DATA)