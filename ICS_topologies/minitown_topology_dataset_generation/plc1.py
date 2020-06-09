from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T_LVL, ATT_1, PLC1_ADDR, flag_attack_plc1, flag_concealed_attack_plc1

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

    def launch_plc1_attack(self):
        # Append measurements to fool the PLC2 that the value is low
        if self.stop_plc1_attack == False:
            if self.tank_level < 1.0:
                self.fake_values.append(self.tank_level)
                self.set(ATT_1, 1)

            if self.local_time >= 382:
                if self.inject_index < len(self.fake_values):
                    self.tank_level = Decimal(1.5) + self.fake_values[self.inject_index] * 2 + self.tank_level
                    self.inject_index += 1
                    self.set(ATT_1, 3)
                if self.inject_index >= 176:
                    self.stop_plc1_attack = True
                    self.set(ATT_1, 0)

    def launch_concealed_plc1_attack(self):
        # The attack starts sniffing T_LVL values when the tank reaches its minimum between iteration 150 and 200 of week 9 results
        # Later, when the T_LVL starts to increase between 330 and 400, launches the attack, concealing the T_LVL values with the sniffed ones
        if self.previous_t_lvl <= self.tank_level:
            if 150 > self.local_time > 200:
                self.launch_conceal_sniff_phase()
            if self.local_time > 330:
                if not self.stop_plc1_attack:
                    self.launch_replay_spoof_phase()

    def launch_conceal_sniff_phase(self):
        self.fake_values.append(self.tank_level)

    def launch_replay_spoof_phase(self):
        sniffed_value = self.fake_values[self.inject_index]
        self.saved_tank_levels.append([datetime.now(), sniffed_value])

        # This would not work, because we can't tell if the incoming connection is going to be from SCADA or PLC2!
        self.send(T_LVL, sniffed_value, PLC1_ADDR)
        sniffed_value += 1

    def main_loop(self):
        """plc1 main loop.
            - reads sensors value
            - drives actuators according to the control strategy
            - updates its enip server
        """
        self.fake_values = []
        self.inject_index = 0
        self.stop_plc1_attack = False
        self.previous_t_lvl = 0.0

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
                self.launch_plc1_attack()

            elif flag_concealed_attack_plc1:
                self.launch_concealed_plc1_attack()
            else:
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