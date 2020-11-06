from basePLC import BasePLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL, ENIP_LISTEN_PLC_ADDR
from utils import T1, PU1, PU2, flag_attack_plc1, CTOWN_IPS
from datetime import datetime
from decimal import Decimal
import time
import threading
from utils import ATT_1, ATT_2

plc1_log_path = 'plc1.log'


class PLC1(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'

        self.local_time = 0
        # Flag used to stop the thread

        self.reader = True

        self.t1 = Decimal(self.get(T1))
        self.pu1 = int(self.get(PU1))
        self.pu2 = int(self.get(PU2))

        self.saved_tank_levels = [["iteration", "timestamp", "T1"]]
        path = 'plc1_saved_tank_levels_received.csv'
        self.lock = threading.Lock()

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, [PU1, PU2], [self.pu1, self.pu2], self.reader, self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def main_loop(self):
        while True:
            try:
                self.local_time += 1
                attack_on = int(self.get(ATT_2))
                self.set(ATT_1, attack_on)

                self.t1 = Decimal(self.receive( T1, CTOWN_IPS['plc2'] ))

                with self.lock:
                    if self.t1 < 4.0:
                            self.pu1 = 1

                    elif self.t1 > 6.3:
                            self.pu1 = 0

                    if self.t1 < 1.0:
                            self.pu2 = 1

                    elif self.t1 > 4.5:
                            self.pu2 = 0

                    # This attack keeps PU1 - PU2 closed
                    if flag_attack_plc1 == 1:
                        # Now ATT_2 is set in the physical_process. This in order to make more predictable the attack start and end time
                        if attack_on == 1:
                            #self.pu1 = 0
                            #self.pu2 = 0

                            # just for testing the drop in the number of packets
                            self.pu1 = self.pu1
                            self.pu2 = self.pu2

                    self.set(PU1, int(self.pu1))
                    self.set(PU2, int(self.pu2))

                time.sleep(0.1)

            except Exception:
                continue

if __name__ == "__main__":
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)