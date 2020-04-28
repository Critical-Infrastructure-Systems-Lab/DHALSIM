from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from topo import ScadaTopo
import sys
import time
import shlex
import subprocess

automatic = 0

class Minitown(MiniCPS):
    """ Script to run the Minitown SCADA topology """

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

        plc1_output = open("plc1.log", 'r+')
        plc2_output = open("plc2.log", 'r+')
        scada_output = open("scada.log", 'r+')

        physical_output = open("physical.log", 'r+')

        plc1_process = plc1.popen(sys.executable, "automatic_plc.py", "-n", "plc1", stderr=sys.stdout, stdout=plc1_output )
        time.sleep(0.1)
        plc2_process = plc2.popen(sys.executable, "automatic_plc.py", "-n", "plc2", stderr=sys.stdout, stdout=plc2_output )
        scada_process = scada.popen(sys.executable, "automatic_plc.py", "-n", "scada", stderr=sys.stdout, stdout=scada_output )

        print "[*] Launched the PLCs and SCADA process, launching simulation..."
        plant = net.get('plant')

        simulation_cmd = shlex.split("python automatic_plant.py -s pdd -t minitown -o physical_process.csv")
        simulation = plant.popen(simulation_cmd, stderr=sys.stdout, stdout=physical_output)

        print "[] Simulating..."

        try:
            while simulation.poll() is None:
                pass
        except KeyboardInterrupt:
            print "Cancelled, finishing simulation"
            self.force_finish(plc1_process, plc2_process, scada_process, simulation)
            return

        self.finish(plc1_process, plc2_process, scada_process)

    def create_log_files(self):
        cmd = shlex.split("./create_log_files.sh")
        subprocess.call(cmd)

    def force_finish(self, plc1, plc2, scada, simulation=None):
        plc1.kill()
        plc2.kill()
        scada.kill()
        simulation.kill()

        cmd = shlex.split("./kill_cppo.sh")
        subprocess.call(cmd)

        net.stop()
        sys.exit(1)

    def finish(self, plc1, plc2, scada, simulation=None):

        #toDo: We have to handle differently the finish process, ideally we want to:
        #   Send a SIGINT signal to the PLCS
        #   Register a signal handler to gracefully handle that signal
        #   If the processes still exist after the SIGINT (they shouldn't) we send a SIGKILL

        print "[*] Simulation finished"
        print "[] Terminating PLC1"
        plc1.terminate()
        print "[*] PLC1 terminated"
        print "[] Terminating PLC2"
        plc2.terminate()
        print "[*] PLC2 terminated"
        print "[] Terminating scada"
        scada.terminate()
        print "[*] All processes terminated"

        # toDo: We have to handle differently for python 3.7 processes, such as simulation
        if simulation:
            simulation.terminate()

        cmd = shlex.split("./kill_cppo.sh")
        subprocess.call(cmd)
        net.stop()
        sys.exit(0)


if __name__ == "__main__":
    topo = ScadaTopo()
    net = Mininet(topo=topo)
    minitown_cps = Minitown(name='minitown', net=net)