from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T1, PU1, PU2, flag_attack_plc1, CTOWN_IPS

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

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'
        self.local_time = 0
        self.t1 = Decimal(self.get(T1))
        self.saved_tank_levels = [["iteration", "timestamp", "T1"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):
        while True:
            try:
                self.local_time += 1
                self.t1 = Decimal(self.receive( T1, CTOWN_IPS['plc2'] ))
                print("ITERATION %d ------------- " % self.local_time)
                print("Tank 1 Level %f " % self.t1)
                self.saved_tank_levels.append([self.local_time, datetime.now(), self.t1])

                if self.t1 < 4.0:
                    print("Opening P1")
                    self.set(PU1, 1)

                if self.t1 > 6.3:
                    print("Closing P1")
                    self.set(PU1, 0)

                # This attack keeps PU2 closed
                if flag_attack_plc1 == 1:
                    # Now ATT_2 is set in the physical_process. This in order to make more predictable the attack start and end time
                    attack_on = int(self.get(ATT_2))
                    if attack_on == 1:
                        print("Attack Closing PU2")
                        self.set(ATT_1, 1)
                        self.set(PU2, 0)
                        time.sleep(0.1)
                        continue

                if self.t1 < 1.0:
                    print("Opening P2")
                    self.set(PU2, 1)

                if self.t1 > 4.5:
                    print("Closing P2")
                    self.set(PU2, 0)

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