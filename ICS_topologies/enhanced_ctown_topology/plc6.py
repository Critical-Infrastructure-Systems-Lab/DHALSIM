from basePLC import BasePLC
from utils import PLC6_DATA, STATE, PLC6_PROTOCOL
from utils import T4, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import signal
import sys

import thread
import threading

logging.basicConfig(filename='plc6_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc6=_log_path = 'plc6.log'

class PLC6(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc6 enters pre_loop'
        self.local_time = 0
        self.saved_tank_levels = [["iteration", "timestamp", "T4"]]

        # Flag used to stop the thread
        self.reader = True
        self.t4 = Decimal(self.get(T4))

        self.lock = threading.Lock()
        path = 'plc6_saved_tank_levels_received.csv'
        tags = [T4]
        values = [self.t4]

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, tags, values, self.reader, self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def main_loop(self):
        get_error_counter = 0
        get_error_counter_limit = 100
        while True:
            try:
                with self.lock:
                    self.t4 = Decimal(self.get(T4))
            except Exception:
                get_error_counter += 1
                if get_error_counter < get_error_counter_limit:
                    continue
                else:
                    print("PLC process encountered errors, aborting process")
                    exit(0)

            self.local_time += 1
            #self.saved_tank_levels.append([self.local_time, datetime.now(), self.t4])

            print("Tank Level %f " % self.t4)
            print("ITERATION %d ------------- " % self.local_time)

if __name__ == "__main__":
    plc6 = PLC6(
        name='plc6',
        state=STATE,
        protocol=PLC6_PROTOCOL,
        memory=PLC6_DATA,
        disk=PLC6_DATA)