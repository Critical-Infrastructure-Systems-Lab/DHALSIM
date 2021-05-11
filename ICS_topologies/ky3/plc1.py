from basePLC import BasePLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL, ENIP_LISTEN_PLC_ADDR
from utils import X_Pump_2
from decimal import Decimal
import time
import threading
from utils import ATT_1, ATT_2, ddos_attack

plc1_log_path = 'plc1.log'


class PLC1(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'

        self.local_time = 0

        # Flag used to stop the thread
        self.reader = True

        self.pu2 = int(self.get(X_Pump_2))
        self.saved_tank_levels = [["iteration", "timestamp", "XPU2"]]
        path = 'plc1_saved_tank_levels_received.csv'
        self.lock = threading.Lock()

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable
        # values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, [X_Pump_2],
                               [self.pu2], self.reader,
                               self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()
    def main_loop(self):
        while True:
            try:
                self.local_time += 1
                attack_on = int(self.get(ATT_2))
                if ddos_attack == 1:
                    if attack_on == 1:
                        self.set(ATT_1, attack_on)
                        self.pu2 = 0
                        print("Closing pump2")

                self.set(X_Pump_2, int(self.pu2))

                time.sleep(0.05)
            except Exception:
                continue

if __name__ == "__main__":
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)