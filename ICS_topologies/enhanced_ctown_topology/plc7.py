from basePLC import BasePLC
from utils import PLC7_DATA, STATE, PLC7_PROTOCOL
from utils import T5, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import signal
import sys

import thread
import threading


plc7_log_path = 'plc7.log'

class PLC7(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc7 enters pre_loop'
        self.local_time = 0
        self.saved_tank_levels = [["iteration", "timestamp", "T5"]]

        # Flag used to stop the thread
        self.reader = True
        self.t5 = Decimal(self.get(T5))

        self.lock = threading.Lock()
        path = 'plc7_saved_tank_levels_received.csv'
        tags = [T5]
        values = [self.t5]

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, tags, values, self.reader, self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def main_loop(self):
        get_error_counter = 0
        get_error_counter_limit = 100
        while True:
            try:
                with self.lock:
                    self.t5 = Decimal(self.get(T5))
            except Exception:
                get_error_counter += 1
                if get_error_counter < get_error_counter_limit:
                    continue
                else:
                    print("PLC process encountered errors, aborting process")
                    exit(0)

            self.local_time += 1
            self.saved_tank_levels.append([self.local_time, datetime.now(), self.t5])

            print("Tank Level %f " % self.t5)
            print("ITERATION %d ------------- " % self.local_time)

if __name__ == "__main__":
    plc7 = PLC7(
        name='plc7',
        state=STATE,
        protocol=PLC7_PROTOCOL,
        memory=PLC7_DATA,
        disk=PLC7_DATA)