import argparse
import pickle
# import csv
# import signal
# import sys
# import threading
# import shlex
# import subprocess
import time
from typing import List

# from minicps.devices import PLC

from dhalsim.static.plc_config import PlcConfig


# todo add minicps import back in (requires adding minicps to gitlab runner for pipeline)

class GenericPlc:
    """
    This code is run when a PLC is started. It will use the plc_config to know what to do.

    :param plc_configs: A list of all the PLC configs
    :type plc_configs: List[class:`dhalsim.static.plc_config.PlcConfig`]
    :param index: This will tell the GenericPlc which of the PLC configs is about this PLC
    :type index: int
    """

    def __init__(self, plc_configs: List[PlcConfig], index: int):
        self.plc_configs = plc_configs
        self.index = index
        self.my_config = self.plc_configs[self.index]
        super().__init__(self.my_config.name,
                         self.my_config.protocol, self.my_config.state)

    def pre_loop(self, sleep=0.5):
        print("entered pre-loop for " + self.my_config.name)

    def send_system_state(self):
        """
        This method sends the values to the SCADA server or any other client requesting the values
        :return:
        """
        values = []
        for tag in self.my_config.tags:
            try:
                values.append(self.get(tag))
            except Exception:
                print("Exception trying to get the tag")
                time.sleep(0.05)
                continue
            values.append(self.get(tag))
        self.send_multiple(self.my_config.tags, values, self.my_config.ip)
        time.sleep(0.05)

    def get_tag(self, tag: str):
        """Placeholder function to get value of sensor

        :param tag: sensor to poll
        :return: value from sensor
        """
        pass

    def set_tag(self, tag: str, action: str):
        """Placeholder function to set value of actuator

        :param tag: actuator to target
        :param action: action to perform
        :return: ???
        """
        pass

    def get_master_clock(self):
        """Gets value of master time (from db?)

        :return:
        """
        pass

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
    parser = argparse.ArgumentParser(
        description='Script that represents PLC node in a DHALSIM topology')
    parser.add_argument("--index", "-i", help="Index of the PLC", dest="index", metavar="I",
                        required=True)
    parser.add_argument("--plcconfigs", "-c", help="A pickled list of PlcConfigs", dest="configs",
                        metavar="FILE",
                        required=True)
    args = parser.parse_args()

    configs = pickle.load(open(args.configs, "rb"))

    plc = GenericPlc(configs, args.index)
