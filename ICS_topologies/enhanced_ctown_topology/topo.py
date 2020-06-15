from mininet.node import Node
from mininet.topo import Topo

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
        plcs = []

        r0_ip = '10.0.1.254/24'

        r0 = self.addNode('r0', cls=LinuxRouter, ip=r0_ip)
        routers.append(r0)

        for i in range(1,10):
            routers.append(self.addNode('r' + str(i), cls=LinuxRouter, ip='10.0.' + str(i) + '.1/24'))
            self.addLink(routers[i], r0, intfName2='r0-eth' + str(i-1), params2={'ip': '10.0.' + str(i) + '.254/24'})
            plcs.append( self.addNode('plc' + str(i), ip='192.168.1.1/24', defaultRoute='via 192.168.1.254/24'))
            #self.addLink(plc1, r1, intfName2='r1-eth1', params2={'ip': '192.168.1.254/24'})


        #  ---------------- Central Router (r0) ----------------------  #
        #r1 = self.addNode('r1', cls=LinuxRouter, ip='10.0.1.1/24')
        #r2 = self.addNode('r2', cls=LinuxRouter, ip='10.0.2.1/24')

        #self.addLink(r1, r0, intfName2='r0-eth0', params2={'ip': '10.0.1.254/24'})
        #self.addLink(r2, r0, intfName2='r0-eth1', params2={'ip': '10.0.2.254/24'})

        #plc1 = self.addNode('plc1', ip='192.168.1.1/24', defaultRoute='via 192.168.1.254/24')
        #self.addLink(plc1, r1, intfName2='r1-eth1', params2={'ip': '192.168.1.254/24'})

        #plc2 = self.addNode('plc2', ip='192.168.1.1/24', defaultRoute='via 192.168.1.254/24')
        #self.addLink(plc2, r2, intfName2='r2-eth1', params2={'ip': '192.168.1.254/24'})

