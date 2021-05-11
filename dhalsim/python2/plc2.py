from basePLC import BasePLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import T2, PLC2_ADDR, V_ER2i
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import signal
import sys
import threading

logging.basicConfig(filename='plc2_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc2_log_path = 'plc2.log'


class PLC2(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc2 enters pre_loop'
        self.local_time = 0

        self.reader = True

        self.t2 = Decimal(self.get(T2))
        self.ver2i = self.get(V_ER2i)

        self.p_raw_delay_timer = 0
        self.timeout_counter = 0

        self.lock = threading.Lock()

        BasePLC.set_parameters(self,  [T2, V_ER2i], [self.t2, self.ver2i], self.reader, self.lock, PLC2_ADDR)
        self.startup()

    def main_loop(self):
        while True:
            try:
                self.local_time += 1
                self.t2 = Decimal(self.get(T2))

                if self.t2 > 0.32:
                    print("Close V_ER2i")
                    self.ver2i = 0

                if self.t2 < 0.16:
                    print("Open V_ER2i")
                    self.ver2i = 1

                self.set(V_ER2i, self.ver2i)
                print("Tank Level 2 %f " % self.t2)
                print("ITERATION %d ------------- " % self.local_time)
                time.sleep(0.1)

            except Exception:
                continue


if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)
