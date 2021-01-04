from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from complex_topo import ComplexTopo
from simple_topo import SimpleTopo
from initialize_experiment import ExperimentInitializer
import sys
import time
import shlex
import signal
import argparse
import yaml
from mininet.link import TCLink
import subprocess
from os.path import expanduser

automatic = 0
iperf_test = 0


class DHALSIM(MiniCPS):
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

    # This method exists, because using TCLinks mininet ignores the ip parameter of some interfaces. We use TCLinks to
    # support bw and delay configurations on interfaces
    def configure_routers_interface(self, index):
        a_router = net.get('r' + index)
        a_router.cmd('ifconfig r' + index + '-eth1 192.168.1.254')
        a_router.waitOutput()

    # This method exists, because using TCLinks mininet ignores the ip parameter of some interfaces. We use TCLinks
    # to support bw and delay configurations on interfaces
    def configure_r0_interfaces(self, index):
        router0 = net.get('r0')
        router0.cmd('ifconfig r0-eth' + str(index) + ' 10.0.' + str(index+1) + '.254 netmask 255.255.255.0' )

    def setup_network(self, complex_topo):
        plc_number = len(self.plc_dict)
        if complex_topo:
            for index in range(0, plc_number):
                self.do_forward(net.get('r' + str(index)))
                self.configure_routers_interface(str(index+1))
                self.configure_r0_interfaces(index+1)
                self.add_degault_gateway(net.get('plc' + str(index+1)), '192.168.1.254')
                self.add_degault_gateway(net.get('r' + str(index+1)), '10.0.' + str(index+1) + '.254')
                index += 1

            index_limit = plc_number + 1
            for i in range(1, index_limit):
                self.setup_iptables('r' + str(i))

            self.add_degault_gateway(net.get('scada'), '192.168.1.254')
        else:
            # toDo: Support simple network topology
            for i in range(0,9):
                self.add_degault_gateway(net.get('plc' + str(i + 1)), '192.168.1.254')

    def get_plc_launch_order(self):
        """
        To launch the experiment more gracefully is nice to launch the processes that are ENIP servers in the network
        topology. We can get this order by analyzing the dependencies. In essence, a PLC without dependencies is a server
        WARNING: There could be situations where this method has deadlocks and we are not testing them
        :return:
        """
        # toDo: Handle possible deadlocks because dependencies

        plc_launch_order = []
        pending_plcs = []
        for plc in self.plc_dict:
            # Add the ENIP servers
            if not plc['Dependencies']:
                plc_launch_order.append(plc['PLC'].lower())
            # These are ENIP clients
            else:
                pending_plcs.append(plc)

        self.last_plc = plc_launch_order[-1]

        for plc in pending_plcs:
            dependency_counter = 0
            for dependency in plc['Dependencies']:
                if dependency['PLC'].lower() in plc_launch_order:
                    dependency_counter += 1

            if dependency_counter == len(plc['Dependencies']):
                plc_launch_order.append(plc['PLC'].lower())

        return plc_launch_order

    def load_plc_dict(self, dict_path):
        with open(dict_path) as config_file:
            options = yaml.load(config_file, Loader=yaml.FullLoader)
        return options

    def __init__(self, name, net, complex_topo, a_week_index, sim_type, a_plc_dict_path, a_config_file):
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        self.config_file = a_config_file
        self.week_index = a_week_index
        self.sim_type = sim_type

        net.start()

        self.last_plc = None
        self.plc_dict_path = a_plc_dict_path
        # We need the plc dicts to analyze the dependencies and define the PLC process launch order
        # It shouldn't matter that much, because in case of no connections we simply retry, but we want to avoid
        # the excessive number of error messages in log because of no connections
        self.plc_dict = self.load_plc_dict(self.plc_dict_path)
        self.plc_launch_order = self.get_plc_launch_order()

        self.setup_network(complex_topo)

        self.plc_nodes = []
        self.plc_files = []
        self.plc_processes = []

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
        last_plc_flag = 0

        for plc in self.plc_launch_order:

            if self.last_plc == plc:
                last_plc_flag = 1

            self.plc_nodes.append(net.get(str(self.plc_launch_order[index])))

            self.plc_files.append(open("output/" + str(self.plc_launch_order[index]) + ".log", 'r+'))
            self.plc_processes.append(self.plc_nodes[index].popen
                                      (sys.executable, "generic_automatic_plc.py", "-c", self.config_file, "-n",
                                       str(self.plc_launch_order[index]), "-d", self.plc_dict_path, "-l",
                                       str(last_plc_flag),
                                       stderr=sys.stdout, stdout=self.plc_files[index]))
            print("Launched " + str(self.plc_launch_order[index]))
            index += 1
            time.sleep(0.2)

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

            iperf_client_cmd = shlex.split("python iperf_client.py -c 10.0.2.1 -P 100 -t 2400")
            self.iperf_client_process = self.iperf_client_node.popen(iperf_client_cmd, stderr=sys.stdout,
                                                                     stdout=iperf_client_file)
            print "[*] Iperf Client launched"

        print "[] Launching SCADA"
        #self.scada_node = net.get('scada')
        #self.scada_file = open("output/scada.log", "r+")
        #self.scada_process = self.scada_node.popen(sys.executable, "automatic_plc.py", "-n", "scada", "-w", str(self.week_index), "-d", self.plc_dict_path, stderr=sys.stdout,stdout=self.scada_file)
        print "[*] SCADA Successfully launched"

        physical_output = open("output/physical.log", 'r+')
        print "[*] Launched the PLCs and SCADA process, launching simulation..."
        plant = net.get('plant')

        simulation_cmd = shlex.split("python automatic_plant.py " + str(self.config_file))
        self.simulation = plant.popen(simulation_cmd, stderr=sys.stdout, stdout=physical_output)
        print "[] Simulating..."

        print "[] Simulating..."
        while self.simulation.poll() is None:
            pass
        self.finish()

    def create_log_files(self):
        cmd = shlex.split("bash ./create_log_files.sh")
        subprocess.call(cmd)

    def end_plc_process(self, plc_process):

        plc_process.send_signal(signal.SIGINT)
        plc_process.wait()

        if plc_process:
            if plc_process.poll() is None:
                plc_process.terminate()
            if plc_process.poll() is None:
                plc_process.kill()

    def finish(self):
        print "[*] Simulation finished"

        #if self.scada_process:
        #    print "[] Finishing SCADA process"
        #    self.end_plc_process(self.scada_process)
        #    print "[*] Finished SCADA process"

        index = len(self.plc_launch_order) - 1
        for plc in reversed(self.plc_processes):
            print "[] Terminating " + str(self.plc_launch_order[index])
            if plc:
                self.end_plc_process(plc)
                print "[*] PLC" + str(self.plc_launch_order[index]) + " terminated"
            index -= 1

        if self.mitm_process:
            self.end_plc_process(self.mitm_process)
        print "[*] All processes terminated"

        if self.iperf_client_process:
            self.end_plc_process(self.iperf_client_process)
            print "Iperf Client process terminated"

        if self.iperf_server_process:
            self.end_plc_process(self.iperf_server_process)
            print "Iperf Server process terminated"

        if self.simulation:
            self.simulation.terminate()

        cmd = shlex.split("./kill_cppo.sh")
        subprocess.call(cmd)
        net.stop()
        sys.exit(0)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Script that runs a DHALSIM experiment, using MiniCPS and WNTR')
    parser.add_argument("--config", "-c", help="YAML experiment configuration file")
    parser.add_argument("--week", "-w", help="Week index, only used batch simulation mode")
    args = parser.parse_args()

    # Global configuration file
    if args.config:
        config_file = args.config
    else:
        config_file = "c_town_config.yaml"

    print "Initializing experiment with config file: " + str(config_file)
    initializer = ExperimentInitializer(config_file, args.week)

    # this creates plc_dicts.yaml and utils.py
    initializer.run_parser()

    complex_topology = initializer.get_complex_topology()
    week_index = initializer.get_week_index()
    simulation_type = initializer.get_simulation_type()
    plc_dict_path = initializer.get_plc_dict_path()

    if complex_topology:
        print "Launching complex network topology"
        topo = ComplexTopo(week_index=week_index, sim_type=simulation_type, config_file=config_file, plc_dict_path=plc_dict_path)
    else:
        print "Launching simple network topology"
        topo = SimpleTopo(week_index=week_index, sim_type=simulation_type, config_file=config_file, plc_dict_path=plc_dict_path)

    net = Mininet(topo=topo, autoSetMacs=True, link=TCLink)
    experiment = DHALSIM(name='ctown', net=net, complex_topo=complex_topology, a_week_index=week_index, sim_type=simulation_type, a_plc_dict_path=plc_dict_path, a_config_file=config_file)