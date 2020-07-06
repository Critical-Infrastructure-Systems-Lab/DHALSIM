from minicps.devices import PLC
from utils import PLC7_DATA, STATE, PLC7_PROTOCOL
from utils import T5, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import signal
import sys

logging.basicConfig(filename='plc7_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc7_log_path = 'plc7.log'

class PLC7(PLC):

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def write_output(self):
        print 'DEBUG plc7 shutdown'
        with open('output/plc7_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)
        exit(0)


    def pre_loop(self):
        print 'DEBUG: plc7 enters pre_loop'
        self.local_time = 0
        self.saved_tank_levels = [["iteration", "timestamp", "T5"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):

        while True:
            self.t5 = Decimal(self.get(T5))
            self.local_time += 1
            self.saved_tank_levels.append([self.local_time, datetime.now(), self.t5])

            print("Tank Level %f " % self.t5)
            print("ITERATION %d ------------- " % self.local_time)
            self.send(T5, self.t5, ENIP_LISTEN_PLC_ADDR)

if __name__ == "__main__":
    plc7 = PLC7(
        name='plc7',
        state=STATE,
        protocol=PLC7_PROTOCOL,
        memory=PLC7_DATA,
        disk=PLC7_DATA)