from mininet.topo import Topo
from mininet.node import Node
from mininet.net import Mininet
import yaml


class LinuxRouter(Node):
    """A node with IP forwarding enabled"""

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_foward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_foward=0')


class ComplexTopo(Topo):
    """
    This class represents a complex topology. A complex topology is a network topology where every
    PLC and the SCADA have their own router and switch. To communicate, port forwarding is done.

    This class will generate ip addresses, mac addresses etc. and write them back to the
    intermediate yaml file. Then, it will use that file to create all the routers, switches
    and nodes. After that, iptables rules and routes will be setup.


    :param intermediate_yaml_path: The path to the intermediate yaml file. Here will also be writen to.
    :type intermediate_yaml_path: Path
    """

    def __init__(self, intermediate_yaml_path):
        # Set variables
        self.router_ip = "10.0.1.254"
        self.supervisor_ip = "10.0.2.254"
        self.local_plc_ips = "192.168.1.1"
        self.local_router_ips = "192.168.1.254"
        self.cpppo_port = "44818"

        # Load the data from the YAML file
        self.intermediate_yaml_path = intermediate_yaml_path
        with self.intermediate_yaml_path.open(mode='r') as intermediate_yaml:
            self.data = yaml.safe_load(intermediate_yaml)

        # Generate PLC and SCADA data and write back to file
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
        plcs = data["plcs"]
        index = 1
        for plc in plcs:
            # Store the data in self.data
            plc['local_ip'] = self.local_plc_ips
            plc['public_ip'] = "10.0." + str(index) + ".1"
            plc['provider_ip'] = "10.0." + str(index) + ".254"
            plc['mac'] = Mininet.randMac()
            plc['interface'] = plc['name'] + "-eth0"
            plc['provider_interface'] = "r0-eth" + str(index)
            plc['gateway_name'] = "r" + str(index)
            plc['switch_name'] = "s" + str(index)
            plc['gateway_ip'] = self.local_router_ips
            index += 1

        data["scada"] = {}
        scada = data["scada"]
        scada['name'] = "scada"
        scada['local_ip'] = self.local_plc_ips
        scada['public_ip'] = "10.0." + str(index) + ".1"
        scada['provider_ip'] = "10.0." + str(index) + ".254"
        scada['mac'] = Mininet.randMac()
        scada['interface'] = scada['name'] + "-eth0"
        scada['provider_interface'] = "r0-eth" + str(index)
        scada['gateway_name'] = "r" + str(index)
        scada['switch_name'] = "s" + str(index)
        scada['gateway_ip'] = self.local_router_ips

    def build(self, *args, **params ):
        """
        Build the topology. This make nodes for every router, switch, plc and scada
        and add links to connect them.
        """

        # -- PROVIDER NETWORK -- #
        provider_router = self.addNode('r0', cls=LinuxRouter, ip=self.router_ip + "/24")

        # -- PLC NETWORK -- #
        if 'plcs' in self.data.keys():
            # Add PLCs to the mininet network
            for plc in self.data['plcs']:
                self.build_for_node(plc, provider_router)

        # -- SCADA -- #
        scada = self.data["scada"]

        self.build_for_node(scada, provider_router)

        # -- PLANT -- #
        self.addHost('plant')

    def build_for_node(self, node, provider_router):
        """
        This build a subnetwork for one node, and connects it to the provider.

        :param node: the data of the node to build the piece of the network for
        :param provider_router: the router to connect to

        """
        node_router = self.addNode(node['gateway_name'], cls=LinuxRouter,
                                   ip=node['public_ip'] + "/24")
        node_switch = self.addSwitch(node['switch_name'])
        node_node = self.addHost(
            node['name'],
            mac=node['mac'],
            ip=node['local_ip'] + "/24",
            defaultRoute='via ' + node['gateway_ip'] + '/24')
        self.addLink(node_router, provider_router, intfName2=node['provider_interface'],
                     params2={'ip': node['provider_ip'] + "/24"})
        self.addLink(node_switch, node_router, params2={'ip': node['gateway_ip'] + "/24"})
        self.addLink(node_node, node_switch, intfName=node['interface'])

    def setup_network(self, net):
        """
        Here all the iptables rules and routes are applied to enable the port forwarding
        of the cpppo port.

        :param net: The initiated net to setup.
        :type net: Mininet

        """
        # Enable ip forwarding on provider router
        provider = net.get('r0')
        provider.cmd('sysctl net.ipv4.ip_forward=1')

        if 'plcs' in self.data.keys():
            for plc_data in self.data['plcs']:
                self.setup_network_for_node(net, plc_data, provider)

        scada_data = self.data['scada']

        self.setup_network_for_node(net, scada_data, provider)

    def setup_network_for_node(self, net, node_data, provider_router):
        """
        This applies the rules for one node.

        :param net: The initiated net to setup.
        :type net: Mininet
        :param node_data:  the data of the node to setup the piece of the network for
        :param provider_router: the router this part of the network connects to

        """
        node = net.get(node_data['name'])
        gateway = net.get(node_data['gateway_name'])
        # Add the plcs gateway router as default gateway to the plc
        node.cmd('route add default gw {ip}'.format(ip=node_data['gateway_ip']))
        # Set ips on the provider router for every interface
        provider_router.cmd('ifconfig {interface} {ip} netmask 255.255.255.0'.format(
            interface=node_data['provider_interface'], ip=node_data["provider_ip"]))
        # Set ip on gateway on plc sides interface
        gateway.cmd(
            'ifconfig {name}-eth1 192.168.1.254'.format(name=node_data['gateway_name']))
        # Set ip on gateway on the provider sides interface
        gateway.cmd('ifconfig {name}-eth1 {ip}'.format(name=node_data['gateway_name'],
                                                       ip=node_data['gateway_ip']))
        # Enable ip forwarding on gateway router
        gateway.cmd('sysctl net.ipv4.ip_forward=1')
        # Add provider router as default gateway to the plcs gateway router
        gateway.cmd('route add default gw {ip}'.format(ip=node_data['provider_ip']))

        # TODO what do these do? they are not necessary yet
        # gateway.cmd(
        #     'iptables -A FORWARD -o {name}-eth1 -i {name}-eth0 -s {ip} -m conntrack --ctstate NEW -j ACCEPT'.format(
        #         name=node_data['gateway_name'], ip=node_data['local_ip']))
        # gateway.cmd(
        #     'iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT')

        # Masquerade the from ip when forwarding a request from a plc to the provider
        gateway.cmd('iptables -t nat -F POSTROUTING')
        gateway.cmd('iptables -t nat -A POSTROUTING -o {name}-eth0  -j MASQUERADE'.format(
            name=node_data['gateway_name']))
        # Portforwarding the cpppo port on the gateway to the plc
        gateway.cmd(
            'iptables -A PREROUTING -t nat -i {name}-eth0 -p tcp --dport {port} -j DNAT --to {ip}:{port}'.format(
                name=node_data['gateway_name'], port=self.cpppo_port,
                ip=node_data['local_ip']))
        gateway.cmd('iptables -A FORWARD -p tcp -d {ip} --dport {port} -j ACCEPT'.format(
            ip=node_data['local_ip'], port=self.cpppo_port))
