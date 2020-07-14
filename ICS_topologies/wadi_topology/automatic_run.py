from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from topo import ScadaTopo
import sys
import time
import shlex
import subprocess
import signal
from utils import wadi_ip


automatic = 1
mitm_attack = 0

class Minitown(MiniCPS):
    """ Script to run the WADI topology """

    def __init__(self, name, net):
        net.start()

        r0 = net.get('r0')
        # Pre experiment configuration, prepare routing path
        r0.cmd('sysctl net.ipv4.ip_forward=1')

        if automatic:
            self.automatic_start()
        else:
            CLI(net)
        net.stop()

    def automatic_start(self):

        plc1 = net.get('plc1')
        plc2 = net.get('plc2')
        scada = net.get('scada')

        self.create_log_files()
        plc1_output = open("output/plc1.log", 'r+')
        plc2_output = open("output/plc2.log", 'r+')
        scada_output = open("output/scada.log", 'r+')

        physical_output = open("output/physical.log", 'r+')

        self.plc2_process = plc2.popen(sys.executable, "automatic_plc.py", "-n", "plc2", stderr=sys.stdout,
                                       stdout=plc2_output)
        time.sleep(0.2)

        self.plc1_process = plc1.popen(sys.executable, "automatic_plc.py", "-n", "plc1", stderr=sys.stdout, stdout=plc1_output )

        # Launching automatically mitm attack
        if mitm_attack == 1 :
            attacker_file = open("output/attacker.log", 'r+')
            attacker = net.get('attacker')
            mitm_cmd = shlex.split("../../../attack-experiments/env/bin/python "
                                   "../../attack_repository/mitm_attacks/wadi_mitm_plc1.py " + wadi_ip['plc2'] + " " + wadi_ip['plc1'])
            print 'Running MiTM attack with command ' + str(mitm_cmd)
            self.mitm_process = attacker.popen(mitm_cmd, stderr=sys.stdout, stdout=attacker_file )
            print "[] Attacking"

        self.scada_process = scada.popen(sys.executable, "automatic_plc.py", "-n", "scada", stderr=sys.stdout, stdout=scada_output )
        print "[*] Launched the PLCs and SCADA process, launching simulation..."
        plant = net.get('plant')

        simulation_cmd = shlex.split("python automatic_plant.py -s pdd -t wadi -o physical_process.csv")
        self.simulation = plant.popen(simulation_cmd, stderr=sys.stdout, stdout=physical_output)

        print "[] Simulating..."
        try:
            while self.simulation.poll() is None:
                pass
        except KeyboardInterrupt:
            print "Cancelled, finishing simulation"
            self.force_finish()
            return

        self.finish()

    def create_log_files(self):
        cmd = shlex.split("./create_log_files.sh")
        subprocess.call(cmd)

    def force_finish(self):
        self.plc1_process.kill()
        self.plc2_process.kill()
        self.scada_process.kill()
        self.simulation.kill()

        cmd = shlex.split("./kill_cppo.sh")
        subprocess.call(cmd)

        net.stop()
        sys.exit(1)

    def end_plc_process(self, plc_process):

        plc_process.send_signal(signal.SIGINT)
        plc_process.wait()
        if plc_process.poll() is None:
            plc_process.terminate()
        if plc_process.poll() is None:
            plc_process.kill()

    def finish(self):
        print "[*] Simulation finished"
        self.end_plc_process(self.scada_process)

        self.end_plc_process(self.plc1_process)
        self.end_plc_process(self.plc2_process)

        if self.simulation:
            self.simulation.terminate()

        cmd = shlex.split("./kill_cppo.sh")
        subprocess.call(cmd)
        net.stop()
        sys.exit(0)

if __name__ == "__main__":
    topo = ScadaTopo()
    net = Mininet(topo=topo)
    minitown_cps = Minitown(name='wadi', net=net)