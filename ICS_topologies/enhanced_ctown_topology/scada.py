from basePLC import BasePLC
from utils import SCADA_PROTOCOL, STATE
from utils import CTOWN_IPS
from utils import T1, T2, T3, T4, T5, T6, T7, PU1, PU2, PU1F, PU2F, ENIP_LISTEN_PLC_ADDR
from utils import V2, PU3, PU4, PU5, PU6, PU7, PU8, PU9, PU10, PU11
from utils import V2F, PU3F, PU4F, PU5F, PU6F, PU7F, PU8F, PU9F, PU10F, PU11F
from utils import J280, J269, J300, J256, J289, J415, J14, J422, J302, J306, J307, J317, ATT_1, ATT_2

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
        print 'DEBUG SCADA shutdown'
        self.write_output()
        sys.exit(0)

    def pre_loop(self, sleep=0.5):
        """scada pre loop.
            - sleep
        """
        self.saved_tank_levels = [["timestamp", "PU1", "PU2", "PU1F", "PU2F", "J280", "J269", "T1", "T2", "V2", "V2F",
                                   "J300", "J256", "J289", "J415", "J14", "J422", "PU4", "PU5", "PU6", "PU7", "PU4F",
                                   "PU5F", "PU6F", "PU7F", "T3", "PU8", "PU10", "PU11", "PU8F", "PU10F", "PU11F",
                                   "J302", "J306", "J307", "J317", "T4", "T5", "T6", "T7", "PU3", "PU3F", "PU9",
                                   "PU9F",  "Attack#01", "Attack#02"]]

        self.plc1_tags = [PU1, PU2, PU1F, PU2F, J280, J269]
        self.plc2_tags = [T1]
        self.plc3_tags = [T2, V2, V2F, J300, J256, J289, J415, J14, J422, PU4, PU5, PU6, PU7, PU4F, PU5F, PU6F, PU7F]
        self.plc4_tags = [T3]
        self.plc5_tags = [PU8, PU10, PU11, PU8F, PU10F, PU11F, J302, J306, J307, J317]
        self.plc6_tags = [T4]
        self.plc7_tags = [T5]
        self.plc8_tags = [T6]
        self.plc9_tags = [T7]

        self.path = 'scada_values.csv'
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
                plc3_values = self.receive_multiple(self.plc3_tags, CTOWN_IPS['plc3'])
                plc4_values = self.receive_multiple(self.plc4_tags, CTOWN_IPS['plc4'])
                plc5_values = self.receive_multiple(self.plc5_tags, CTOWN_IPS['plc5'])
                plc6_values = self.receive_multiple(self.plc6_tags, CTOWN_IPS['plc6'])
                plc7_values = self.receive_multiple(self.plc7_tags, CTOWN_IPS['plc7'])
                plc8_values = self.receive_multiple(self.plc8_tags, CTOWN_IPS['plc8'])
                plc9_values = self.receive_multiple(self.plc9_tags, CTOWN_IPS['plc9'])

                scada_values = [self.get(PU3), self.get(PU3F), self.get(PU9), self.get(PU9F)]
                att_1 = self.get(ATT_1)
                att_2 = self.get(ATT_2)

                results = [datetime.now()]
                results.extend(plc1_values)
                results.extend(plc2_values)
                results.extend(plc3_values)
                results.extend(plc4_values)
                results.extend(plc5_values)
                results.extend(plc6_values)
                results.extend(plc7_values)
                results.extend(plc8_values)
                results.extend(plc9_values)
                results.extend(scada_values)
                results.extend([att_1, att_2])
                self.saved_tank_levels.append(results)

                time.sleep(2)
            except Exception, msg:
                print(msg)
                continue


if __name__ == "__main__":

    scada = SCADAServer(
        name='scada',
        state=STATE,
        protocol=SCADA_PROTOCOL,
        )
