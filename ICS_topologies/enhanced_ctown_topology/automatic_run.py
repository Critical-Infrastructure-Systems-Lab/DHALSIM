from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from topo import CTownTopo
from initialize_experiment import ExperimentInitializer
import sys
import time
import shlex
import subprocess
import signal
from mininet.link import TCLink
import glob

automatic = 1
mitm_attack = 0
iperf_test = 0

class CTown(MiniCPS):
    """ Main script controlling an experiment
    All the automatic_run.py follow roughly the same pattern by launching subprocesses representing each element in the simulation
    The flag automatic controls if this simulation is run automatically, in which case this process will only finish when the automatic_plant.py finishes.
    automatic_plant will only finish when physical_process.py and in turn that is controlled by the duration parameters configured in the .inp file
    If automatic is 1 and automatic mitm_attack can also be simulated by giving the mitm_attack a flag value of 1
    Every device outputs two files: a .csv file with the values it received during the simulation and a .pcap file with the network messages sent/received during simuilation.
    Those files will be stored into the output/ folder. In addition, output/ will contain a file named by default "physical_process.py" which contains the physical state of the system
    This represents the "ground truth" values of the simulated plant
    """
    def setup_iptables(self, node_name):
        a_node = net.get(node_name)
        a_node.cmd('bash ./ctown_nat.sh ' + node_name)
        a_node.waitOutput()
        a_node.cmd('bash ./port_forward.sh ' + node_name)
        a_node.waitOutput()

    def do_forward(self, node):
        # Pre experiment configuration, prepare routing path
        node.cmd('sysctl net.ipv4.ip_forward=1')
        node.waitOutput()

    def add_degault_gateway(self, node, gw_ip):
        node.cmd('route add default gw ' + gw_ip)
        node.waitOutput()

    # This method exists, because using TCLinks mininet ignores the ip parameter of some interfaces. We use TCLinks to support bw and delay configurations on interfaces
    def configure_routers_interface(self, index):
        a_router = net.get('r' + index)
        a_router.cmd('ifconfig r' + index + '-eth1 192.168.1.254')
        a_router.waitOutput()

    # This method exists, because using TCLinks mininet ignores the ip parameter of some interfaces. We use TCLinks to support bw and delay configurations on interfaces
    def configure_r0_interfaces(self, index):
        router0 = net.get('r0')
        router0.cmd('ifconfig r0-eth' + str(index) + ' 10.0.' + str(index+1) + '.254 netmask 255.255.255.0' )

    def setup_network(self):
        for i in range(0, 9):
            self.do_forward(net.get('r' + str(i)))
            self.configure_routers_interface(str(i+1))
            self.configure_r0_interfaces(i+1)
            self.add_degault_gateway(net.get('plc' + str(i+1)), '192.168.1.254')
            self.add_degault_gateway(net.get('r' + str(i+1)), '10.0.' + str(i+1) + '.254')
        for i in range(1, 10):
            self.setup_iptables('r' + str(i))

        self.add_degault_gateway(net.get('scada'), '192.168.1.254')
        self.add_degault_gateway(net.get('attacker'), '192.168.1.254')
        self.add_degault_gateway(net.get('client'), '192.168.1.254')
        self.add_degault_gateway(net.get('server'), '192.168.1.254')
        self.do_forward(net.get('attacker'))

    def __init__(self, name, net, week_index):
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        print "Running for week: " + str(week_index)
        self.week_index = week_index

        net.start()
        self.setup_network()

        self.sender_plcs = [2, 4, 6, 7, 8, 9]
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
        self.iperf_server_process = None
        self.iperf_client_process = None

        if automatic:
            self.automatic_start()
        else:
            CLI(net)
        net.stop()

    def interrupt(self, sig, frame):
        self.finish()
        sys.exit(0)

    def automatic_start(self):
        self.create_log_files()

        # Because of our sockets, we gotta launch all the PLCs "sending" variables first
        index = 0
        for plc in self.sender_plcs:
            self.sender_plcs_nodes.append(net.get('plc' + str(self.sender_plcs[index])))
            self.sender_plcs_files.append(open("output/plc" + str(self.sender_plcs[index]) + ".log", 'r+'))
            cmd_string = "python automatic_plc.py -n plc" + str(self.sender_plcs[index]) + " -w " + str(self.week_index)
            print "Launching PLC with command: " + cmd_string
            cmd = shlex.split(cmd_string)
            self.sender_plcs_processes.append(self.sender_plcs_nodes[index].popen(cmd,stderr=sys.stdout,
                                                                                  stdout=self.sender_plcs_files[index]))
            print("Launched plc" + str(self.sender_plcs[index]))
            index += 1
            time.sleep(0.1)

        # After the servers are done, we can launch the client PLCs
        index = 0
        for plc in self.receiver_plcs:
            self.receiver_plcs_nodes.append(net.get('plc' + str(self.receiver_plcs[index])))
            self.receiver_plcs_files.append(open("output/plc" + str(self.receiver_plcs[index]) + ".log", 'r+'))
            cmd_string = "python automatic_plc.py -n plc" + str(self.receiver_plcs[index]) + " -w " + str(self.week_index)
            print "Launching PLC with command: " + cmd_string
            cmd = shlex.split(cmd_string)
            self.receiver_plcs_processes.append(self.receiver_plcs_nodes[index].popen(cmd,stderr=sys.stdout,
                                                                                      stdout=self.receiver_plcs_files[index]))
            print("Launched plc" + str(self.receiver_plcs[index]))
            index += 1
            time.sleep(0.1)

        # Launch an iperf server in LAN1 (same LAN as PLC1) and a client in LAN3 (same LAN as PLC3)
        if iperf_test == 1:
            self.iperf_server_node = net.get('server')
            self.iperf_client_node = net.get('client')

            iperf_server_file = open("output/server.log", "r+")
            iperf_client_file = open("output/client.log", "r+")

            iperf_server_cmd = shlex.split("python iperf_server.py")
            self.iperf_server_process = self.iperf_server_node.popen(iperf_server_cmd, stderr=sys.stdout,
                                                                     stdout=iperf_server_file)
            print "[*] Iperf Server launched"

            # iperf_client_cmd = shlex.split("python iperf_client.py -c 10.0.1.1 -P 100 -t 690")

            iperf_client_cmd = shlex.split("python iperf_client.py -c 10.0.2.1 -P 100 -t 2400")
            self.iperf_client_process = self.iperf_client_node.popen(iperf_client_cmd, stderr=sys.stdout,
                                                                     stdout=iperf_client_file)
            print "[*] Iperf Client launched"

        # Launching automatically mitm attack
        if mitm_attack == 1:
            attacker_file = open("output/attacker.log", 'r+')
            attacker = net.get('attacker')
            # In the future, the type of attack sent to the script should be obtained from utils configuration. An ENUM should be better
            mitm_cmd = shlex.split("../../../attack-experiments/env/bin/python "
                                   "../../attack_repository/mitm_plc/mitm_attack.py 192.168.1.1 192.168.1.254 exponential_offset")
            print 'Running MiTM attack with command ' + str(mitm_cmd)
            self.mitm_process = attacker.popen(mitm_cmd, stderr=sys.stdout, stdout=attacker_file)
            print "[] Attacking"

        print "[] Launching SCADA"
        self.scada_node = net.get('scada')
        self.scada_file = open("output/scada.log", "r+")
        cmd_string = "python automatic_plc.py -n scada -w " + str(self.week_index)
        cmd = shlex.split(cmd_string)
        self.scada_process = self.scada_node.popen(cmd, stderr=sys.stdout, stdout=self.scada_file)
        print "[*] SCADA Successfully launched"
        print "[*] Launched the PLCs and SCADA process, launching simulation..."
        physical_output = open("output/physical.log", 'r+')
        plant = net.get('plant')

        simulation_cmd = shlex.split("python automatic_plant.py c_town_config.yaml " + str(self.week_index))
        self.simulation = plant.popen(simulation_cmd, stderr=sys.stdout, stdout=physical_output)
        print "[] Simulating..."

        print "[] Simulating..."
        while self.simulation.poll() is None:
            pass
        self.finish()

    def create_log_files(self):
        cmd = shlex.split("bash ./create_log_files.sh")
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
        self.end_process(self.scada_process)

        index = 0
        for plc in self.receiver_plcs_processes:
            print "[] Terminating PLC" + str(self.receiver_plcs[index])
            if plc:
                self.end_process(plc)
                print "[*] PLC" + str(self.receiver_plcs[index]) + " terminated"
            index += 1

        index = 0
        for plc in self.sender_plcs_processes:
            print "[] Terminating PLC" + str(self.sender_plcs[index])
            if plc:
                self.end_process(plc)
                print "[*] PLC" + str(self.sender_plcs[index]) + " terminated"
            index += 1

        if self.mitm_process:
            self.end_process(self.mitm_process)
        print "[*] All processes terminated"

        if self.iperf_client_process:
            self.end_process(self.iperf_client_process)
            print "Iperf Client process terminated"

        if self.iperf_server_process:
            self.end_process(self.iperf_server_process)
            print "Iperf Server process terminated"

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

    if len(sys.argv) < 2:
        week_index = str(0)
    else:
        week_index = sys.argv[1]

    config_file = "c_town_config.yaml"
    print "Initializing experiment with config file: " + str(config_file)
    initializer = ExperimentInitializer(config_file, week_index)

    # this creates plc_dicts.yaml and utils.py
    #initializer.run_parser()

    complex_topology = initializer.get_complex_topology()
    week_index = initializer.get_week_index()
    simulation_type = initializer.get_simulation_type()
    plc_dict_path = initializer.get_plc_dict_path()

    #week_index, sim_type, config_file, plc_dict_path
    topo = CTownTopo(week_index, simulation_type, config_file, plc_dict_path)
    net = Mininet(topo=topo, autoSetMacs=True, link=TCLink)
    minitown_cps = CTown(name='ctown', net=net, week_index=week_index)