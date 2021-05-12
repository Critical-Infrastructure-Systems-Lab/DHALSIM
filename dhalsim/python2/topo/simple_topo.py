import os.path
from mininet.topo import Topo
from mininet.node import Node
from mininet.link import Intf
from pathlib import Path
import yaml
import random


class LinuxRouter(Node):
    """
    A node with IP forwarding enabled
    """

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_foward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_foward=0')


class SimpleTopo(Topo):
    """
    A class for a simple mininet topology
    """

    def __init__(self, intermediate_yaml_path):
        """
        Initialize a simple mininet topology

        :param intermediate_yaml_path: The path of the intermediate.yaml file
        """

        self.intermediate_yaml_path = intermediate_yaml_path

        with self.intermediate_yaml_path.open(mode='r') as intermediate_yaml:
            self.data = yaml.safe_load(intermediate_yaml)

        self.generate_plc_data(self.data['plcs'])

        print(self.data)

        with self.intermediate_yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(self.data, intermediate_yaml)

        Topo.__init__(self)


    def generate_plc_data(self, plcs):
        for idx, plc in enumerate(plcs):
            plc_ip = "192.168.1." + str(idx + 1) + "/24"
            plc_mac = get_random_mac_address()
            plc_int = plc['name'] + "-eth0"

            # Store the data in self.data
            plc['ip'] = plc_ip
            plc['mac'] = plc_mac
            plc['interface'] = plc_int


    def build(self):
        """
        Build the mininet topology
        """

        # -- FIELD NETWORK -- #
        router_ip = "192.168.1.254/24"
        # Add a router to the network
        router = self.addNode('r0', cls=LinuxRouter, ip=router_ip)
        # Add a switch to the network
        switch = self.addSwitch('s1')
        self.addLink(switch, router, intfName2='r0-eth1', params2={'ip': router_ip})

        gateway = 'via ' + router_ip

        if 'plcs' in self.data.keys():
            # Add PLCs to the mininet network
            for idx, plc in enumerate(self.data['plcs']):
                plc_node = self.addHost(
                    plc['name'],
                    mac=plc['mac'],
                    ip=plc['ip'],
                    defaultRoute=gateway)
                self.addLink(switch, plc_node, intfName2=plc['interface'])

        # -- SUPERVISOR NETWORK -- #
        supervisor_ip = "192.168.2.254/24"
        # Add a switch for the supervisor network
        supervisor_switch = self.addSwitch("s2")
        # Link the router and the supervisor switch
        self.addLink(supervisor_switch, router, intfName2='r0-eth2', params2={'ip': supervisor_ip})
        # Create a supervisor gateway
        supervisor_gateway = "via " + supervisor_ip
        # Add a scada to the network
        scada = self.addHost('scada', ip="192.168.2.1/24", defaultRoute=supervisor_gateway)
        # Add a link between the switch and the scada
        self.addLink(supervisor_switch, scada)

    def setup_network(self, net):
        # Code from automatic_run.py
        pass


def get_random_mac_address():
    return "05:01:65:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
