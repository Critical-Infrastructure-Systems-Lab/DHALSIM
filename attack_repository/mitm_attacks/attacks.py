import subprocess
import shlex
import argparse
import sys

class Attacks():
    def launch_attack(self, attack_script):
        print 'Running attack...'
        mitm = subprocess.Popen(["../../../attack-experiments/env/bin/python", attack_script])
        return mitm

    def main(self):
        args = self.get_arguments()
        self.process_arguments(args)

        if self.attack == "mitm" and self.target == "plc2":
            print "Launching MiTM attack on PLC2"
            attack_process = self.launch_attack('minitown_mitm_plc2.py')
            print "Launced MiTM attack on PLC2"
            attack_process.wait()
            print "Attack finished"

        if self.attack == "mitm" and self.target == "scada":
            print "Launching MiTM attack on SCADA"
            attack_process = self.launch_attack('minitown_mitm_scada.py')
            print "Launced MiTM attack on SCADA"
            attack_process.wait()
            print "Attack finished"

        else:
            print 'No attack was specified, exiting...'
            sys.exit(1)

    def process_arguments(self,arg_parser):
        if arg_parser.attack:
            self.attack = arg_parser.attack
        else:
            self.attack = 'mitm'

        if arg_parser.target:
            self.target = arg_parser.target
        else:
            self.target = 'plc2'

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script that launches LAN communication attacks')
        parser.add_argument("--attack", "-a",help="Attack to be launched")
        parser.add_argument("--target", "-t", help="target of the attack")
        return parser.parse_args()

if __name__ == "__main__":
    mitm = Attacks()
    mitm.main()