from minicps.devices import PLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import T2, PLC2_ADDR, V_ER2i
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import signal
import sys

logging.basicConfig(filename='plc2_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc2_log_path = 'plc2.log'


class PLC2(PLC):

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def write_output(self):
        print 'DEBUG plc2 shutdown'
        with open('output/plc2_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)
        exit(0)

    def pre_loop(self):
        print 'DEBUG: plc2 enters pre_loop'
        self.local_time = 0
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)
        self.saved_tank_levels = [["iteration", "timestamp", "T2"]]
        self.timeout_counter = 0

    def main_loop(self):
        while True:
            try:
                self.local_time += 1
                self.t2 = Decimal(self.get(T2))

                if self.t2 > 0.36:
                    print("Close V_ER2i")
                    self.set(V_ER2i, 0)

                if self.t2 < 0.08:
                    print("Open V_ER2i")
                    self.set(V_ER2i, 1)

                self.saved_tank_levels.append([self.local_time, datetime.now(), self.t2])

                print("Tank Level 2 %f " % self.t2)
                print("ITERATION %d ------------- " % self.local_time)

                self.send(T2, self.t2, PLC2_ADDR)
            except Exception:
                continue

if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)