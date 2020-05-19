from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T0, T2, P_RAW1, V_PUB, flag_attack_plc1, PLC2_ADDR

import csv
from datetime import datetime
from decimal import Decimal

import time
import sqlite3
import signal
import sys
from utils import ATT_1, ATT_2

plc1_log_path = 'plc1.log'


class PLC1(PLC):

    def write_output(self):
        print 'DEBUG plc1 shutdown'
        with open('output/plc1_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)
        exit(0)

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'
        self.local_time = 0
        self.t0 = Decimal(self.get(T0))
        self.saved_tank_levels = [["iteration", "timestamp", "T0"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):
        while True:
            try:
                self.local_time += 1
                self.t0 = Decimal(self.get(T0))
                self.t2 = Decimal(self.receive( T2, PLC2_ADDR ))
                print("ITERATION %d ------------- " % self.local_time)
                print("Tank 1 Level %f " % self.t1)
                self.saved_tank_levels.append([datetime.now(), self.t0])

                if self.t0 < 0.3008:
                    print("Close P_RAW1")
                    self.set(P_RAW1, 0)

                    print("Open V_PUB")
                    self.set(V_PUB, 1)

                if self.t0 > 0.576:
                    print("Closing V_PUB")
                    self.set(V_PUB, 0)

                if self.t2 < 0.08:
                    print("Opening P_RAW1")
                    self.set(P_RAW1, 1)

                if self.t2 > 0.36:
                    print("Closing P_RAW1")
                    self.set(P_RAW1, 0)

                self.set(ATT_1, 0)
                time.sleep(0.1)

            except Exception:
                continue


if __name__ == "__main__":
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)