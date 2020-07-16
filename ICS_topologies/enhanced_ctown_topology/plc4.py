from minicps.devices import PLC
from utils import PLC4_DATA, STATE, PLC4_PROTOCOL
from utils import T3, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import signal
import sys

logging.basicConfig(filename='plc4_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc4=_log_path = 'plc4.log'

class PLC4(PLC):

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def write_output(self):
        print 'DEBUG plc4 shutdown'
        with open('no_attack/output/plc4_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)
        exit(0)


    def pre_loop(self):
        print 'DEBUG: plc4 enters pre_loop'
        self.local_time = 0
        self.saved_tank_levels = [["iteration", "timestamp", "T3"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)


    def main_loop(self):

        while True:
            self.t3 = Decimal(self.get(T3))
            self.local_time += 1
            self.saved_tank_levels.append([self.local_time, datetime.now(), self.t3])

            print("Tank Level %f " % self.t3)
            print("ITERATION %d ------------- " % self.local_time)
            self.send(T3, self.t3, ENIP_LISTEN_PLC_ADDR)

if __name__ == "__main__":
    plc4 = PLC4(
        name='plc4',
        state=STATE,
        protocol=PLC4_PROTOCOL,
        memory=PLC4_DATA,
        disk=PLC4_DATA)