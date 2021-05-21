from basePLC import BasePLC
import logging
from utils import SCADA_PROTOCOL, STATE
from utils import PLC1_ADDR, PLC2_ADDR
from utils import T0, T2, P_RAW1, V_PUB, V_ER2i
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
        self.logger.debug("SCADA shutdown")
        self.write_output()
        sys.exit(0)

    def pre_loop(self, sleep=0.5):
        """SCADA pre loop.
            - sleep
        """
        self.saved_tank_levels = [["timestamp", "T0", "P_RAW1", "V_PUB", "T2", "V_ER2i"]]
        self.path = 'scada_values.csv'

        self.plc1_tags = [T0, P_RAW1, V_PUB]
        self.plc2_tags = [T2, V_ER2i]

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

    def main_loop(self):
        """scada main loop."""
        self.logger.debug("SCADA main loop")
        while True:

            try:
                plc1_values = self.receive_multiple(self.plc1_tags, PLC1_ADDR)
                plc2_values = self.receive_multiple(self.plc2_tags, PLC2_ADDR)
                results = [datetime.now()]
                results.extend(plc1_values)
                results.extend(plc2_values)
                self.saved_tank_levels.append(results)
            except Exception, msg:
                self.logger.error(msg)
                continue


if __name__ == "__main__":
    scada = SCADAServer(
        name='scada',
        state=STATE,
        protocol=SCADA_PROTOCOL,
    )
