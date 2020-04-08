from minicps.devices import PLC
from utils import PLC7_DATA, STATE, PLC7_PROTOCOL
from utils import T5, PLC7_ADDR
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time

logging.basicConfig(filename='plc7_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc7_log_path = 'plc7.log'

def write_output(saved_tank_levels):
    print 'DEBUG plc7 shutdown'
    with open('output/plc7_saved_tank_levels_received.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(saved_tank_levels)
    exit(0)

class PLC7(PLC):

    def pre_loop(self):
        print 'DEBUG: plc7 enters pre_loop'
        self.local_time = 0

    def main_loop(self):

        saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        while True:
            try:
                self.t5 = Decimal(self.get(T5))
                self.local_time += 1
                saved_tank_levels.append([self.local_time, datetime.now(), self.t5])

                print("Tank Level %f " % self.t5)
                print("Applying control")
                print("ITERATION %d ------------- " % self.local_time)
                self.send(T5, self.t5, PLC7_ADDR)

            except KeyboardInterrupt:
                write_output(saved_tank_levels)

if __name__ == "__main__":
    plc7 = PLC7(
        name='plc7',
        state=STATE,
        protocol=PLC7_PROTOCOL,
        memory=PLC7_DATA,
        disk=PLC7_DATA)