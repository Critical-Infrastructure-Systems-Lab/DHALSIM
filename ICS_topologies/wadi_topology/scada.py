from minicps.devices import SCADAServer
from utils import SCADA_PROTOCOL, STATE
from utils import PLC1_ADDR, PLC2_ADDR
from utils import T0, T2

import time
import csv
from datetime import datetime
from decimal import Decimal

import signal
import sys


class SCADAServer(SCADAServer):

    def write_output(self):
        print 'DEBUG SCADA shutdown'
        with open('output/scada_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def pre_loop(self, sleep=0.5):
        """scada pre loop.
            - sleep
        """
        self.saved_tank_levels = [["iteration", "timestamp", "T0", "T2"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):
        """scada main loop."""
        print("DEBUG: scada main loop")
        while True:

            try:
                t0 = Decimal(self.receive(T0, PLC1_ADDR))
                t2 = Decimal(self.receive(T2, PLC2_ADDR))
                self.saved_tank_levels.append([datetime.now(), t0, t2])
                time.sleep(0.3)
            except Exception, msg:
                print (msg)
                continue

if __name__ == "__main__":

    scada = SCADAServer(
        name='scada',
        state=STATE,
        protocol=SCADA_PROTOCOL,
        )