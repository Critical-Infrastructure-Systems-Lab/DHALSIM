from minicps.devices import PLC
from utils import PLC3_DATA, STATE, PLC3_PROTOCOL
from utils import T2, T3, T4, V2, PU4, PU5, PU6, PU7, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS

import csv
from datetime import datetime
from decimal import Decimal
import time
import signal
import sys

class PLC3(PLC):

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def write_output(self):
        print 'DEBUG plc3 shutdown'
        with open('output/plc3_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def pre_loop(self):
        print 'DEBUG: plc3 enters pre_loop'
        self.local_time = 0
        self.saved_tank_levels = [["iteration", "timestamp", "T2", "T3", "T4"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):
        while True:
            try:
                self.local_time += 1
                self.t2 = Decimal( self.get( T2 ) )
                self.t3 = Decimal(self.receive( T3, CTOWN_IPS['plc4'] ))
                self.t4 = Decimal(self.receive( T4, CTOWN_IPS['plc6'] ))

                self.saved_tank_levels.append([self.local_time, datetime.now(), self.t2, self.t3, self.t4])

                if self.t2 < 0.5:
                    print("Opening V2")
                    self.set(V2, 1)

                if self.t2 > 5.5:
                    print("Closing V2")
                    self.set(V2, 0)

                if self.t3 < 3.0:
                    print("Opening PU4")
                    self.set(PU4, 1)

                if self.t3 > 5.3:
                    print("Closing PU4")
                    self.set(PU4, 0)

                if self.t3 < 1.0:
                    print("Opening PU5")
                    self.set(PU5, 1)

                if self.t3 > 3.5:
                    print("Closing PU5")
                    self.set(PU5, 0)

                if self.t4 < 2.0:
                    print("Opening PU6")
                    self.set(PU6, 1)

                if self.t4 > 3.5:
                    print("Closing PU6")
                    self.set(PU6, 0)

                if self.t4 < 3.0:
                    print("Opening PU7")
                    self.set(PU7, 1)

                if self.t4 > 4.5:
                    print("Closing PU7")
                    self.set(PU7, 0)

                time.sleep(0.1)

            except Exception:
                continue

if __name__ == "__main__":
    plc3 = PLC3(
        name='plc3',
        state=STATE,
        protocol=PLC3_PROTOCOL,
        memory=PLC3_DATA,
        disk=PLC3_DATA)