from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from topo import CTownTopo
import sys
import time
import shlex
import subprocess
import signal

class CTown(MiniCPS):
    """ Script to run the Minitown SCADA topology """

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

    def __init__(self, name, net):
        net.start()

        for i in range(0, 3):
            self.do_forward(net.get('r' + str(i)))

        self.add_degault_gateway(net.get('plc1'), '192.168.1.254')
        self.add_degault_gateway(net.get('plc2'), '192.168.1.254')

        self.add_degault_gateway(net.get('r1'), '10.0.1.254')
        self.add_degault_gateway(net.get('r2'), '10.0.2.254')

        for i in range(1, 3):
            self.setup_iptables('r' + str(i))

        CLI(net)
        net.stop()

        net.stop()
        sys.exit(0)

if __name__ == "__main__":
    topo = CTownTopo()
    net = Mininet(topo=topo)
    minitown_cps = CTown(name='ctown', net=net)
