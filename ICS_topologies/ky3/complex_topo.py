from mininet.node import Node
from mininet.topo import Topo
import pandas as pd
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


class ComplexTopo(Topo):
    """
    Enhanced C-Town topology
    Each PLC is now in a local area network called "substation"
    Substation 1 includes the SCADA server
    """
    def __init__( self, week_index, sim_type, config_file, plc_dict_path):
        "Create custom topo."
        self.week_index = int(week_index)
        self.options = self.load_options(config_file)
        self.plcs_dict = self.load_plcs(plc_dict_path)

        # Initialize topology
        Topo.__init__( self )

    def load_plcs(self, plc_file):
        with open(plc_file) as config_file:
            options = yaml.load(config_file, Loader=yaml.FullLoader)
        return options

    def load_options(self, config_file):
        with open(config_file) as config_file:
            options = yaml.load(config_file, Loader=yaml.FullLoader)
        return options

    def build(self):

        routers = []
        plcs = []
        switches = []

        print("Week index is: " + str(self.week_index))

        if 'network_delay_path' in self.options:
            network_delay_path = self.options['network_delay_path']
        else:
            network_delay_path = '../../Demand_patterns/network_links_delay_small.csv'

        if 'network_losses_path' in self.options:
            network_losses_path = self.options['network_losses_path']
        else:
            network_losses_path = '../../Demand_patterns/network_loss_small.csv'

        network_delays = pd.read_csv(network_delay_path, index_col=0)
        network_losses = pd.read_csv(network_losses_path, index_col=0)

        r0_ip = '10.0.1.254/24'
        r0 = self.addNode('r0', cls=LinuxRouter, ip=r0_ip)
        routers.append(r0)

        index = 1
        for plc in self.plcs_dict:
            routers.append(self.addNode('r' + str(index), cls=LinuxRouter, ip='10.0.' + str(index) + '.1/24'))
            switches.append((self.addSwitch('s'+ str(index))))

            plc_name = plc['PLC'].lower()
            plcs.append(self.addNode(plc_name, ip='192.168.1.1/24', defaultRoute='via 192.168.1.254/24'))

            self.addLink(routers[index], r0, intfName2='r0-eth' + str(index - 1), params2={'ip': '10.0.' + str(index) + '.254/24'})
            print("Link " + str(index) + " delay: " + str(network_delays.iloc[self.week_index]['r' + str(index)])+"ms" + " loss: " + str(network_losses.iloc[self.week_index]['r' + str(index)]) )
            self.addLink(switches[index - 1], routers[index], intfName2='r' + str(index) + '-eth1',
                         params2={'ip': '192.168.1.254/24'})
            loss = network_losses.iloc[self.week_index]['r' + str(index)]
            linkopts = dict(bw=1000, delay=str(network_delays.iloc[self.week_index]['r' + str(index)])+"ms", loss=loss, max_queue_size=1000,
                           use_htb=True)
            self.addLink(plcs[index-1], switches[index-1], **linkopts)
            index += 1

        plant = self.addHost('plant')
        attacker = self.addHost('attacker', ip='192.168.1.10/24', defaultRoute='via 192.168.1.254/24')
        scada = self.addNode('scada', ip='192.168.1.2/24', defaultRoute='via 192.168.1.254/24')
        self.addLink(scada, switches[0])
        self.addLink(attacker, switches[0])
