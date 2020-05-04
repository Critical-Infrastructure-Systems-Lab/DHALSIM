from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T1, PU1, PU2, PLC2_ADDR

import csv
from datetime import datetime
from decimal import Decimal

import time
import sqlite3

plc1_log_path = 'plc1.log'


def write_output(saved_tank_levels):
    print 'DEBUG plc1 shutdown'
    with open('output/plc1_saved_tank_levels_received.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(saved_tank_levels)
    exit(0)

class PLC1(PLC):

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'
        self.local_time = 0
        self.t1 = Decimal(self.get(T1))

    def main_loop(self):
        saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]

        while True:
            try:
                self.local_time += 1
                self.t1 = Decimal(self.receive( T1, PLC2_ADDR ))
                print("ITERATION %d ------------- " % self.local_time)
                print("Tank 1 Level %f " % self.t1)
                saved_tank_levels.append([datetime.now(), self.t1])

                if self.t1 < 4.0:
                    print("Opening P1")
                    self.set(PU1, 1)

                if self.t1 > 6.3:
                    print("Closing P1")
                    self.set(PU1, 0)

                if self.t1 < 1.0:
                    print("Opening P2")
                    self.set(PU2, 1)

                if self.t1 > 4.5:
                    print("Closing P2")
                    self.set(PU2, 0)

                time.sleep(0.1)

            except KeyboardInterrupt:
                write_output(saved_tank_levels)
                return
            except Exception:
                continue


if __name__ == "__main__":
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)