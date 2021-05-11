from basePLC import BasePLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL, ENIP_LISTEN_PLC_ADDR
from utils import X_Pump_4, T_2, CTOWN_IPS
from decimal import Decimal
import time
import threading
from utils import ATT_1, ATT_2, ddos_attack


class PLC2(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'

        self.local_time = 0

        # Flag used to stop the thread
        self.reader = True

        self.pu4 = int(self.get(X_Pump_4))
        self.saved_tank_levels = [["iteration", "timestamp", "XPU4"]]
        path = 'plc2_saved_tank_levels_received.csv'
        self.lock = threading.Lock()

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable
        # values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, [X_Pump_4],
                               [self.pu4], self.reader,
                               self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()
    def main_loop(self):
        while True:
            try:
                self.t2 = Decimal(self.receive(T_2, CTOWN_IPS['plc3']))
                with self.lock:
                    if self.t2 < 152.244:
                        self.pu4 = 1
                    if self.t2 > 167.244:
                        self.pu4 = 0

                attack_on = int(self.get(ATT_2))
                if ddos_attack == 1:
                    if attack_on == 1:
                        self.set(ATT_1, attack_on)
                        self.pu4 = 0
                        print("Closing pump4")

                    self.set(X_Pump_4, int(self.pu4))

                time.sleep(0.05)
            except Exception:
                continue

if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)