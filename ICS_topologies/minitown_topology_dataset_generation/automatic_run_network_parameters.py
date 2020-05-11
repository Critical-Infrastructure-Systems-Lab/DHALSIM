from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from topo_network_parameters import ScadaTopo
import sys
import time
import shlex
import subprocess
import signal
import argparse
from mininet.link import TCLink

automatic = 0

delay = 0
bandwidth = None
loss = 0
week_index = 0
mode = None

class Minitown(MiniCPS):
    """ Script to run the Minitown SCADA topology """

    def __init__(self, name, net, week_index):
        net.start()

        r0 = net.get('r0')
        # Pre experiment configuration, prepare routing path
        r0.cmd('sysctl net.ipv4.ip_forward=1')

        if automatic:
            self.automatic_start(week_index)
        else:
            CLI(net)
        net.stop()

    def automatic_start(self, week_index) :

        plc1 = net.get('plc1')
        plc2 = net.get('plc2')
        scada = net.get('scada')


        self.week_index = week_index
        self.create_log_files()

        plc1_output = open("output/plc1.log", 'r+')
        plc2_output = open("output/plc2.log", 'r+')
        scada_output = open("output/scada.log", 'r+')

        physical_output = open("output/physical.log", 'r+')

        plc1_process = plc1.popen(sys.executable, "automatic_plc.py", "-n", "plc1", "-w", self.week_index, stderr=sys.stdout, stdout=plc1_output )
        time.sleep(0.2)
        plc2_process = plc2.popen(sys.executable, "automatic_plc.py", "-n", "plc2", "-w", self.week_index, stderr=sys.stdout, stdout=plc2_output )
        scada_process = scada.popen(sys.executable, "automatic_plc.py", "-n", "scada", "-w", self.week_index, stderr=sys.stdout, stdout=scada_output )

        print "[*] Launched the PLCs and SCADA process, launching simulation..."
        plant = net.get('plant')

        simulation_cmd = shlex.split("python automatic_plant.py -s pdd -t minitown -o physical_process.csv -w " + self.week_index)
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
        subprocess.call("./create_log_files.sh")


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
        #   If the processes still exist after the SIGINT (they shouldn't) we send a SIGKILL
        print "[*] Simulation finished"

        print "[] Terminating scada"
        scada.send_signal(signal.SIGINT)
        scada.wait()
        if scada.poll() is None:
            scada.terminate()
        if scada.poll() is None:
            scada.kill()
        print "[*] SCADA terminated"

        print "[] Terminating PLC2"
        plc2.send_signal(signal.SIGINT)
        plc2.wait()
        if plc2.poll() is None:
            plc2.terminate()
        if plc2.poll() is None:
            plc2.kill()
        print "[*] PLC2 terminated"

        print "[] Terminating PLC1"
        plc1.send_signal(signal.SIGINT)
        plc1.wait()
        if plc1.poll() is None:
            plc1.terminate()
        if plc1.poll() is None:
            plc1.kill()
        print "[*] PLC1 terminated"

        cmd = shlex.split("./kill_cppo.sh")
        subprocess.call(cmd)

        print "[*] All processes terminated"
        if simulation:
            simulation.terminate()

        net.stop()
        sys.exit(0)


def process_arguments(arg_parser):

    if arg_parser.mode:
        global mode
        mode = arg_parser.mode
    else:
        global mode
        mode = "free"

    if arg_parser.week:
        global week_index
        week_index = arg_parser.week
    else:
        global week_index
        week_index = 0

    if arg_parser.delay:
        global delay
        delay = arg_parser.delay
    else:
        global delay
        delay = 0

    if arg_parser.loss:
        global loss
        loss = arg_parser.loss
    else:
        global loss
        loss = 0

    if arg_parser.bandwidth:
        global bandwidth
        bandwidth = arg_parser.bandwidth
    else:
        global bandwidth
        bandwidth = None


def get_arguments():
    parser = argparse.ArgumentParser(description='Master Script runs a MiniCPS simulation')
    parser.add_argument("--mode", "-m", help="Type of mode. free means no control over link parameters, control means parameters controlling link between PLC1 and PLC2, in free all the link parameters are ignored")
    parser.add_argument("--week", "-w", help="Week index of the simulation")
    parser.add_argument("--delay", "-d", help="Delay in the link between PLC1 and PLC2. String of the form Xms or Xus")
    parser.add_argument("--loss", "-l", help="Loss Packet Ratio in the link between PLC1 and PLC2, integer of a percentage between 0 and 100 ")
    parser.add_argument("--bandwidth", "-b", help="Bandwidth available in the link between PLC1 and PLC2")
    return parser.parse_args()


if __name__ == "__main__":

    args = get_arguments()
    process_arguments(args)
    topo = ScadaTopo(mode, delay, loss, bandwidth)

    if mode == "free":
        net = Mininet(topo=topo)
    else:
        net = Mininet(topo=topo, link=TCLink)

    minitown_cps = Minitown(name='minitown', net=net, week_index=week_index )