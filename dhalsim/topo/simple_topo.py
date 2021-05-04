from mininet.topo import Topo
from mininet.node import Node


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
    This class is a mininet simple topology.
    """

    def __init__(self, plc_configs):
        """
        Initialize a simple topology

        :param plc_configs: An array of PlcConfig objects
        """
        self.plc_configs = plc_configs
        # TODO Add the plc_dicts alternative to this
        # Initialize the topology (this calls build)
        Topo.__init__(self)

    def build(self):
        """
        Build the mininet network. This function overrides the mininet build method
        """
        # -- FIELD NETWORK -- #
        router_ip = "192.168.1.254/24"
        # Add a router to the network
        router = self.addNode('r0', cls=LinuxRouter, ip=router_ip)
        # Add a switch to the network
        switch = self.addSwitch('s1')
        # Add a link between the router and the switch
        self.addLink(switch, router, intfName2='r0-eth1', params2={'ip': router_ip})

        gateway = 'via ' + router_ip

        for index, plc_config in enumerate(self.plc_configs):
            # TODO What if we have >254 PLCs?
            plc_config.ip = "192.168.1." + str(index + 1) + "/24"
            # Add the PLC to the network (and the array)
            plc = self.addHost(plc_config.name, ip=plc_config.ip, defaultRoute=gateway)
            # Add a link between the added plc and the switch
            self.addLink(switch, plc)

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
