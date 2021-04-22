from basePLC import BasePLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL, ENIP_LISTEN_PLC_ADDR, CONTROL
from utils import T1, PU1, PU2, PU1F, PU2F, CTOWN_IPS, J280, J269
from decimal import Decimal
import time
import threading
from utils import ATT_1, ATT_2
import argparse
import sys
import yaml

plc1_log_path = 'plc1.log'


class PLC1(BasePLC):

    def pre_loop(self):
        print 'DEBUG: plc1 enters pre_loop'

        # We wish we could implement this as arg_parse, but we cannot overwrite the constructor
        self.week_index = sys.argv[2]
        self.attack_flag = False
        self.attack_dict = None

        if len(sys.argv) >= 4:
            self.attack_flag = sys.argv[4]
            self.attack_path = sys.argv[6]
            self.attack_name = sys.argv[8]

        if self.attack_flag:
            self.attack_dict = self.get_attack_dict(self.attack_path, self.attack_name)
            print "PLC1 running attack: " + str(self.attack_dict)

        self.local_time = 0

        # Used to sync the actuators and the physical process
        self.plc_mask = 1

        # Flag used to stop the thread
        self.reader = True

        self.t1 = Decimal(self.get(T1))
        self.pu1 = int(self.get(PU1))
        self.pu2 = int(self.get(PU2))
        self.pu1f = Decimal(self.get(PU1F))
        self.pu2f = Decimal(self.get(PU2F))

        self.j280 = Decimal(self.get(J280))
        self.j269 = Decimal(self.get(J269))

        self.saved_tank_levels = [["iteration", "timestamp", "T1"]]
        path = 'plc1_saved_tank_levels_received.csv'
        self.lock = threading.Lock()

        # Used in handling of sigint and sigterm signals, also sets the parameters to save the system state variable
        # values into a persistent file
        BasePLC.set_parameters(self, path, self.saved_tank_levels, [PU1, PU2, PU1F, PU2F, J280, J269],
                               [self.pu1, self.pu2, self.pu1f, self.pu2f, self.j280, self.j269], self.reader,
                               self.lock, ENIP_LISTEN_PLC_ADDR)
        self.startup()

    def get_attack_dict(self, path, name):
        with open(path) as config_file:
            attack_file = yaml.load(config_file, Loader=yaml.FullLoader)

        for attack in attack_file['attacks']:
            if name == attack['name']:
                return attack

    def check_control(self, mask):
        control = int(self.get(CONTROL))
        if not (mask & control):
            return True
        return False

    def main_loop(self):
        while True:
            try:
                if self.check_control(self.plc_mask):
                    self.local_time += 1

                    # Reads from the DB
                    attack_on = int(self.get(ATT_2))
                    self.set(ATT_1, attack_on)

                    self.t1 = Decimal(self.receive(T1, CTOWN_IPS['plc2']))
                    with self.lock:
                        if self.t1 < 4.0:
                            self.pu1 = 1

                        elif self.t1 > 6.3:
                            self.pu1 = 0

                        if self.t1 < 1.0:
                            self.pu2 = 1

                        elif self.t1 > 4.5:
                            self.pu2 = 0

                        # This is configured in the yaml file
                        if self.attack_flag:
                            # Now ATT_2 is set in the physical_process. This in order to make more predictable the
                            # attack start and end time. This ATT_2 is read from the DB
                            if attack_on == 1:
                                if self.attack_dict['command'] == 'Close':
                                    # toDo: Implement this dynamically.
                                    # There's a horrible way of doing it with the current code. This would be much
                                    # easier (and less horrible) if we use the general topology

                                    # pu1 and pu2 should not be hardcoded
                                    # This object should have a list of actuators
                                    self.pu1 = 0
                                    self.pu2 = 0
                                elif self.attack_dict['command'] == 'Open':
                                    self.pu1 = 1
                                    self.pu2 = 1
                                elif self.attack_dict['command'] == 'Maintain':
                                    continue
                                elif self.attack_dict['command'] == 'Toggle':
                                    if self.pu1 == 1:
                                        self.pu1 = 0
                                    else:
                                        self.pu1 = 1

                                    if self.pu2 == 1:
                                        self.pu2 = 0
                                    else:
                                        self.pu2 = 1
                                else:
                                    print "Warning. Attack not implemented yet"

                        # Writes into the DB
                        self.set(PU1, int(self.pu1))
                        self.set(PU2, int(self.pu2))

                    control = int(self.get(CONTROL))
                    control += self.plc_mask
                    self.set(CONTROL, control)
                    time.sleep(0.05)
                else:
                    time.sleep(0.01)
            except Exception:
                continue


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Script that represents PLC/SCADA node in a DHALSIM topology')
    parser.add_argument("--week", "-w", help="Week index in case demand customization flag is enabled")
    parser.add_argument("--attack_flag", "-f", help="Flag to indicate if this PLC needs to run an attack")
    parser.add_argument("--attack_path", "-p", help="Path to the attack repository")
    parser.add_argument("--attack_name", "-a", help="Name of the attack to be run by this PLC")

    args = parser.parse_args()

    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)