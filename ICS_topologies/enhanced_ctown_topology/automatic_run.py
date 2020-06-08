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

    def do_forward(self, node):
        # Pre experiment configuration, prepare routing path
        node.cmd('sysctl net.ipv4.ip_forward=1')
        node.waitOutput()

    def add_degault_gateway(self, node):
        node.cmd('roude add default gw 192.168.1.254')
        node.waitOutput()

    def __init__(self, name, net):
        net.start()

        r0 = net.get('r0')
        self.do_forward(r0)

        for i in range(0, 3):
            self.do_forward( net.get('r' + str(i) ) )

        self.add_degault_gateway( net.get('plc1') )
        self.add_degault_gateway( net.get('plc2') )

        CLI(net)
        net.stop()

        net.stop()
        sys.exit(0)

if __name__ == "__main__":
    topo = CTownTopo()
    net = Mininet(topo=topo)
    minitown_cps = CTown(name='ctown', net=net)
