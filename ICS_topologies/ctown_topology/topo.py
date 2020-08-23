from mininet.node import Node
from mininet.topo import Topo
from utils import IP, NETMASK
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


class ScadaTopo(Topo):
    """
    SCADA topology
    """

    def build(self):
        # Add router
        fieldIP = '192.168.1.254/24'  # IP Address for r0-eth1
        network_delays = pd.read_csv('../../Demand_patterns/network_links_delay.csv', index_col=0)
        network_losses = pd.read_csv('../../Demand_patterns/network_loss_small.csv', index_col=0)
        week_index = 0

        # ---------------- FIELD NETWORK ----------------------  #
        router = self.addNode('r0', cls=LinuxRouter, ip=fieldIP)

        # Add switch of supervisory network
        s1 = self.addSwitch('s1')
        self.addLink(s1, router, intfName2='r0-eth1', params2={'ip': fieldIP})

        gateway_1 = 'via ' + fieldIP

        plant = self.addHost('plant')
        attacker = self.addHost('attacker', ip=IP['attacker'] + NETMASK, defaultRoute=gateway_1)

        plcs=[]

        for i in range(1,10):
            plcs.append(self.addHost('plc' + str(i), ip=IP['plc'+str(i)] + NETMASK, defaultRoute=gateway_1))
            this_delay = str(network_delays.iloc[week_index]['r' + str(i)]) + "ms"
            print("Link " + str(i) + " delay: " + this_delay + " loss: " + str(network_losses.iloc[week_index]['r' + str(i)]))
            #linkopts = dict(bw=1000, delay=this_delay + "ms", loss=network_losses.iloc[week_index]['r' + str(i)], max_queue_size=1000, use_htb=True)
            linkopts = dict(bw=1000, delay="4.501130591094455ms",loss=0.2448607788241941, max_queue_size=1000, use_htb=True)
            self.addLink(s1, plcs[i-1], **linkopts)

        self.addLink(s1, attacker)

        # ---------------- SUPERVISORY NETWORK --------------  #
        supervisoryIP = '192.168.2.254/24'
        s2 = self.addSwitch('s2')
        self.addLink(s2, router, intfName2='r0-eth2', params2={'ip': supervisoryIP})
        gateway_2 = 'via ' + supervisoryIP

        scada = self.addHost('scada', ip=IP['scada'] + NETMASK, defaultRoute=gateway_2)
        attacker2 = self.addHost('attacker2', ip=IP['attacker2'] + NETMASK, defaultRoute=gateway_2)

        self.addLink(s2, scada)
        self.addLink(s2, attacker2)