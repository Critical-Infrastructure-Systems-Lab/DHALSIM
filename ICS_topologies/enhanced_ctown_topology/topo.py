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


class CTownTopo(Topo):
    """
    Enhanced C-Town topology
    Each PLC is now in a local area network called "substation"
    Substation 1 includes the SCADA server
    """
    def __init__(self, week_index, sim_type, config_file, plc_dict_path):
        "Create custom topo."

        "Create custom topo."
        self.week_index = int(week_index)
        self.options = self.load_options(config_file)

        # Initialize topology
        Topo.__init__(self)

    def load_options(self, config_file):
        with open(config_file) as config_file:
            options = yaml.load(config_file, Loader=yaml.FullLoader)
        return options

    def build(self):

        routers = []
        plcs = []
        switches = []

        custom_links = self.options['initial_custom_flag']

        network_delays = pd.read_csv('../../Demand_patterns/network_links_delay_small.csv', index_col=0)
        network_losses = pd.read_csv('../../Demand_patterns/network_loss_small.csv', index_col=0)

        r0_ip = '10.0.1.254/24'
        r0 = self.addNode('r0', cls=LinuxRouter, ip=r0_ip, mac='00:00:00:01:00:00')
        routers.append(r0)

        # Scheme for MAC addresses in R0 in the net 10.0.X.254:
        # '00:00:00:01:00:00'

        # Scheme for MAC addresses in Ri in the interfaces with IP 192.1.1.254
        # '00:00:00:00:01:00'
        for i in range(1, 10):

            # todo: Fix this hotfix. We are assigning MAC addresses manually to routers, because Mininet is giving
            # them random MAC addresses
            r0_mac = '00:00:01:00:00:0' + str(i)
            ri_inbound_mac = '00:00:00:01:00:0' + str(i)
            ri_outbound_mac = '00:00:00:00:01:0' + str(i)
            ri_intermediate_mac = '00:01:00:00:00:0' + str(i)
            routers.append(self.addNode('r' + str(i), cls=LinuxRouter, ip='10.0.' + str(i) + '.1/24',
                                        mac=ri_intermediate_mac))
            switches.append((self.addSwitch('s' + str(i))))
            plcs.append(self.addNode('plc' + str(i), ip='192.168.1.1/24', defaultRoute='via 192.168.1.254/24'))

            loss = network_losses.iloc[self.week_index]['r' + str(i)]
            self.addLink(routers[i], r0, intfName2='r0-eth' + str(i - 1), params2={'ip': '10.0.' + str(i) + '.254/24'},
                         addr2=r0_mac)
            self.addLink(switches[i - 1], routers[i], intfName2='r' + str(i) + '-eth1',
                         params2={'ip': '192.168.1.254/24'}, addr2=ri_outbound_mac)
            if custom_links == "True":
                print("Link " + str(i) + " delay: " + str(
                    network_delays.iloc[self.week_index]['r' + str(i)]) + "ms" + " loss: " + str(
                    network_losses.iloc[self.week_index]['r' + str(i)]))
                linkopts = dict(bw=1000, delay=str(network_delays.iloc[self.week_index]['r' + str(i)])+"ms",
                                loss=loss, max_queue_size=1000, use_htb=True)
                self.addLink(plcs[i-1], switches[i-1], params2={'mac': ri_inbound_mac}, **linkopts)
            else:
                self.addLink(plcs[i - 1], switches[i - 1])

        plant = self.addHost('plant')
        # SCADA wil be on the same LAN as the PLC3.
        scada = self.addNode('scada', ip='192.168.1.2/24', defaultRoute='via 192.168.1.254/24')

        # toDo: We have to decide if always add these nodes and only activate them when needed. Or add them
        # dynamically only when there is a network attack
        attacker_1 = self.addNode('attacker_1', ip='192.168.1.10/24', defaultRoute='via 192.168.1.254/24')
        attacker_2 = self.addNode('attacker_2', ip='192.168.1.10/24', defaultRoute='via 192.168.1.254/24')
        attacker_4 = self.addNode('attacker_4', ip='192.168.1.10/24', defaultRoute='via 192.168.1.254/24')

        self.addLink(scada, switches[0])

        # Attack on Tank3 Switch4. PLC4 to PLC3. Stored in switches[3]
        # Switch 1 is Connected to PLC1. We connect to the plc_source
        self.addLink(attacker_1, switches[0])

        # Switch 4 is Connected to PLC4. We connect to the plc_source
        self.addLink(attacker_4, switches[3])

        # Switch 2 is Connected to PLC2. We connect to the plc_source
        self.addLink(attacker_2, switches[1])

        # For iperf tests we    want the client/server to be in the possible most impactful LAN (LAN1 and LN3)
        client = self.addNode('client', ip='192.168.1.2/24', defaultRoute='via 192.168.1.254/24')
        server = self.addNode('server', ip='192.168.1.3/24', defaultRoute='via 192.168.1.254/24')

        self.addLink(server, switches[0])
        self.addLink(client, switches[2])