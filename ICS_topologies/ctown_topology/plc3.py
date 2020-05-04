from minicps.devices import PLC
from utils import PLC3_DATA, STATE, PLC3_PROTOCOL
from utils import T2, T3, T4, V2, PU4, PU5, PU6, PU7, PLC4_ADDR, PLC6_ADDR

import csv
from datetime import datetime
from decimal import Decimal
import time


def write_output(saved_tank_levels):
    print 'DEBUG plc3 shutdown'
    with open('output/plc3_saved_tank_levels_received.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(saved_tank_levels)
    exit(0)

class PLC3(PLC):

    def pre_loop(self):
        print 'DEBUG: plc3 enters pre_loop'
        self.local_time = 0

    def main_loop(self):
        saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]

        while True:
            try:
                self.local_time += 1
                self.t2 = Decimal( self.get( T2 ) )
                self.t3 = Decimal(self.receive( T3, PLC4_ADDR ))
                self.t4 = Decimal(self.receive( T4, PLC6_ADDR ))
                print("ITERATION %d ------------- " % self.local_time)
                print("T2 Level %f " % self.t2)
                print("T3 Level %f " % self.t3)
                print("T4 Level %f " % self.t4)

                saved_tank_levels.append([datetime.now(), self.t2, self.t3, self.t4])

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
                    print("Opening PU6")
                    self.set(PU7, 1)

                if self.t4 > 4.5:
                    print("Closing PU6")
                    self.set(PU7, 0)

                time.sleep(0.1)

            except KeyboardInterrupt:
                write_output(saved_tank_levels)
                return
            except Exception:
                continue

if __name__ == "__main__":
    plc3 = PLC3(
        name='plc3',
        state=STATE,
        protocol=PLC3_PROTOCOL,
        memory=PLC3_DATA,
        disk=PLC3_DATA)