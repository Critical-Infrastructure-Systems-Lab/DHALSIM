from mininet.node import Node
from mininet.topo import Topo
import pandas as pd

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
    def __init__( self, week_index ):
        "Create custom topo."
        self.week_index = int(week_index)
        # Initialize topology
        Topo.__init__( self )

    def build(self):

        routers = []
        plcs = []
        switches = []

        print("Week index is: " + str(self.week_index))

        network_delays = pd.read_csv('../../Demand_patterns/network_links_delay_small.csv', index_col=0)
        network_losses = pd.read_csv('../../Demand_patterns/network_loss_small.csv', index_col=0)

        r0_ip = '10.0.1.254/24'
        r0 = self.addNode('r0', cls=LinuxRouter, ip=r0_ip)
        routers.append(r0)

        for i in range(1,10):
            routers.append(self.addNode('r' + str(i), cls=LinuxRouter, ip='10.0.' + str(i) + '.1/24'))
            switches.append((self.addSwitch('s'+ str(i))))
            plcs.append(self.addNode('plc' + str(i), ip='192.168.1.1/24', defaultRoute='via 192.168.1.254/24'))

            self.addLink(routers[i], r0, intfName2='r0-eth' + str(i - 1), params2={'ip': '10.0.' + str(i) + '.254/24'})
            print("Link " + str(i) + " delay: " + str(network_delays.iloc[self.week_index]['r' + str(i)])+"ms" + " loss: " + str(network_losses.iloc[self.week_index]['r' + str(i)]) )
            self.addLink(switches[i - 1], routers[i], intfName2='r' + str(i) + '-eth1',
                         params2={'ip': '192.168.1.254/24'})
            loss = network_losses.iloc[self.week_index]['r' + str(i)]
            linkopts = dict(bw=100, delay=str(network_delays.iloc[self.week_index]['r' + str(i)])+"ms", loss=loss, max_queue_size=1000,
                           use_htb=True)
            self.addLink(plcs[i-1], switches[i-1], **linkopts)

        plant = self.addHost('plant')
        # SCADA wil be on the same LAN as the PLC3
        scada = self.addNode('scada', ip='192.168.1.2/24', defaultRoute='via 192.168.1.254/24')

        # Attacker will be on the same LAN as the PLC5
        attacker = self.addNode('attacker', ip='192.168.1.2/24', defaultRoute='via 192.168.1.254/24')

        self.addLink(scada, switches[0])
        self.addLink(attacker, switches[8])

        # For iperf tests we want the client/server to be in the possible most impactful LAN (LAN1 and LN3)
        client = self.addNode('client', ip='192.168.1.2/24', defaultRoute='via 192.168.1.254/24')
        server = self.addNode('server', ip='192.168.1.3/24', defaultRoute='via 192.168.1.254/24')

        self.addLink(server, switches[0])
        self.addLink(client, switches[2])