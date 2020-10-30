from basePLC import BasePLC
from utils import PLC3_DATA, STATE, PLC3_PROTOCOL
from utils import T2, T3, T4, V2, PU4, PU5, PU6, PU7, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS

import csv
from datetime import datetime
from decimal import Decimal
import time
import signal
import sys

import thread
import threading

class PLC3(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc3 enters pre_loop'
        self.local_time = 0

        # Flag used to stop the thread
        self.reader = True
        self.saved_tank_levels = [["iteration", "timestamp", "T2", "T3", "T4"]]

        self.t2 = Decimal(self.get(T2))
        self.v2 = int(self.get(V2))
        self.pu4 = int(self.get(PU4))
        self.pu5 = int(self.get(PU5))
        self.pu6 = int(self.get(PU6))
        self.pu7 = int(self.get(PU7))

        self.lock = threading.Lock()
        path = 'plc3_saved_tank_levels_received.csv'
        tags = [V2, PU4, PU5, PU6, PU7]
        values = [self.v2, self.pu4, self.pu5, self.pu6, self.pu7]

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, tags, values, self.reader, self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def main_loop(self):
        while True:
            try:
                self.local_time += 1
                self.t2 = Decimal( self.get( T2 ) )
                self.t3 = Decimal(self.receive( T3, CTOWN_IPS['plc4'] ))
                self.t4 = Decimal(self.receive( T4, CTOWN_IPS['plc6'] ))

                self.saved_tank_levels.append([self.local_time, datetime.now(), self.t2, self.t3, self.t4])
                with self.lock:
                    if self.t2 < 0.5:
                        self.v2 = 1

                    if self.t2 > 5.5:
                        self.v2 = 0

                    if self.t3 < 3.0:
                        self.pu4 = 1

                    if self.t3 > 5.3:
                        self.pu4 = 0

                    if self.t3 < 1.0:
                        self.pu5 = 1

                    if self.t3 > 3.5:
                        self.pu5 = 0

                    if self.t4 < 2.0:
                        self.pu6 = 1

                    if self.t4 > 3.5:
                        self.pu6 = 0

                    if self.t4 < 3.0:
                        self.pu7 = 1

                    if self.t4 > 4.5:
                        self.pu7 = 0

                    self.set(V2, self.v2)
                    self.set(PU4, self.pu4)
                    self.set(PU5, self.pu5)
                    self.set(PU6, self.pu6)
                    self.set(PU7, self.pu7)

                time.sleep(0.1)

            except Exception:
                continue

if __name__ == "__main__":
    plc3 = PLC3(
        name='plc3',
        state=STATE,
        protocol=PLC3_PROTOCOL,
        memory=PLC3_DATA,
        disk=PLC3_DATA)