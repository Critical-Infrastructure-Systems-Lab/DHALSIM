from basePLC import BasePLC
from utils import PLC5_DATA, STATE, PLC5_PROTOCOL
from utils import T5, T7, PU8, PU10, PU11, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS

import csv
from datetime import datetime
from decimal import Decimal
import time
import signal
import sys
import subprocess
import shlex

import thread
import threading


class PLC5(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc5 enters pre_loop'
        self.local_time = 0
        self.saved_tank_levels = [["iteration", "timestamp", "T5", "T7"]]

        # Flag used to stop the thread
        self.reader = True
        self.pu8 = int(self.get(PU8))
        self.pu10 = int(self.get(PU10))
        self.pu11 = int(self.get(PU11))

        self.lock = threading.Lock()
        path = 'plc5_saved_tank_levels_received.csv'
        tags = [PU8, PU10, PU11]
        values = [self.pu8, self.pu10, self.pu11]

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, tags, values, self.reader, self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def main_loop(self):

        while True:
            try:
                self.local_time += 1
                self.t5 = Decimal(self.receive( T5, CTOWN_IPS['plc7'] ))
                self.t7 = Decimal(self.receive( T7, CTOWN_IPS['plc9'] ))
                print("ITERATION %d ------------- " % self.local_time)
                print("T5 Level %f " % self.t5)
                print("T7 Level %f " % self.t7)

                self.saved_tank_levels.append([self.local_time, datetime.now(), self.t5, self.t7])
                with self.lock:
                    if self.t5 < 1.5:
                        print("Opening PU8")
                        self.pu8 = 1

                    if self.t5 > 4.5:
                        print("Closing PU8")
                        self.pu8 = 0

                    if self.t7 < 2.5:
                        print("Opening PU10")
                        self.pu10 = 1

                    if self.t7 > 4.8:
                        print("Closing PU10")
                        self.pu10 = 0

                    if self.t7 < 1.0:
                        print("Opening PU11")
                        self.pu11 = 1

                    if self.t7 > 3.0:
                        print("Closing PU11")
                        self.pu11 = 0

                    self.set(PU8, self.pu8)
                    self.set(PU10, self.pu10)
                    self.set(PU11, self.pu11)

                time.sleep(0.1)

            except Exception:
                print("Connection interrupted at " + str(self.local_time))
                continue

if __name__ == "__main__":
    plc5 = PLC5(
        name='plc5',
        state=STATE,
        protocol=PLC5_PROTOCOL,
        memory=PLC5_DATA,
        disk=PLC5_DATA)