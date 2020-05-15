from minicps.devices import PLC
from utils import PLC5_DATA, STATE, PLC5_PROTOCOL
from utils import T5, T7, PU8, PU10, PU11, PLC7_ADDR, PLC9_ADDR

import csv
from datetime import datetime
from decimal import Decimal
import time
import signal
import sys

class PLC5(PLC):

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def write_output(self):
        print 'DEBUG plc5 shutdown'
        with open('output/plc5_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)
        exit(0)

    def pre_loop(self):
        print 'DEBUG: plc5 enters pre_loop'
        self.local_time = 0
        self.saved_tank_levels = [["iteration", "timestamp", "T5", "T7"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):

        while True:
            try:
                self.local_time += 1
                self.t5 = Decimal(self.receive( T5, PLC7_ADDR ))
                self.t7 = Decimal(self.receive( T7, PLC9_ADDR ))
                print("ITERATION %d ------------- " % self.local_time)
                print("T5 Level %f " % self.t5)
                print("T7 Level %f " % self.t7)

                self.saved_tank_levels.append([datetime.now(), self.t5, self.t7])

                if self.t5 < 1.5:
                    print("Opening PU8")
                    self.set(PU8, 1)

                if self.t5 > 4.5:
                    print("Closing PU8")
                    self.set(PU8, 0)

                if self.t7 < 2.5:
                    print("Opening PU10")
                    self.set(PU10, 1)

                if self.t7 > 4.8:
                    print("Closing PU10")
                    self.set(PU10, 0)

                if self.t7 < 1.0:
                    print("Opening PU11")
                    self.set(PU11, 1)

                if self.t7 > 3.0:
                    print("Closing PU11")
                    self.set(PU11, 0)

                time.sleep(0.1)

            except Exception:
                continue

if __name__ == "__main__":
    plc5 = PLC5(
        name='plc5',
        state=STATE,
        protocol=PLC5_PROTOCOL,
        memory=PLC5_DATA,
        disk=PLC5_DATA)