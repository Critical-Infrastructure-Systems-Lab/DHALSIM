from basePLC import BasePLC
from utils import PLC5_DATA, STATE, PLC5_PROTOCOL, CONTROL
from utils import T5, T7, PU8, PU10, PU11, PU8F, PU10F, PU11F, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS
from utils import J302, J306, J307, J317
from decimal import Decimal
import time
import threading


class PLC5(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc5 enters pre_loop'
        self.local_time = 0

        # Used to sync the actuators and the physical process
        self.plc_mask = 4

        # Flag used to stop the thread
        self.reader = True
        self.pu8 = int(self.get(PU8))
        self.pu10 = int(self.get(PU10))
        self.pu11 = int(self.get(PU11))

        self.pu8f = Decimal(self.get(PU8F))
        self.pu10f = Decimal(self.get(PU10F))
        self.pu11f = Decimal(self.get(PU11F))

        self.j302 = Decimal(self.get(J302))
        self.j306 = Decimal(self.get(J306))
        self.j307 = Decimal(self.get(J307))
        self.j317 = Decimal(self.get(J317))

        self.lock = threading.Lock()
        tags = [PU8, PU10, PU11, PU8F, PU10F, PU11F, J302, J306, J307, J317]
        values = [self.pu8, self.pu10, self.pu11, self.pu8f, self.pu10f, self.pu11f, self.j302, self.j306, self.j307,
                  self.j317]

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable
        # values into a persistent file
        BasePLC.set_parameters(self, tags, values, self.reader, self.lock,
                               ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def check_control(self, mask):
        control = int(self.get(CONTROL))
        if not (mask & control):
            return True
        return False

    def main_loop(self):

        while True:
            try:
                self.local_time += 1
                self.t5 = Decimal(self.receive(T5, CTOWN_IPS['plc7']))
                self.t7 = Decimal(self.receive(T7, CTOWN_IPS['plc9']))

                with self.lock:
                    if self.t5 < 1.5:
                        self.pu8 = 1

                    if self.t5 > 4.5:
                        self.pu8 = 0

                    if self.t7 < 2.5:
                        self.pu10 = 1

                    if self.t7 > 4.8:
                        self.pu10 = 0

                    if self.t7 < 1.0:
                        self.pu11 = 1

                    if self.t7 > 3.0:
                        self.pu11 = 0

                    self.set(PU8, self.pu8)
                    self.set(PU10, self.pu10)
                    self.set(PU11, self.pu11)

                control = int(self.get(CONTROL))
                control += self.plc_mask
                self.set(CONTROL, control)
                time.sleep(0.05)
                #else:
                #    time.sleep(0.1)
            except Exception:
                print("Connection interrupted at " + str(self.local_time))
                continue

if __name__ == "__main__":
    plc5 = PLC5(
        name='plc5',
        state=STATE,
        protocol=PLC5_PROTOCOL,
        memory=PLC5_DATA,
        disk=PLC5_DATA)