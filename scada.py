from basePLC import BasePLC
from utils import *

import time
from datetime import datetime
from decimal import Decimal
import signal
import sys
import csv

class SCADAServer(BasePLC):

    def write_output(self):
        with open('output/' + self.path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def pre_loop(self, sleep=0.5):
        """scada pre loop.
            - sleep
        """
        self.saved_tank_levels = [["timestamp", "T_2", "X_Pump_4"]]
        self.plc1_tags = [X_Pump_4]
        self.plc2_tags = [T_2]

        self.path = 'scada_saved_tank_levels_received.csv'
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):
        """scada main loop."""
        print("DEBUG: scada main loop.")
        while True:

            try:
                #plc1 is in the same LAN as SCADA!
                plc1_values = self.receive_multiple(self.plc1_tags, ENIP_LISTEN_PLC_ADDR)
                plc2_values = self.receive_multiple(self.plc2_tags, CTOWN_IPS['plc2'])
                results = [datetime.now()]
                results.extend(plc1_values)
                results.extend(plc2_values)
                self.saved_tank_levels.append(results)

                time.sleep(0.3)
            except Exception, msg:
                print(msg)
                continue


if __name__ == "__main__":

    scada = SCADAServer(
        name='scada',
        state=STATE,
        protocol=SCADA_PROTOCOL,
        )
