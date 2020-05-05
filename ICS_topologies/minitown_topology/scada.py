from minicps.devices import PLC
from utils import SCADA_PROTOCOL, STATE, SCADA_DATA
from utils import PLC1_ADDR, T_LVL

import time
import csv
from datetime import datetime
from decimal import Decimal

import signal
import sys

class SCADAServer(PLC):

    def write_output(self):
        print 'DEBUG SCADA shutdown'
        with open('output/scada_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def sigint_handler(self, sig, frame):
        print "I received a SIGINT!"
        self.write_output()
        sys.exit(0)

    def pre_loop(self, sleep=0.5):
        """scada pre loop.
            - sleep
        """
        self.saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):
        """scada main loop."""

        print("DEBUG: scada main loop")
        while True:
            try:
                tank_level = Decimal(self.receive(T_LVL, PLC1_ADDR))
                self.saved_tank_levels.append([datetime.now(), tank_level])
                time.sleep(0.3)
            except Exception, msg:
                print (msg)
                continue

if __name__ == "__main__":

    scada = SCADAServer(
        name='scada',
        state=STATE,
        protocol=SCADA_PROTOCOL,
        memory=SCADA_DATA,
        disk=SCADA_DATA,
        )