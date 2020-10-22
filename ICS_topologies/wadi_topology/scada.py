from basePLC import BasePLC
from utils import SCADA_PROTOCOL, STATE
from utils import PLC1_ADDR, PLC2_ADDR
from utils import T0, T2, P_RAW1, V_PUB, V_ER2i
from datetime import datetime


class SCADAServer(BasePLC):

    def pre_loop(self, sleep=0.5):
        """scada pre loop.
            - sleep
        """
        self.saved_tank_levels = [["timestamp", "T0", "P_RAW1", "V_PUB", "T2", "V_ER2i"]]
        self.plc1_tags = [T0, P_RAW1, V_PUB]
        self.plc2_tags = [T2, V_ER2i]

        path = 'scada_saved_tank_levels_received.csv'

        isScada = True
        BasePLC.set_parameters(self, path, self.saved_tank_levels, None, None, None, None, None, False, 0, isScada)
        self.startup()


    def main_loop(self):
        """scada main loop."""
        print("DEBUG: scada main loop")
        while True:

            try:
                plc1_values = self.receive_multiple(self.plc1_tags, PLC1_ADDR)
                plc2_values = self.receive_multiple(self.plc2_tags, PLC2_ADDR)
                results = [datetime.now()]
                results.extend(plc1_values)
                results.extend(plc2_values)
                self.saved_tank_levels.append(results)
            except Exception, msg:
                print (msg)
                continue


if __name__ == "__main__":

    scada = SCADAServer(
        name='scada',
        state=STATE,
        protocol=SCADA_PROTOCOL,
        )
