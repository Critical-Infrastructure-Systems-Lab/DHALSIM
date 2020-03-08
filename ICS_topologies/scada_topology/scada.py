from minicps.devices import SCADAServer
from utils import SCADA_PROTOCOL, STATE
from utils import IP, ATT2_ADDR, PLC1_ADDR

import time
import csv
from datetime import datetime

T_LVL = ('T_LVL', 1)

class SCADAServer(SCADAServer):

    def pre_loop(self, sleep=0.5):
        """scada pre loop.
            - sleep
        """
        time.sleep(sleep)


    def main_loop(self):
        """scada main loop."""

        saved_tank_levels = [["timestamp", "TANK_LEVEL"]]
        print("DEBUG: scada main loop")
        while(True):

            try:
                tank_level = float(self.receive(T_LVL, PLC1_ADDR))
                saved_tank_levels.append([datetime.now(), tank_level])
                print " DEBUG PLC2 - receive from plc1 tank level: %f " % tank_level
            except Exception, msg:
                print (msg)
                continue
            except KeyboardInterrupt:
                with open('scada_saved_tank_levels_received.csv', 'w') as f:
                    writer = csv.writer(f)
                    writer.writerows(saved_tank_levels)
                return


        time.sleep(0.3)

if __name__ == "__main__":

    scada = SCADAServer(
        name='scada',
        state=STATE,
        protocol=SCADA_PROTOCOL,
        )