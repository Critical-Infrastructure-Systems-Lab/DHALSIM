from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from topo import SimpleTopo
from initialize_experiment import ExperimentInitializer
import sys
import time
import shlex
import subprocess
import signal
from utils import wadi_ip
from mininet.link import TCLink
import yaml
import glob

automatic = 1


class WADI(MiniCPS):
    """ Main script controlling an experiment
    All the automatic_run.py follow roughly the same pattern by launching subprocesses representing each element in the simulation
    The flag automatic controls if this simulation is run automatically, in which case this process will only finish when the automatic_plant.py finishes.
    automatic_plant will only finish when physical_process.py and in turn that is controlled by the duration parameters configured in the .inp file
    If automatic is 1 and automatic mitm_attack can also be simulated by giving the mitm_attack a flag value of 1
    Every device outputs two files: a .csv file with the values it received during the simulation and a .pcap file with the network messages sent/received during simuilation.
    Those files will be stored into the output/ folder. In addition, output/ will contain a file named by default "physical_process.py" which contains the physical state of the system
    This represents the "ground truth" values of the simulated plant
    """

    def do_forward(self, node):
        # Pre experiment configuration, prepare routing path
        node.cmd('sysctl net.ipv4.ip_forward=1')
        node.waitOutput()

    def add_degault_gateway(self, node, gw_ip):
        node.cmd('route add default gw ' + gw_ip)
        node.waitOutput()

    def setup_network(self):
        r0 = net.get('r0')
        self.do_forward(r0)
        self.add_degault_gateway(net.get('plc1'), '192.168.1.254')
        self.add_degault_gateway(net.get('plc2'), '192.168.1.254')
        self.add_degault_gateway(net.get('attacker_1'), '192.168.1.254')
        self.add_degault_gateway(net.get('scada'), '192.168.2.254')
        self.add_degault_gateway(net.get('attacker_2'), '192.168.2.254')
        r0.cmd('ifconfig r0-eth2 192.168.2.254')
        r0.waitOutput()

    def __init__(self, name, net, week_index, attack_flag, attack_path, attack_name):

        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        print "Running for week: " + str(week_index)
        self.week_index = week_index

        net.start()
        self.setup_network()

        r0 = net.get('r0')
        # Pre experiment configuration, prepare routing path
        r0.cmd('sysctl net.ipv4.ip_forward=1')

        self.attack_flag = attack_flag
        self.attack_path = attack_path
        self.attack_name = attack_name
        self.attack_options = None
        self.attack_type = None
        self.attack_target = None

        if self.attack_flag:
            self.attack_options = self.get_attack_dict(attack_path, attack_name)
            self.attack_type = self.attack_options['type']
            if self.attack_type == "device_attack":
                self.attack_target = self.attack_options['target']

        if automatic:
            self.automatic_start()
        else:
            CLI(net)
        net.stop()

    def get_attack_dict(self, path, name):
        with open(path) as config_file:
            attack_file = yaml.load(config_file, Loader=yaml.FullLoader)

        for attack in attack_file['attacks']:
            if name == attack['name']:
                return attack

    def interrupt(self, sig, frame):
        self.finish()
        sys.exit(0)

    def automatic_start(self):

        plc1 = net.get('plc1')
        plc2 = net.get('plc2')
        scada = net.get('scada')

        self.create_log_files()
        plc1_output = open("output/plc1.log", 'r+')
        plc2_output = open("output/plc2.log", 'r+')
        scada_output = open("output/scada.log", 'r+')

        physical_output = open("output/physical.log", 'r+')

        cmd_string = "python automatic_plc.py -n plc2 -w " + str(self.week_index)
        if self.attack_flag and self.attack_type == "device_attack":
            if "plc2" == self.attack_target:
                cmd_string = "python automatic_plc.py -n plc2 -w " \
                             + str(self.week_index) + " -f " + str(self.attack_flag) + " -p " \
                             + str(self.attack_path) + " -a " + str(self.attack_name)
        print "Launching PLC with command: " + cmd_string
        cmd = shlex.split(cmd_string)
        self.plc2_process = plc2.popen(cmd, stderr=sys.stdout, stdout=plc2_output)
        time.sleep(0.2)

        cmd_string = "python automatic_plc.py -n plc1 -w " + str(self.week_index)
        if self.attack_flag and self.attack_type == "device_attack":
            if "plc1" == self.attack_target:
                cmd_string = "python automatic_plc.py -n plc1 -w " \
                             + str(self.week_index) + " -f " + str(self.attack_flag) + " -p " \
                             + str(self.attack_path) + " -a " + str(self.attack_name)
        print "Launching PLC with command: " + cmd_string
        cmd = shlex.split(cmd_string)
        self.plc1_process = plc1.popen(cmd, stderr=sys.stdout, stdout=plc1_output)
        time.sleep(0.2)

        self.scada_process = scada.popen(sys.executable, "automatic_plc.py", "-n", "scada", stderr=sys.stdout, stdout=scada_output )
        print "[*] Launched the PLCs and SCADA processes"

        # Check and launch network attacks
        if self.attack_flag and self.attack_type == "network_attack":
            attacker_file = open("output/attacker.log", 'r+')
            plc_number = str(self.attack_options['source_plc'])[-1]
            print("Attacker is node: " + 'attacker_1')
            attacker = net.get('attacker_1')
            cmd_string = "../../../attack-experiments/env/bin/python ../../attack_repository/mitm_plc/wadi_mitm_attack.py 192.168.1.20 192.168.1.10 "\
                         + str(self.attack_options['name']) + " "\
                         + str(self.attack_options['values'][0])
            mitm_cmd = shlex.split(cmd_string)
            print 'Running MiTM attack with command ' + str(mitm_cmd)
            self.mitm_process = attacker.popen(mitm_cmd, stderr=sys.stdout, stdout=attacker_file)
            print "[] Attacking"

        # Physical process - WNTR Simulation
        physical_output = open("output/physical.log", 'r+')
        plant = net.get('plant')

        cmd_string = "python automatic_plant.py wadi_config.yaml " + str(self.week_index)

        if self.attack_flag:
            cmd_string = "python automatic_plant.py wadi_config.yaml " + str(self.week_index) + " " + \
                         str(self.attack_path)

        simulation_cmd = shlex.split(cmd_string)
        self.simulation = plant.popen(simulation_cmd, stderr=sys.stdout, stdout=physical_output)

        print "[] Simulating..."
        # We wait until the simulation ends
        while self.simulation.poll() is None:
            pass
        self.finish()

    def create_log_files(self):
        cmd = shlex.split("./create_log_files.sh")
        subprocess.call(cmd)

    def end_process(self, process):
        process.send_signal(signal.SIGINT)
        process.wait()
        if process.poll() is None:
            process.terminate()
        if process.poll() is None:
            process.kill()

    def move_output_files(self, week_index):
        cmd = shlex.split("./copy_output.sh " + str(week_index))
        subprocess.call(cmd)

    def merge_pcap_files(self):
        print "Merging pcap files"
        pcap_files = glob.glob("output/*.pcap")
        separator = ' '
        a_cmd = shlex.split("mergecap -w output/devices.pcap " + separator.join(pcap_files))
        subprocess.call(a_cmd)

    def finish(self):
        print "[*] Simulation finished"

        if self.scada_process:
            self.end_process(self.scada_process)
        if self.plc1_process:
            self.end_process(self.plc1_process)
        if self.plc2_process:
            self.end_process(self.plc2_process)

        if self.simulation.poll() is None:
            self.end_process(self.simulation)
            print "Physical Simulation process terminated"

        self.merge_pcap_files()
        self.move_output_files(self.week_index)

        cmd = shlex.split("./kill_cppo.sh")
        subprocess.call(cmd)

        net.stop()
        sys.exit(0)

if __name__ == "__main__":

    # Here we are deciding if this should be run as Batch or Single mode.
    #
    if len(sys.argv) < 2:

        # This is single mode
        week_index = str(0)
    else:

        # This is batch mode
        week_index = sys.argv[1]

    config_file = "wadi_config.yaml"
    print "Initializing experiment with config file: " + str(config_file)
    initializer = ExperimentInitializer(config_file, week_index)

    complex_topology = initializer.get_complex_topology()
    week_index = initializer.get_week_index()
    simulation_type = initializer.get_simulation_type()
    plc_dict_path = initializer.get_plc_dict_path()

    # check if there is an attack to be run in the experiment
    a_flag = initializer.get_attack_flag()
    if a_flag:
        a_name = initializer.get_attack_name()
        a_path = initializer.get_attack_path()
    else:
        a_name = None
        a_path = None

    topo = SimpleTopo(week_index, simulation_type, config_file, plc_dict_path)
    net = Mininet(topo=topo, autoSetMacs=True, link=TCLink)
    minitown_cps = WADI(name='WADI', net=net, week_index=week_index, attack_flag=a_flag,
                         attack_name=a_name, attack_path=a_path)