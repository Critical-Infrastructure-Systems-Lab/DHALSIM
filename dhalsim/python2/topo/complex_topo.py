import sys
from pathlib import Path

from mininet.topo import Topo
from mininet.node import Node
from mininet.net import Mininet
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

        # Generate PLC data and write back to file
        self.generate_plc_data(self.data['plcs'])
        with self.intermediate_yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(self.data, intermediate_yaml)

        # Initialize mininet topology
        Topo.__init__(self)

    def generate_plc_data(self, plcs):
        for idx, plc in enumerate(plcs):
            # Store the data in self.data
            plc['local_ip'] = self.local_plc_ips
            plc['public_ip'] = "10.0." + str(idx + 1) + ".1"
            plc['provider_ip'] = "10.0." + str(idx + 1) + ".254"
            plc['mac'] = Mininet.randMac()
            plc['interface'] = plc['name'] + "-eth0"
            plc['provider_interface'] = "r0-eth" + str(idx)
            plc['gateway_name'] = "r" + str(idx + 1)
            plc['switch_name'] = "s" + str(idx + 1)
            plc['gateway_ip'] = self.local_router_ips

    def build(self):

        # -- FIELD NETWORK -- #
        # Add a router to the network
        provider_router = self.addNode('r0', cls=LinuxRouter, ip=self.router_ip + "/24")

        # -- FIELD NETWORK -- #
        if 'plcs' in self.data.keys():
            # Add PLCs to the mininet network
            for plc in self.data['plcs']:
                plc_router = self.addNode(plc['gateway_name'], cls=LinuxRouter,
                                          ip=plc['public_ip'] + "/24")

                plc_switch = self.addSwitch(plc['switch_name'])

                plc_node = self.addHost(
                    plc['name'],
                    mac=plc['mac'],
                    ip=plc['local_ip'] + "/24",
                    defaultRoute='via ' + plc['gateway_ip'] + '/24')

                self.addLink(plc_router, provider_router,
                             params2={'ip': plc['provider_ip'] + "/24"})
                self.addLink(plc_switch, plc_router, params2={'ip': plc['gateway_ip'] + "/24"})
                self.addLink(plc_node, plc_switch, intfName=plc['interface'])

        # # # -- SUPERVISOR NETWORK -- #
        # supervisor_ip = self.supervisor_ip + "/24"
        # # # Add a switch for the supervisor network
        # supervisor_switch = self.addSwitch("s" + str(router_number))
        # # # Link the router and the supervisor switch
        # self.addLink(supervisor_switch, router, params2={'ip': supervisor_ip})
        # # # Create a supervisor gateway
        # supervisor_gateway = "via " + supervisor_ip
        # # # Add a scada to the network
        # scada = self.addHost('scada', ip="192.168.2.1/24", defaultRoute=supervisor_gateway)
        # # # Add a link between the switch and the scada
        # self.addLink(supervisor_switch, scada)
        #
        # # -- PLANT -- #
        self.addHost('plant')

    def setup_network(self, net):
        # Enable ip forwarding on provider router
        provider = net.get('r0')
        provider.cmd('sysctl net.ipv4.ip_forward=1')

        if 'plcs' in self.data.keys():
            for plc_data in self.data['plcs']:
                plc = net.get(plc_data['name'])
                gateway = net.get(plc_data['gateway_name'])

                # Add the plcs gateway router as default gateway to the plc
                plc.cmd('route add default gw {ip}'.format(ip=plc_data['gateway_ip']))

                # Set ips on the provider router for every interface
                provider.cmd('ifconfig {interface} {ip} netmask 255.255.255.0'.format(
                    interface=plc_data['provider_interface'], ip=plc_data["provider_ip"]))

                # Set ip on gateway on plc sides interface
                gateway.cmd(
                    'ifconfig {name}-eth1 192.168.1.254'.format(name=plc_data['gateway_name']))

                # Set ip on gateway on the provider sides interface
                gateway.cmd('ifconfig {name}-eth1 {ip}'.format(name=plc_data['gateway_name'],
                                                               ip=plc_data['gateway_ip']))

                # Enable ip forwarding on gateway router
                gateway.cmd('sysctl net.ipv4.ip_forward=1')

                # Add provider router as default gateway to the plcs gateway router
                gateway.cmd('route add default gw {ip}'.format(ip=plc_data['provider_ip']))

                # TODO what do these do? they are not necessary yet
                # gateway.cmd(
                #     'iptables -A FORWARD -o {name}-eth1 -i {name}-eth0 -s {ip} -m conntrack --ctstate NEW -j ACCEPT'.format(
                #         name=plc_data['gateway_name'], ip=plc_data['local_ip']))
                # gateway.cmd(
                #     'iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT')

                # Masquerade the from ip when forwarding a request from a plc to the provider
                gateway.cmd('iptables -t nat -F POSTROUTING')
                gateway.cmd('iptables -t nat -A POSTROUTING -o {name}-eth0  -j MASQUERADE'.format(
                    name=plc_data['gateway_name']))

                # Portforwarding the cpppo port on the gateway to the plc
                gateway.cmd(
                    'iptables -A PREROUTING -t nat -i {name}-eth0 -p tcp --dport {port} -j DNAT --to {ip}:{port}'.format(
                        name=plc_data['gateway_name'], port=self.cpppo_port,
                        ip=plc_data['local_ip']))
                gateway.cmd('iptables -A FORWARD -p tcp -d {ip} --dport {port} -j ACCEPT'.format(
                    ip=plc_data['local_ip'], port=self.cpppo_port))

        # # Set the default gateway of the SCADA
        # net.get('scada').cmd('route add default gw ' + self.supervisor_ip)
