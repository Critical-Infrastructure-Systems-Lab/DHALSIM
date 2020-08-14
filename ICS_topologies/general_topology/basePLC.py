from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from minicps.devices import PLC
import csv
import signal
import sys


class BasePLC(PLC):

    def set_parameters(self, path, result_list):
        self.result_list = result_list
        self.path = path

    def write_output(self):
        with open('output/' + self.path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.result_list)

    def sigint_handler(self, sig, frame):
        print 'DEBUG plc shutdown'
        self.write_output()
        sys.exit(0)

    def startup(self):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

