from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from topo import ScadaTopo
import sys
import time
import shlex
import subprocess
import signal

automatic = 1
concealed_mitm = 0

class Minitown(MiniCPS):
    """ Main script controlling an experiment
    All the automatic_run.py follow roughly the same pattern by launching subprocesses representing each element in the simulation
    The flag automatic controls if this simulation is run automatically, in which case this process will only finish when the automatic_plant.py finishes.
    automatic_plant will only finish when physical_process.py and in turn that is controlled by the duration parameters configured in the .inp file
    If automatic is 1 and automatic mitm_attack can also be simulated by giving the mitm_attack a flag value of 1
    Every device outputs two files: a .csv file with the values it received during the simulation and a .pcap file with the network messages sent/received during simuilation.
    Those files will be stored into the output/ folder. In addition, output/ will contain a file named by default "physical_process.py" which contains the physical state of the system
    This represents the "ground truth" values of the simulated plant
    """

    def __init__(self, name, net):

        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        self.plc2_mitm_process = None
        self.scada_mitm_process = None

        net.start()

        r0 = net.get('r0')
        # Pre experiment configuration, prepare routing path
        r0.cmd('sysctl net.ipv4.ip_forward=1')

        if automatic:
            self.automatic_start()
        else:
            CLI(net)
        net.stop()

    def interrupt(self, sig, frame):
        self.finish()
        sys.exit(0)

    def automatic_start(self):

        plc1 = net.get('plc1')
        plc2 = net.get('plc2')
        scada = net.get('scada')

        if len(sys.argv) < 2:
            self.week_index = str(0)
        else:
            self.week_index = sys.argv[1]

        self.create_log_files()

        plc1_output = open("output/plc1.log", 'r+')
        plc2_output = open("output/plc2.log", 'r+')
        scada_output = open("output/scada.log", 'r+')

        physical_output = open("output/physical.log", 'r+')

        self.plc1_process = plc1.popen(sys.executable, "automatic_plc.py", "-n", "plc1", "-w", self.week_index, stderr=sys.stdout, stdout=plc1_output )
        time.sleep(0.2)
        self.plc2_process = plc2.popen(sys.executable, "automatic_plc.py", "-n", "plc2", "-w", self.week_index, stderr=sys.stdout, stdout=plc2_output )
        self.scada_process = scada.popen(sys.executable, "automatic_plc.py", "-n", "scada", "-w", self.week_index, stderr=sys.stdout, stdout=scada_output )

        if concealed_mitm == 1:
            plc2_attacker_file = open("output/attacker_plc2.log", 'r+')
            plc2_attacker = net.get('attacker')
            mitm_cmd = shlex.split("../../../attack-experiments/env/bin/python "
                                   "../../attack_repository/mitm_attacks/minitown_mitm_plc2.py")
            print 'Running MiTM attack with command ' + str(mitm_cmd)
            self.plc2_mitm_process = plc2_attacker.popen(mitm_cmd, stderr=sys.stdout, stdout=plc2_attacker_file )
            print "[] Launching MiTM on PLC2"

            scada_attacker_file = open("output/attacker_scada.log", 'r+')
            scada_attacker = net.get('attacker2')
            mitm_cmd = shlex.split("../../../attack-experiments/env/bin/python "
                                   "../../attack_repository/mitm_attacks/minitown_mitm_scada.py")
            print 'Running MiTM attack with command ' + str(mitm_cmd)
            self.scada_mitm_process = scada_attacker.popen(mitm_cmd, stderr=sys.stdout, stdout=scada_attacker_file )
            print "[] Launching MiTM on PLC2"


        print "[*] Launched the PLCs and SCADA process, launching simulation..."
        plant = net.get('plant')

        simulation_cmd = shlex.split("python automatic_plant.py -s pdd -t minitown -o physical_process.csv -w " + self.week_index)
        self.simulation = plant.popen(simulation_cmd, stderr=sys.stdout, stdout=physical_output)

        print "[] Simulating..."
        while self.simulation.poll() is None:
            pass
        self.finish()

    def create_log_files(self):
        subprocess.call("./create_log_files.sh")

    def end_process(self, process):
        process.send_signal(signal.SIGINT)
        process.wait()
        if process.poll() is None:
            process.terminate()
        if process.poll() is None:
            process.kill()

    def finish(self):

        print "[*] Simulation finished"
        self.end_process(self.scada_process)
        self.end_process(self.plc2_process)
        self.end_process(self.plc1_process)

        if self.plc2_mitm_process:
            self.end_process(self.plc2_mitm_process)

        if self.scada_mitm_process:
            self.end_process(self.scada_mitm_process)

        if self.simulation:
            self.simulation.terminate()

        cmd = shlex.split("./kill_cppo.sh")
        subprocess.call(cmd)

        net.stop()
        sys.exit(0)

if __name__ == "__main__":

    topo = ScadaTopo()
    net = Mininet( topo=topo, autoSetMacs=True )
    minitown_cps = Minitown( name='minitown', net=net )