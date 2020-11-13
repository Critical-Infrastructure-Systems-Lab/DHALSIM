from basePLC import BasePLC
from utils import *
from datetime import datetime
from decimal import Decimal
import time
import threading

class PLC(BasePLC):
    def pre_loop(self):
        print "Pre-loop"

    def main_loop(self):
        print "Main loop"



if __name__ == "__main__":
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)