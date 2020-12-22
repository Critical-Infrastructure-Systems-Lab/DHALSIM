from basePLC import BasePLC
from utils import PLC4_DATA, STATE, PLC4_PROTOCOL
from utils import T3, ENIP_LISTEN_PLC_ADDR
import logging
from decimal import Decimal
import threading

logging.basicConfig(filename='plc4_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc4_log_path = 'plc4.log'


class PLC4(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc4 enters pre_loop'
        self.local_time = 0
        self.saved_tank_levels = [["iteration", "timestamp", "T3"]]

        # Flag used to stop the thread
        self.reader = True
        self.t3 = Decimal(self.get(T3))

        self.lock = threading.Lock()
        path = 'plc4_saved_tank_levels_received.csv'
        tags = [T3]
        values = [self.t3]

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state
        # variable values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, tags, values, self.reader, self.lock,
                               ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def main_loop(self):
        get_error_counter = 0
        get_error_counter_limit = 100
        print("Starting main loop")
        while True:
            try:
                with self.lock:
                    self.t3 = Decimal(self.get(T3))
            except Exception:
                get_error_counter += 1
                print("Exception!")
                if get_error_counter < get_error_counter_limit:
                    print("Continue!")
                    continue
                else:
                    print("PLC process encountered errors, aborting process")
                    exit(0)

            self.local_time += 1
            get_error_counter = 0

if __name__ == "__main__":
    plc4 = PLC4(
        name='plc4',
        state=STATE,
        protocol=PLC4_PROTOCOL,
        memory=PLC4_DATA,
        disk=PLC4_DATA)