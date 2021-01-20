from basePLC import BasePLC
from utils import PLC8_DATA, STATE, PLC8_PROTOCOL
from utils import T6, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS
from decimal import Decimal
import sys
import threading


class PLC8(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc8 enters pre_loop'
        self.local_time = 0
        self.week_index = sys.argv[2]
        self.week_index = 0
        print "Week index in PLC8 is: " + str(self.week_index)

        # Flag used to stop the thread
        self.reader = True
        self.t6 = Decimal(self.get(T6))

        self.lock = threading.Lock()
        self.saved_tank_levels = [["iteration", "timestamp", "T6"]]
        path = 'plc8_saved_tank_levels_received.csv'
        tags = [T6]
        values = [self.t6]
        lastPLC = True

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable
        # values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, tags, values, self.reader, self.lock,
                               ENIP_LISTEN_PLC_ADDR, lastPLC, self.week_index)
        self.startup()

    def main_loop(self):
        get_error_counter = 0
        get_error_counter_limit = 100
        while True:
            try:
                with self.lock:
                    self.t6 = Decimal(self.get(T6))
            except Exception:
                get_error_counter += 1
                if get_error_counter < get_error_counter_limit:
                    continue
                else:
                    print("System database is locked, aborting process")
                    exit(0)

            self.local_time += 1


if __name__ == "__main__":
    plc8 = PLC8(
        name='plc8',
        state=STATE,
        protocol=PLC8_PROTOCOL,
        memory=PLC8_DATA,
        disk=PLC8_DATA)