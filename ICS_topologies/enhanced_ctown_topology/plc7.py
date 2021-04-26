from basePLC import BasePLC
from utils import PLC7_DATA, STATE, PLC7_PROTOCOL
from utils import T5, ENIP_LISTEN_PLC_ADDR
from decimal import Decimal
import threading


plc7_log_path = 'plc7.log'


class PLC7(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc7 enters pre_loop'
        self.local_time = 0

        # Flag used to stop the thread
        self.reader = True
        self.t5 = Decimal(self.get(T5))

        self.lock = threading.Lock()
        tags = [T5]
        values = [self.t5]

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable
        # values into a persistent file
        BasePLC.set_parameters(self, tags, values, self.reader, self.lock,
                               ENIP_LISTEN_PLC_ADDR)
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


if __name__ == "__main__":
    plc7 = PLC7(
        name='plc7',
        state=STATE,
        protocol=PLC7_PROTOCOL,
        memory=PLC7_DATA,
        disk=PLC7_DATA)