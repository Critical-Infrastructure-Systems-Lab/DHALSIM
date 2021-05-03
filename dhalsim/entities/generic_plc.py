import argparse
import pickle
from typing import List

from minicps.devices import PLC
import csv
import signal
import sys

import threading
import shlex
import subprocess
import time

from dhalsim.static.plc_config import PlcConfig


class GenericPlc(PLC):

    def __init__(self, plc_configs: List[PlcConfig], index: int):
        self.plc_configs = plc_configs
        self.index = index
        super().__init__(self.plc_configs[self.index].name,
                         self.plc_configs[self.index].protocol, self.plc_configs[self.index].state)

    def send_system_state(self):
        """
        This method sends the values to the SCADA server or any other client requesting the values
        :return:
        """
        values = []
        for tag in self.plc_configs[self.index].tags:
            try:
                values.append(self.get(tag))
            except Exception:
                print("Exception trying to get the tag")
                time.sleep(0.05)
                continue
            values.append(self.get(tag))
        self.send_multiple(self.plc_configs[self.index].tags, values, self.plc_configs[self.index].ip)
        time.sleep(0.05)
    #
    # def write_output(self):
    #     with open('output/' + self.path, 'w') as f:
    #         writer = csv.writer(f)
    #         writer.writerows(self.result_list)
    #
    # def sigint_handler(self, sig, frame):
    #     print('DEBUG plc shutdown')
    #     self.reader = False
    #     self.write_output()
    #     if self.lastPLC:
    #         self.move_files()
    #     sys.exit(0)
    #
    # def move_files(self):
    #     cmd = shlex.split("./scripts/copy_output.sh " + str(self.week_index))
    #     subprocess.call(cmd)
    #
    # def startup(self):
    #     signal.signal(signal.SIGINT, self.sigint_handler)
    #     signal.signal(signal.SIGTERM, self.sigint_handler)
    #
    #     if not self.isScada:
    #         threading.Thread(target=self.send_system_state).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script that represents PLC node in a DHALSIM topology')
    parser.add_argument("--index", "-i", help="Index of the PLC", dest="index", metavar="I", required=True)
    parser.add_argument("--plcconfigs", "-c", help="A pickled list of PlcConfigs", dest="plc_configs", metavar="FILE",
                        required=True)
    args = parser.parse_args()

    plc_configs = pickle.load(open(args.plc_configs, "rb"))

    plc = GenericPlc(plc_configs, args.index)
