from mininet.node import Node
from mininet.topo import Topo
from utils import IP, plc_netmask


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




class CTownTopo(Topo):
    """
    Enhanced C-Town topology
    Each PLC is now in a local area network called "substation"
    Substation 1 includes the SCADA server
    """
    def build(self):
        routers = []
        switches = []
        plcs = []

        r0_ip = '10.0.1.254/8'
        net_prefix = '10.0.1.'

        # ---------------- Central Router (r0) ----------------------  #
        routers.append(self.addNode('r0', cls=LinuxRouter, ip=r0_ip))
        switches.append(self.addSwitch('s0'))
        self.addLink(switches[0], routers[0], intfName2='r0-eth0', params2={'ip': r0_ip})

        # ---------------- Substation Routers and Central Router Connection ----------------------  #
        for i in range(1,10):
            routers.append( self.addNode( 'r' + str(i), cls=LinuxRouter, ip=net_prefix + str(i) + '/8' ) )
            self.addLink(switches[0], routers[i], intfName2='r' + str(i) + '-eth0', params2={'ip': net_prefix + str(i) + '/8' })

        # ---------------- Substation 1 ----------------------  #
        plc_gateway = '192.168.1.254'
        plcs.append(self.addHost('plc1', ip=IP['plc_ip'] + plc_netmask, defaultRoute='via ' + plc_gateway))
        self.addLink(plcs[0], routers[1], intfName2='r1-eth1', params2={'ip': plc_gateway+plc_netmask})