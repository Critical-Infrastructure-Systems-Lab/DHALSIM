from basePLC import BasePLC
from utils import PLC3_DATA, STATE, PLC3_PROTOCOL
from utils import T_2, ENIP_LISTEN_PLC_ADDR
from decimal import Decimal
import time
import threading

class PLC3(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc3 enters pre_loop'
        self.local_time = 0

        # Flag used to stop the thread
        self.reader = True
        self.saved_tank_levels = [["iteration", "timestamp", "T_2"]]
        self.t2 = Decimal(self.get(T_2))
        self.lock = threading.Lock()

        path = 'plc3_saved_tank_levels_received.csv'

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable
        # values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, [T_2], [self.t2], self.reader, self.lock,
                               ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def main_loop(self):
        while True:
            time.sleep(0.05)


if __name__ == "__main__":
    plc3 = PLC3(
        name='plc3',
        state=STATE,
        protocol=PLC3_PROTOCOL,
        memory=PLC3_DATA,
        disk=PLC3_DATA)