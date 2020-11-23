from mininet.node import Node
from mininet.topo import Topo
from utils import plc_netmask
import subprocess
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
    Simple topology
    """

    def __init__(self, week_index, sim_type, config_file, plc_dict_path):

        "Create custom topo."
        self.sim_type = sim_type
        self.week_index = int(week_index)
        self.plc_dicts = self.get_plc_dicts(plc_dict_path)
        # Initialize topology
        Topo.__init__( self )

    def get_plc_dicts(self, dict_path):
        """
        Given a list of PLC dicts, returns the PLC of this instance. As defined by self.name
        :return:
        """
        with open(dict_path, 'r') as plc_file:
            plc_dicts = yaml.full_load(plc_file)
        return plc_dicts

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

        plcs=[]
        for plc in self.plc_dicts:
            plc_name = plc['PLC'].lower()
            plcs.append(self.addHost(plc_name, ip=SIMPLE_IP_OPTIONS[plc_name] + plc_netmask, defaultRoute=gateway_1))
            self.addLink(s1, plcs[-1])

        # ---------------- SUPERVISORY NETWORK --------------  #
        supervisoryIP = '192.168.2.254/24'
        s2 = self.addSwitch('s2')
        self.addLink(s2, router, intfName2='r0-eth2', params2={'ip': supervisoryIP})
        gateway_2 = 'via ' + supervisoryIP

        scada = self.addHost('scada', ip=SIMPLE_IP_OPTIONS['scada'] + plc_netmask, defaultRoute=gateway_2)
        self.addLink(s2, scada)