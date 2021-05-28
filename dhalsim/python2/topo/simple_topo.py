import yaml

from mininet.topo import Topo
from mininet.node import Node
from mininet.net import Mininet


class Error(Exception):
    """Base class for exceptions in this module."""


class NoSuchPlc(Error):
    """Raised when an attack targets a PLC that does not exist"""


class LinuxRouter(Node):
    """
    A node with IP forwarding enabled
    """

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')


class SimpleTopo(Topo):
    """
    This class represents a simple topology. A simple topology is a network topology where every
    PLC is on the same LAN.

    This class will generate ip addresses, mac addresses etc. and write them back to the
    intermediate yaml file. Then, it will use that file to create all the routers, switches
    and nodes. After that, iptables rules and routes will be setup.

    :param intermediate_yaml_path: The path to the intermediate yaml file. Here will also be writen to.
    :type intermediate_yaml_path: Path
    """

    def __init__(self, intermediate_yaml_path):
        # Set variables
        self.router_ip = "192.168.1.254"
        self.supervisor_ip = "192.168.2.254"
        self.router = 'r0'
        self.plc_switch = 's1'
        self.scada_switch = 's2'

        # Load the data from the YAML file
        self.intermediate_yaml_path = intermediate_yaml_path
        with self.intermediate_yaml_path.open(mode='r') as intermediate_yaml:
            self.data = yaml.safe_load(intermediate_yaml)

        # Generate PLC data and write back to file (mac addresses, ip addresses, interface names, ...)
        self.generate_data(self.data)

        with self.intermediate_yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(self.data, intermediate_yaml)

        # Initialize mininet topology
        Topo.__init__(self)

    def generate_data(self, data):
        """
        Generate all the ips, interfaces, etc. from every plc and the scada.
        These are then applied when building the topo

        :param data: the dict resulting from a dump of the intermediate yaml
        """
        index = 1
        if 'plcs' in self.data.keys():
            for plc in data["plcs"]:
                plc_ip = "192.168.1." + str(index)
                plc_mac = Mininet.randMac()
                plc_int = plc['name'] + "-eth0"

                # Store the data in self.data
                plc['local_ip'] = plc_ip
                plc['public_ip'] = plc_ip
                plc['mac'] = plc_mac
                plc['interface'] = plc_int
                plc['gateway'] = self.router_ip
                plc['switch_name'] = self.plc_switch
                plc['gateway_name'] = self.router
                plc['gateway_ip'] = self.router_ip
                index += 1

        # Generate scada data
        data['scada'] = {}
        data['scada']['name'] = "scada"
        data['scada']['local_ip'] = "192.168.2.1"
        data['scada']['public_ip'] = "192.168.2.1"
        data['scada']['interface'] = "scada-eth0"
        data['scada']['switch_name'] = self.scada_switch
        data['scada']['gateway_name'] = self.router
        data['scada']['gateway_ip'] = self.supervisor_ip

        if 'network_attacks' in self.data.keys():
            for attack in data['network_attacks']:
                target = next((plc for plc in data['plcs'] if plc['name'] == attack['target']), None)
                if attack['target'] == 'scada':
                    target = data['scada']
                if not target:
                    raise NoSuchPlc("The target plc {name} does not exist".format(name=attack['target']))
                if attack['target'] == 'scada':
                    attack['local_ip'] = "192.168.2." + str(index)
                else:
                    attack['local_ip'] = "192.168.1." + str(index)
                attack['public_ip'] = attack['local_ip']
                attack['mac'] = Mininet.randMac()
                attack['interface'] = attack['name'] + "-eth0"
                attack['gateway_name'] = target['gateway_name']
                attack['switch_name'] = target['switch_name']
                attack['gateway_ip'] = target['gateway_ip']
                index += 1

    def build(self):
        """
        Build the topology. This make nodes for every router, switch, plc and scada
        and add links to connect them.
        """
        # -- FIELD NETWORK -- #
        router_ip = self.router_ip + "/24"
        # Add a router to the network
        router = self.addNode('r0', cls=LinuxRouter, ip=router_ip)
        # Add a switch to the network
        switch = self.addSwitch('s1')
        self.addLink(switch, router, intfName2='r0-eth1', params2={'ip': router_ip})

        gateway = 'via ' + router_ip

        if 'plcs' in self.data.keys():
            # Add PLCs to the mininet network
            for idx, plc in enumerate(self.data['plcs']):
                plc_node = self.addHost(
                    plc['name'],
                    mac=plc['mac'],
                    ip=plc['local_ip'] + "/24",
                    defaultRoute=gateway)
                self.add_node_switch_link(plc_node, switch, plc)

        # -- SUPERVISOR NETWORK -- #
        supervisor_ip = self.supervisor_ip + "/24"
        # Add a switch for the supervisor network
        supervisor_switch = self.addSwitch("s2")
        # Link the router and the supervisor switch
        self.addLink(supervisor_switch, router, intfName2='r0-eth2', params2={'ip': supervisor_ip})
        # Create a supervisor gateway
        supervisor_gateway = "via " + supervisor_ip
        # Add a scada to the network
        scada = self.addHost('scada', ip=self.data['scada']['local_ip'] + "/24", defaultRoute=supervisor_gateway)
        # Add a link between the switch and the scada
        self.add_node_switch_link(scada, supervisor_switch, self.data['scada'])

        # -- ATACKERS -- #
        if 'network_attacks' in self.data.keys():
            # Add attackers to the mininet network
            for attack in self.data['network_attacks']:
                attacker = self.addHost(
                    attack['name'],
                    mac=attack['mac'],
                    ip=attack['local_ip'] + "/24",
                    defaultRoute='via ' + attack['gateway_ip'] + '/24')
                self.addLink(attacker, attack["switch_name"], intfName=attack['interface'])

        # -- PLANT -- #
        self.addHost('plant')

    def add_node_switch_link(self, node, switch, yaml_node_data):
        """
        This function adds the link between the node and its switch,
        and configures network losses/delays as nececarry

        :param switch: The switch to link
        :param node: The node to link
        :param yaml_node_data: The yaml data for the given node
        """
        # TODO: figure out which of these parameters are necessary
        link_params = dict(bw=1000, delay="0ms", loss=0, max_queue_size=1000, use_htb=True)
        # If delays enabled
        if 'network_delay_data' in self.data:
            # If delay value for this node defined
            if self.data['network_delay_values'][yaml_node_data['name']]:
                link_params['delay'] = self.data['network_delay_values'][yaml_node_data['name']]
        # If losses enabled
        if 'network_loss_data' in self.data:
            # If loss value for this node defined
            if self.data['network_loss_values'][yaml_node_data['name']]:
                link_params['loss'] = self.data['network_loss_values'][yaml_node_data['name']]
        # Add link with network parameters
        self.addLink(node, switch, intfName=yaml_node_data['interface'], **link_params)

    def setup_network(self, net):
        """
        Here all the rules are applied to make the routers function like routers

        :param net: The initiated net to setup.
        :type net: Mininet
        """
        # Enable forwarding on router r0
        net.get('r0').cmd('sysctl net.ipv4.ip_forward=1')

        # Set the default gateway of the PLCs
        if 'plcs' in self.data.keys():
            for plc in self.data['plcs']:
                net.get(plc['name']).cmd('route add default gw {ip}'.format(ip=plc['gateway']))

        # Set the default gateway of the SCADA
        net.get('scada').cmd('route add default gw ' + self.supervisor_ip)

        # Set default gateway for the attackers
        if 'network_attacks' in self.data.keys():
            for attack in self.data['network_attacks']:
                net.get(attack['name']).cmd('route add default gw {ip}'.format(ip=attack['gateway_ip']))

        # Set interface ip on router for scada
        net.get('r0').cmd('ifconfig r0-eth2 {ip}'.format(ip=self.supervisor_ip))
        net.get('r0').waitOutput()
