from minicps.devices import PLC
from utils import PLC9_DATA, STATE, PLC9_PROTOCOL
from utils import T7, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import signal
import sys
import shlex
import subprocess


plc9_log_path = 'plc9.log'


class PLC9(PLC):

    def sigint_handler(self, sig, frame):
        self.write_output()
        self.move_files()
        sys.exit(0)

    def move_files(self):
        cmd = shlex.split("./copy_output.sh " + str(self.week_index))
        subprocess.call(cmd)

    def write_output(self):
        print 'DEBUG plc9 shutdown'
        with open('output/plc9_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def pre_loop(self):
        print 'DEBUG: plc9 enters pre_loop'
        self.local_time = 0
        self.week_index = sys.argv[1]
        print "Week index in PLC9 is: " + str(self.week_index)
        self.saved_tank_levels = [["iteration", "timestamp", "T7"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):
        get_error_counter = 0
        get_error_counter_limit = 100
        while True:
            try:
                self.t7 = Decimal(self.get(T7))
            except Exception:
                get_error_counter += 1
                if get_error_counter < get_error_counter_limit:
                    continue
                else:
                    print("System database is locked, aborting process")
                    exit(0)

            self.local_time += 1
            self.saved_tank_levels.append([self.local_time, datetime.now(), self.t7])

            print("Tank Level %f " % self.t7)
            print("ITERATION %d ------------- " % self.local_time)
            self.send(T7, self.t7, ENIP_LISTEN_PLC_ADDR)


if __name__ == "__main__":
    plc9 = PLC9(
        name='plc9',
        state=STATE,
        protocol=PLC9_PROTOCOL,
        memory=PLC9_DATA,
        disk=PLC9_DATA)