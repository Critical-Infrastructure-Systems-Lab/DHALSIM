from basePLC import BasePLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import T1, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import signal
import sys

import thread
import threading

plc2_log_path = 'plc2.log'


class PLC2(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc2 enters pre_loop'
        self.local_time = 0

        # Flag used to stop the thread
        reader = True

        self.saved_tank_levels = [["iteration", "timestamp", "T1"]]
        t1 = Decimal(self.get(T1))
        self.lock = threading.Lock()

        path = 'plc2_saved_tank_levels_received.csv'

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, [T1], [t1], reader, self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def main_loop(self):
        get_error_counter = 0
        get_error_counter_limit = 100
        while True:
            try:
                with self.lock:
                    self.t1 = Decimal(self.get(T1))
            except Exception:
                get_error_counter += 1
                if get_error_counter < get_error_counter_limit:
                    continue
                else:
                    print("PLC process encountered errors, aborting process")
                    exit(0)
            self.local_time += 1
            #self.saved_tank_levels.append([self.local_time, datetime.now(), self.t1])
            get_error_counter = 0

if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)