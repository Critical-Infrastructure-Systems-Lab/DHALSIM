from minicps.devices import PLC
from utils import PLC6_DATA, STATE, PLC6_PROTOCOL
from utils import T4, PLC6_ADDR
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time

logging.basicConfig(filename='plc6_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc6=_log_path = 'plc6.log'

def write_output(saved_tank_levels):
    print 'DEBUG plc6 shutdown'
    with open('output/plc6_saved_tank_levels_received.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(saved_tank_levels)
    exit(0)

class PLC6(PLC):

    def pre_loop(self):
        print 'DEBUG: plc6 enters pre_loop'
        self.local_time = 0

    def main_loop(self):

        saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        while True:
            try:
                self.t4 = Decimal(self.get(T4))
                self.local_time += 1
                saved_tank_levels.append([self.local_time, datetime.now(), self.t4])

                print("Tank Level %f " % self.t4)
                print("ITERATION %d ------------- " % self.local_time)
                self.send(T4, self.t4, PLC6_ADDR)

            except KeyboardInterrupt:
                write_output(saved_tank_levels)

if __name__ == "__main__":
    plc6 = PLC6(
        name='plc6',
        state=STATE,
        protocol=PLC6_PROTOCOL,
        memory=PLC6_DATA,
        disk=PLC6_DATA)