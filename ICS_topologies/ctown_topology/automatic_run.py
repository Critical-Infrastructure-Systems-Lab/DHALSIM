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
mitm_attack = 1

class Minitown(MiniCPS):
    """ Script to run the Minitown SCADA topology """

    def __init__(self, name, net):
        net.start()

        r0 = net.get('r0')
        # Pre experiment configuration, prepare routing path
        r0.cmd('sysctl net.ipv4.ip_forward=1')

        self.sender_plcs =  [2, 4, 6, 7, 9]
        self.receiver_plcs = [1, 3, 5]

        self.sender_plcs_nodes = []
        self.receiver_plcs_nodes = []

        self.sender_plcs_files = []
        self.receiver_plcs_files = []

        self.sender_plcs_processes = []
        self.receiver_plcs_processes = []

        self.attacker = None
        self.attacker_file = None
        self.mitm_process = None

        if automatic:
            self.automatic_start()
        else:
            CLI(net)
        net.stop()

    def automatic_start(self):
        self.create_log_files()

        # Because of our sockets, we gotta launch all the PLCs "sending" variables first
        index = 0
        for plc in self.sender_plcs:
            self.sender_plcs_nodes.append(net.get('plc' + str( self.sender_plcs[index] ) ) )

            self.sender_plcs_files.append( open("output/plc" + str( self.sender_plcs[index]) + ".log", 'r+' ) )
            self.sender_plcs_processes.append( self.sender_plcs_nodes[index].popen(sys.executable, "automatic_plc.py", "-n", "plc" + str(self.sender_plcs[index]), stderr=sys.stdout,
                                                         stdout=self.sender_plcs_files[index]) )
            print("Launched plc" + str(self.sender_plcs[index]))
            index += 1
            time.sleep(0.2)

        # After the servers are done, we can launch the client PLCs
        index = 0
        for plc in self.receiver_plcs:
            self.receiver_plcs_nodes.append(net.get('plc' + str( self.receiver_plcs[index] ) ) )
            self.receiver_plcs_files.append( open("output/plc" + str(self.receiver_plcs[index]) + ".log", 'r+') )
            self.receiver_plcs_processes.append( self.receiver_plcs_nodes[index].popen(sys.executable, "automatic_plc.py", "-n", "plc" + str(self.receiver_plcs[index]), stderr=sys.stdout,
                                                         stdout=self.receiver_plcs_files[index]) )
            print("Launched plc" + str(self.receiver_plcs[index]))
            index += 1

        # Launching automatically mitm attack
        if mitm_attack == 1 :
            attacker_file = open("output/attacker.log", 'r+')
            attacker = net.get('attacker')
            mitm_cmd = shlex.split("/home/mininet/attack-experiments/env/bin/python "
                                   "/home/mininet/WadiTwin/attack_repository/mitm_plc_plc/mitm_attack.py plc5")
            print 'Running MiTM attack with command ' + str(mitm_cmd)
            self.mitm_process = attacker.popen(mitm_cmd, stderr=sys.stdout, stdout=attacker_file )
            print "[] Attacking"

        physical_output = open("output/physical.log", 'r+')
        print "[*] Launched the PLCs and SCADA process, launching simulation..."
        plant = net.get('plant')

        simulation_cmd = shlex.split("python automatic_plant.py -s pdd -t ctown -o physical_process.csv")
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

        for plc in self.receiver_plcs_processes:
            plc.kill()

        for plc in self.sender_plcs_processes:
            plc.kill()

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

        index = 0
        for plc in self.receiver_plcs_processes:
            print "[] Terminating PLC" + str(self.receiver_plcs[index])
            if plc:
                self.end_plc_process(plc)
                print "[*] PLC" + str(self.receiver_plcs[index]) + " terminated"
            index += 1

        index = 0
        for plc in self.sender_plcs_processes:
            print "[] Terminating PLC" + str(self.sender_plcs[index])
            if plc:
                self.end_plc_process(plc)
                print "[*] PLC" + str(self.sender_plcs[index]) + " terminated"
            index += 1

        if self.mitm_process:
            self.end_plc_process(self.mitm_process)
        print "[*] All processes terminated"

        if self.simulation:
            self.simulation.terminate()

        cmd = shlex.split("./kill_cppo.sh")
        subprocess.call(cmd)
        net.stop()
        sys.exit(0)

if __name__ == "__main__":
    topo = ScadaTopo()
    net = Mininet(topo=topo)
    minitown_cps = Minitown(name='minitown', net=net)