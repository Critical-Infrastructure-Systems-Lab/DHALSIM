import os.path

from mininet.node import Node
from mininet.topo import Topo
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
    SCADA topology
    """

    def __init__(self, week_index, sim_type, config_file, plc_dict_path):
        # Create custom topo
        # self.yaml_path = intermediate_yaml_path
        # self.week_index = int(week_index)
        # self.options = self.load_options(config_file)
        # with self.yaml_path.open(mode='r') as yaml_file:
        #     self.intermediate_read = yaml.safe_load(yaml_file)

        # Initialize topology
        Topo.__init__(self)


    # def load_options(self, config_file):
    #     with open(config_file) as config_file:
    #         options = yaml.load(config_file, Loader=yaml.FullLoader)
    #     return options


    def build(self):
        # Add router
        fieldIP = '192.168.1.254/24'  # IP Address for r0-eth1

        # ---------------- FIELD NETWORK ----------------------  #
        router = self.addNode('r0', cls=LinuxRouter, ip=fieldIP)

        # Add switch of supervisory network
        s1 = self.addSwitch('s1')
        self.addLink(s1, router, intfName2='r0-eth1', params2={'ip': fieldIP})

        gateway_1 = 'via ' + fieldIP

        plant = self.addHost('plant')
        plc1 = self.addHost('plc1', ip='192.168.1.1/24', mac='11:22:33:44:55:01', defaultRoute=gateway_1)
        plc2 = self.addHost('plc2', ip='192.168.1.2/24', mac='11:22:33:44:55:02', defaultRoute=gateway_1)
        # attacker = self.addHost('attacker_1', ip=wadi_ip['attacker'] + NETMASK, defaultRoute=gateway_1)

        self.addLink(s1, plc1)
        self.addLink(s1, plc2)
        # self.addLink(s1, attacker)

        # ---------------- SUPERVISORY NETWORK --------------  #
        supervisoryIP = '192.168.2.254/24'
        s2 = self.addSwitch('s2')
        self.addLink(s2, router, intfName2='r0-eth2', params2={'ip': supervisoryIP})
        gateway_2 = 'via ' + supervisoryIP

        scada = self.addHost('scada', ip="192.168.2.1/24", defaultRoute=gateway_2)
        # attacker2 = self.addHost('attacker_2', ip=wadi_ip['attacker2'] + NETMASK, defaultRoute=gateway_2)

        self.addLink(s2, scada)
        # self.addLink(s2, attacker2)

        # if self.intermediate_read:
        #     with self.yaml_path.open(mode='w') as yaml_file:
        #         yaml.safe_dump(self.intermediate_read, yaml_file)