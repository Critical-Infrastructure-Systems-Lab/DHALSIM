from basePLC import BasePLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T_LVL, ATT_1, PLC1_ADDR, flag_attack_plc1, flag_attack_plc2, \
    flag_attack_communication_plc1_scada, flag_attack_communication_plc1_plc2, flag_attack_dos_plc2, CONTROL
from datetime import datetime
from decimal import Decimal


class PLC(BasePLC):
    def pre_loop(self):
        print "Calling basePLC init"
        self.saved_tank_levels = [["timestamp", "TANK_LEVEL"]]
        path = 'plc1_saved_tank_levels_received.csv'
        BasePLC.set_parameters(self, path, self.saved_tank_levels)
        self.startup()
        print 'DEBUG: plc1 enters pre_loop'
        self.reader = True
        self.local_time = 0
        self.tank_level = Decimal(self.get(T_LVL))

    def main_loop(self):
        """plc1 main loop.
            - reads sensors value
            - drives actuators according to the control strategy
            - updates its enip server
        """
        fake_values = []
        while True:
            control = int(self.get(CONTROL))
            if control == 0:
                self.local_time += 1
                self.tank_level = Decimal(self.get(T_LVL))
                self.saved_tank_levels.append([datetime.now(), self.tank_level])
                self.send(T_LVL, self.tank_level, PLC1_ADDR)

                if flag_attack_plc1:
                    if self.local_time in range(100, 200):
                        fake_values.append(self.tank_level)
                        self.set(ATT_1, 1)
                    elif self.local_time in range(250, 350):
                        self.set(ATT_1, 2)
                        self.tank_level = fake_values[self.local_time]
                        self.local_time += 1
                    else:
                        if flag_attack_plc2 == 0 and flag_attack_communication_plc1_scada == 0 and flag_attack_communication_plc1_plc2 == 0 and flag_attack_dos_plc2 == 0:
                            self.set(ATT_1, 0)


if __name__ == "__main__":
    plc1 = PLC(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)