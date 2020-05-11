from minicps.devices import PLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import T_LVL, P1_STS, P2_STS,ATT_1, PLC1_ADDR,  \
    flag_attack_plc2, flag_attack_dos_plc2, CONTROL
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import sys
import signal

class PLC2(PLC):

    def write_output(self):
        print 'DEBUG plc2 shutdown'
        with open('output/plc2_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def sigint_handler(self, sig, frame):
        print "I received a SIGINT!"
        self.write_output()
        sys.exit(0)

    def pre_loop(self):
        print 'DEBUG: plc2 enters pre_loop'
        self.local_time = 0

    def main_loop(self):
        """plc2 main loop.
            - read flow level sensors #2
            - update interval enip server
        """

        self.saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)
        print 'DEBUG: plc2 enters main_loop.'
        self.local_time = 0

        while True:
            try:
                self.tank_level = Decimal(self.receive(T_LVL, PLC1_ADDR))

            except Exception:
                continue

            control = int(self.get(CONTROL))
            if control == 1:
                print "Continuing..."
                continue

            self.local_time += 1
            self.saved_tank_levels.append([self.local_time, datetime.now(), self.tank_level])

            if flag_attack_plc2:
                if 382 <= self.local_time <= 558:
                    self.set(ATT_1, 1)
                    self.set(P2_STS, 0)
                    continue
                else:
                    self.set(ATT_1, 0)

            if flag_attack_dos_plc2:
                self.set(ATT_1, 0)

            if self.tank_level < 4:
                self.set(P1_STS, 1)

            if self.tank_level > 6.3:
                self.set(P1_STS, 0)

            # CONTROL PUMP2
            if self.tank_level < 1:
                self.set(P2_STS, 1)

            if self.tank_level > 4.5:
                self.set(P2_STS, 0)

            time.sleep(0.1)

if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)
