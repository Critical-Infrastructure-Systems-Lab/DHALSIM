from minicps.devices import PLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import T1, PLC1_SERVER_ADDR
import csv
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
                self.tank_level = Decimal(self.receive(T1, PLC1_SERVER_ADDR))
                print "Received..."
            except Exception:
                time.sleep(0.3)
                continue

            time.sleep(1.0)

if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)
