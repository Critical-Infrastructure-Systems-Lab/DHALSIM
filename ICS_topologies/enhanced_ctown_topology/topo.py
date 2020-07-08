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
        switches = []

        r0_ip = '10.0.1.254/24'
        r0 = self.addNode('r0', cls=LinuxRouter, ip=r0_ip)
        routers.append(r0)

        for i in range(1,10):
            routers.append(self.addNode('r' + str(i), cls=LinuxRouter, ip='10.0.' + str(i) + '.1/24'))
            switches.append((self.addSwitch('s'+ str(i))))
            plcs.append(self.addNode('plc' + str(i), ip='192.168.1.1/24', defaultRoute='via 192.168.1.254/24'))

            self.addLink(routers[i], r0, intfName2='r0-eth' + str(i - 1), params2={'ip': '10.0.' + str(i) + '.254/24'})
            self.addLink(plcs[i-1], switches[i-1])
            self.addLink(switches[i - 1], routers[i], intfName2='r'+str(i)+'-eth1', params2={'ip': '192.168.1.254/24'})

        plant = self.addHost('plant')

        # SCADA wil be on the same LAN as the PLC3
        scada = self.addNode('scada', ip='192.168.1.2/24', defaultRoute='via 192.168.1.254/24')

        # Attacker will be on the same LAN as the PLC5
        attacker = self.addNode('attacker', ip='192.168.1.2/24', defaultRoute='via 192.168.1.254/24')

        self.addLink(scada, switches[0])
        self.addLink(attacker, switches[8])