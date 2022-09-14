from mininet.topo import Topo
from mininet.node import Node
from mininet.net import Mininet
import yaml
from pathlib import Path
import sys
import signal


class Error(Exception):
    """Base class for exceptions in this module."""


class NoSuchPlc(Error):
    """Raised when an attack targets a PLC that does not exist"""


class TooManyNodes(Error):
    """Raised when there will be too many nodes in the network"""


class LinuxRouter(Node):
    """A node with IP forwarding enabled"""

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')


    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')

    @staticmethod
    def end_process(process):
        """
        End a process.

        :param process: the process to end
        """
        process.terminate()

        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            process.wait()
        if process.poll() is None:
            process.terminate()
        if process.poll() is None:
            process.kill()


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

        self.check_amount_of_nodes(self.data)

        # Generate PLC and SCADA data and write back to file
        self.generate_data(self.data)
        with self.intermediate_yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(self.data, intermediate_yaml)

        # Initialize mininet topology
        Topo.__init__(self)

        self.router_processes = []

    @staticmethod
    def check_amount_of_nodes(data):
        """
        Check if there are not more then 250 plcs and network attacks.
        This would cause trouble with assigning IP and MAC addresses.

        :param data: the data to check on
        :raise TooManyNodes: When there are more then 250 nodes in the network
        """
        raise_message = "There are too many nodes in the network. Only 250 nodes are supported."

        if 'plcs' in data:
            n_plcs = len(data["plcs"])
            if n_plcs > 250:
                raise TooManyNodes(raise_message)
            if 'network_attacks' in data and n_plcs + len(data['network_attacks']) > 250:
                raise TooManyNodes(raise_message)
        elif 'network_attacks' in data and len(data['network_attacks']) > 250:
            raise TooManyNodes(raise_message)

    def generate_data(self, data):
        """
        Generate all the ips, interfaces, etc. from every plc and the scada.
        These are then applied when building the topo

        :param data: the dict resulting from a dump of the intermediate yaml
        """
        index = 1

        data["scada"] = {}
        scada = data["scada"]
        scada['name'] = "scada"
        scada['local_ip'] = self.local_plc_ips
        scada['public_ip'] = "10.0." + str(index) + ".1"
        scada['provider_ip'] = "10.0." + str(index) + ".254"
        scada['provider_mac'] = 'AA:BB:CC:DD:00:' + "{:02x}".format(index)
        scada['mac'] = 'AA:BB:CC:DD:01:' + "{:02x}".format(index)
        scada['interface'] = scada['name'] + "-eth0"
        scada['provider_interface'] = "r0-eth" + str(index)
        scada['gateway_name'] = "r" + str(index)
        scada['switch_name'] = "s" + str(index)
        scada['gateway_inbound_mac'] = 'AA:BB:CC:DD:03:' + "{:02x}".format(index)
        scada['gateway_outbound_mac'] = 'AA:BB:CC:DD:04:' + "{:02x}".format(index)
        scada['gateway_ip'] = self.local_router_ips

        index += 1

        if 'plcs' in self.data.keys():
            for plc in data["plcs"]:
                # Store the data in self.data
                plc['local_ip'] = self.local_plc_ips
                plc['public_ip'] = "10.0." + str(index) + ".1"
                plc['provider_ip'] = "10.0." + str(index) + ".254"
                plc['mac'] = 'AA:BB:CC:DD:02:' + "{:02x}".format(index)
                plc['interface'] = plc['name'] + "-eth0"
                plc['provider_interface'] = "r0-eth" + str(index)
                plc['provider_mac'] = 'AA:BB:CC:DD:00:' + "{:02x}".format(index)
                plc['gateway_name'] = "r" + str(index)
                plc['switch_name'] = "s" + str(index)
                plc['gateway_ip'] = self.local_router_ips
                plc['gateway_inbound_mac'] = 'AA:BB:CC:DD:03:' + "{:02x}".format(index)
                plc['gateway_outbound_mac'] = 'AA:BB:CC:DD:04:' + "{:02x}".format(index)
                index += 1

        if 'network_attacks' in self.data.keys():
            for attack in data['network_attacks']:

                # This is the only valid target of this attack
                if attack['type'] == 'unconstrained_blackbox_concealment_mitm':
                    target = data['scada']
                    attack['target'] = 'scada'
                else:
                    target = next((plc for plc in data['plcs'] if plc['name'] == attack['target']), None)
                    if attack['target'].lower() == 'scada':
                        target = data['scada']

                if not target:
                    raise NoSuchPlc("The target plc {name} does not exist".format(name=attack['target']))
                attack['local_ip'] = "192.168.1." + str(index)
                attack['public_ip'] = target['public_ip']
                attack['provider_ip'] = target['provider_ip']
                attack['mac'] = 'AA:BB:CC:DD:05:' + "{:02x}".format(index)
                attack['interface'] = attack['name'][0:9] + "-eth0"
                attack['provider_interface'] = target['provider_interface']
                attack['provider_mac'] = target['provider_mac']
                attack['gateway_name'] = target['gateway_name']
                attack['switch_name'] = target['switch_name']
                attack['gateway_ip'] = target['gateway_ip']
                attack['gateway_inbound_mac'] = target['gateway_inbound_mac']
                attack['gateway_outbound_mac'] = target['gateway_outbound_mac']
                index += 1

    def build(self, *args, **params):
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

        # -- ATACKERS -- #
        if 'network_attacks' in self.data.keys():
            # Add attackers to the mininet network
            for attack in self.data['network_attacks']:
                attacker = self.addHost(
                    attack['name'][0:9],
                    mac=attack['mac'],
                    ip=attack['local_ip'] + "/24",
                    defaultRoute='via ' + attack['gateway_ip'] + '/24')
                self.addLink(attacker, attack["switch_name"], intfName=attack['interface'])

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
                     params2={'ip': node['provider_ip'] + "/24"},
                     addr1=node['gateway_outbound_mac'],
                     addr2=node['provider_mac'])
        self.addLink(node_switch, node_router, params2={'ip': node['gateway_ip'] + "/24"},
                     addr2=node['gateway_inbound_mac'])
        self.add_node_switch_link(node_node, node_switch, node)

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
        # If delays enabled and delay value for this node defined
        if 'network_delay_data' in self.data and\
                self.data['network_delay_values'][yaml_node_data['name']]:
            link_params['delay'] = self.data['network_delay_values'][yaml_node_data['name']]
        # If losses enabled and loss value for this node defined
        if 'network_loss_data' in self.data and\
                self.data['network_loss_values'][yaml_node_data['name']]:
            link_params['loss'] = self.data['network_loss_values'][yaml_node_data['name']]
        # Add link with network parameters
        self.addLink(node, switch, intfName=yaml_node_data['interface'],
                     addr1=yaml_node_data['mac'],
                     **link_params
                     )

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

        # Set default gateway for the attackers
        if 'network_attacks' in self.data.keys():
            for attack in self.data['network_attacks']:
                node = net.get(attack['name'][0:9])
                node.cmd('route add default gw {ip}'.format(ip=attack['gateway_ip']))

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