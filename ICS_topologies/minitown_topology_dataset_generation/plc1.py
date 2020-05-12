from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T_LVL, ATT_1, PLC1_ADDR, flag_attack_plc1, flag_attack_plc2, \
    flag_attack_communication_plc1_scada, flag_attack_communication_plc1_plc2, flag_attack_dos_plc2, CONTROL

import csv
from datetime import datetime
from decimal import Decimal

import subprocess
import shlex
import sys
import signal

tank_level=3.0


class PLC1(PLC):

    def sigint_handler(self, sig, frame):
        print "I received a SIGINT!"
        self.write_output()
        self.move_files()
        sys.exit(0)

    def move_files(self):
        cmd = shlex.split("./copy_output.sh " + str(self.output_path))
        subprocess.call(cmd)

    def write_output(self):
        print 'DEBUG plc1 shutdown'
        with open('output/plc1_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'
        self.saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.output_path = sys.argv[1]
        self.local_time = 0

        #non-threading
        self.tank_level = Decimal(self.get(T_LVL))

    def main_loop(self):
        """plc1 main loop.
            - reads sensors value
            - drives actuators according to the control strategy
            - updates its enip server
        """
        fake_values = []
        inject_index = 0
        stop_plc1_attack = False
        while True:
            self.local_time += 1

            #threading
            #global tank_level
            #saved_tank_levels.append([datetime.now(), tank_level])
            #self.send(T_LVL, tank_level, PLC1_ADDR)
            #print("Tank Level %f " % tank_level)

            #non threading
            self.tank_level = Decimal(self.get(T_LVL))

            if flag_attack_plc1:

                # Append measurements to fool the PLC2 that the value is low
                if stop_plc1_attack == False:
                    if self.tank_level < 1.0:
                        fake_values.append( self.tank_level )
                        self.set(ATT_1, 1)

                    if self.local_time >= 382:
                        if inject_index < len(fake_values):
                            self.tank_level = Decimal(1.5)+fake_values[inject_index]*2 + self.tank_level
                            inject_index += 1
                            self.set(ATT_1, 3)
                        if inject_index >= 176:
                            stop_plc1_attack = True
                            self.set(ATT_1, 0)

            self.saved_tank_levels.append([datetime.now(), self.tank_level])
            self.send(T_LVL, self.tank_level, PLC1_ADDR)
            #print("Tank Level %f " % self.tank_level)


if __name__ == "__main__":
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)