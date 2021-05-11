from basePLC import BasePLC
# from utils import SCADA_PROTOCOL, STATE
# from utils import PLC1_ADDR, PLC2_ADDR
# from utils import T0, T2, P_RAW1, V_PUB, V_ER2i
from datetime import datetime
import signal
import csv
import sys

class SCADAServer(BasePLC):

    def write_output(self):
        with open('output/' + self.path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def sigint_handler(self, sig, frame):
        print('DEBUG SCADA shutdown')
        self.write_output()
        sys.exit(0)

    def pre_loop(self, sleep=0.5):
        """scada pre loop.
            - sleep
        """
        print('DEBUG: scada pre loop...')
        # self.saved_tank_levels = [["timestamp", "T0", "P_RAW1", "V_PUB", "T2", "V_ER2i"]]
        # self.path = 'scada_values.csv'
        #
        # self.plc1_tags = [T0, P_RAW1, V_PUB]
        # self.plc2_tags = [T2, V_ER2i]
        #
        # signal.signal(signal.SIGINT, self.sigint_handler)
        # signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):
        """scada main loop."""
        print("DEBUG: scada main loop...")
        while True:
            continue
        # while True:
        #
        #     try:
        #         plc1_values = self.receive_multiple(self.plc1_tags, PLC1_ADDR)
        #         plc2_values = self.receive_multiple(self.plc2_tags, PLC2_ADDR)
        #         results = [datetime.now()]
        #         results.extend(plc1_values)
        #         results.extend(plc2_values)
        #         self.saved_tank_levels.append(results)
        #     except Exception, msg:
        #         print(msg)
        #         continue


if __name__ == "__main__":
    STATE = {
        'name': 'wadi',
        'path': '/home/robert/dhalsim/examples/wadi_topology/wadi_map.cpa'
    }
    SCADA_TAGS = (
        ('X_Pump_1', 1, 'REAL'),
        ('X_Pump_2', 1, 'REAL'),
        ('X_Pump_3', 1, 'REAL'),
        ('X_Pump_4', 1, 'REAL'),
        ('X_Pump_5', 1, 'REAL'),
        ('T_1', 1, 'REAL'),
        ('T_2', 1, 'REAL'),
        ('T_3', 1, 'REAL'),
    )
    SCADA_SERVER = {
        'address': '192.168.2.1',
        'tags': SCADA_TAGS
    }
    SCADA_PROTOCOL = {
        'name': 'enip',
        'mode': 1,
        'server': SCADA_SERVER
    }

    scada = SCADAServer(
        name='scada',
        state=STATE,
        protocol=SCADA_PROTOCOL,
        )