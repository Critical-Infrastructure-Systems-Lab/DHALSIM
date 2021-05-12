import os.path

from mininet.topo import Topo
from mininet.node import Node
import yaml


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

        with open(os.path.abspath(intermediate_yaml_path)) as intermediate_yaml:
            self.data = yaml.safe_load(intermediate_yaml)

        Topo.__init__(self)

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

        print(self.data)

        if 'plcs' in self.data.keys():
            for idx, plc in enumerate(self.data['plcs']):
                plc_ip = "192.168.1." + str(idx + 1) + "/24"
                plc_node = self.addHost(plc['name'], ip=plc_ip, defaultRoute=gateway)
                self.addLink(switch, plc_node)

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