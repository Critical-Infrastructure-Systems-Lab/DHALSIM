from basePLC import BasePLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL, ENIP_LISTEN_PLC_ADDR
from utils import T1, PU1, PU2, flag_attack_plc1, CTOWN_IPS

import csv
from datetime import datetime
from decimal import Decimal

import time
import signal
import sys
import thread
import threading
from utils import ATT_1, ATT_2

plc1_log_path = 'plc1.log'


class PLC1(BasePLC):

    def send_system_state(self, a, b):
        """
        This method sends the values to the SCADA server or any other client requesting the values
        :param a:
        :param b:
        :return:
        """
        while self.reader:
            tags = [PU1, PU2]
            values = [self.pu1, self.pu2]
            self.send_multiple(tags, values, ENIP_LISTEN_PLC_ADDR)

    def sigint_handler(self, sig, frame):
        self.reader = False
        self.write_output()
        sys.exit(0)

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'

        self.local_time = 0
        # Flag used to stop the thread

        self.reader = True

        self.t1 = Decimal(self.get(T1))

        self.pu1 = int(self.get(PU1))
        self.pu2 = int(self.get(PU1))

        self.saved_tank_levels = [["iteration", "timestamp", "T1"]]
        path = 'plc1_saved_tank_levels_received.csv'

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels)

        # How to call startup, ensuring that we set self.reader?
        #self.startup()

        self.lock = threading.Lock()
        thread.start_new_thread(self.send_system_state,(0,0))

    def main_loop(self):
        while True:
            try:
                self.local_time += 1
                self.t1 = Decimal(self.receive( T1, CTOWN_IPS['plc2'] ))
                #print("ITERATION %d ------------- " % self.local_time)
                #print("Tank 1 Level %f " % self.t1)
                self.saved_tank_levels.append([self.local_time, datetime.now(), self.t1])

                if self.t1 < 4.0:
                    #print("Opening P1")
                    with self.lock:
                        self.pu1 = 1

                if self.t1 > 6.3:
                    #print("Closing P1")
                    with self.lock:
                        self.pu1 = 0

                # This attack keeps PU2 closed
                if flag_attack_plc1 == 1:
                    # Now ATT_2 is set in the physical_process. This in order to make more predictable the attack start and end time
                    attack_on = int(self.get(ATT_2))
                    if attack_on == 1:
                        print("Attack Closing PU2")
                        self.set(ATT_1, 1)
                        with self.lock:
                            self.pu2 = 0
                        time.sleep(0.1)
                        continue

                if self.t1 < 1.0:
                    #print("Opening P2")
                    with self.lock:
                        self.pu2 = 1

                if self.t1 > 4.5:
                    #print("Closing P2")
                    with self.lock:
                        self.pu2 = 0

                with self.lock:
                    self.set(PU1, self.pu1)
                    self.set(PU2, self.pu2)
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