from minicps.devices import SCADAServer
from utils import SCADA_PROTOCOL, STATE
from utils import CTOWN_IPS
from utils import T1, T2, T3, T4, T5, T7, PU1, PU2, ENIP_LISTEN_PLC_ADDR
from utils import V2, PU4, PU5, PU6, PU7, PU8, PU10, PU11

import time
import csv
from datetime import datetime
from decimal import Decimal

import signal
import sys


class SCADAServer(SCADAServer):

    def write_output(self):
        print 'DEBUG SCADA shutdown'
        with open('output/scada_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def pre_loop(self, sleep=0.5):
        """scada pre loop.
            - sleep
        """
        self.saved_tank_levels = ["timestamp", "T1", "T2", "T3", "T4", "T5", "T7", "PU1", "PU2", "V2", "PU4", "PU5",
                                   "PU6", "PU7", "PU8", "PU10", "PU11"]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)
        self.plc1_tags = [PU1, PU2]
        self.plc3_tags = [V2, PU4, PU5, PU6, PU7]
        self.plc5_tags = [PU8, PU10, PU11]

    def main_loop(self):
        """scada main loop."""
        print("DEBUG: scada main loop")
        while True:

            try:
                t1 = Decimal(self.receive(T1, CTOWN_IPS['plc2']))
                t2 = Decimal(self.receive(T2, CTOWN_IPS['plc3']))
                t3 = Decimal(self.receive(T3, CTOWN_IPS['plc4']))
                t4 = Decimal(self.receive(T4, CTOWN_IPS['plc6']))
                t5 = Decimal(self.receive(T5, CTOWN_IPS['plc7']))
                t7 = Decimal(self.receive(T7, CTOWN_IPS['plc9']))

                #plc1 is in the same LAN as SCADA!
                plc1_values = self.receive_multiple(self.plc1_tags, ENIP_LISTEN_PLC_ADDR)
                plc3_values = self.receive_multiple(self.plc3_tags, CTOWN_IPS['plc3'])
                plc5_values = self.receive_multiple(self.plc5_tags, CTOWN_IPS['plc35'])

                results = [datetime.now(), t1, t2, t3, t4, t5, t7]
                results.extend(plc1_values)
                results.extend(plc3_values)
                results.extend(plc5_values)
                self.saved_tank_levels.append(results)

                time.sleep(0.3)
            except Exception, msg:
                print (msg)
                continue

if __name__ == "__main__":

    scada = SCADAServer(
        name='scada',
        state=STATE,
        protocol=SCADA_PROTOCOL,
        )