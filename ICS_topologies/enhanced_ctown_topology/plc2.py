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
        self.reader = True
        self.saved_tank_levels = [["iteration", "timestamp", "T1"]]
        self.t1 = Decimal(self.get(T1))
        self.lock = threading.Lock()

        path = 'plc2_saved_tank_levels_received.csv'

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, [T1], [self.t1], self.reader, self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def main_loop(self):
        while True:
            time.sleep(0.05)

if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)