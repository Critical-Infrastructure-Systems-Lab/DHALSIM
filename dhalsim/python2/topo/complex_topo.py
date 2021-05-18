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
    """
    A class for a simple mininet topology
    """

    def __init__(self, intermediate_yaml_path):
        """
        Initialize a simple mininet topology

        :param intermediate_yaml_path: The path of the intermediate.yaml file
        """

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

        # Generate PLC data and write back to file (mac addresses, ip addresses, interface names, ...)
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
        """
        Build the mininet topology
        """

        # Todo change maartens comments

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
        # Enable forwarding on router r0
        net.get('r0').cmd('sysctl net.ipv4.ip_forward=1')

        # Set the default gateway of the PLCs
        if 'plcs' in self.data.keys():
            for plc in self.data['plcs']:
                # Add the plcs router as default gateway to the plc
                net.get(plc['name']).cmd('route add default gw ' + plc['gateway_ip'])
                # Set ips on the provider router for every interface
                net.get("r0").cmd('ifconfig ' + plc['provider_interface'] + ' ' + plc[
                    "provider_ip"] + ' netmask 255.255.255.0')

                # net.get(plc['gateway_name']).cmd('sysctl net.ipv4.ip_forward=1')
                net.get(plc['gateway_name']).cmd('ifconfig ' + plc['gateway_name'] + '-eth1 192.168.1.254')

                net.get(plc['gateway_name']).cmd(
                    'ifconfig ' + plc['gateway_name'] + '-eth1 ' + plc['gateway_ip'])

                net.get(plc['gateway_name']).cmd('sudo iptables -A FORWARD -o '+plc['gateway_name']+'-eth1 -i '+plc['gateway_name']+'-eth0 -s '+ plc['local_ip'] +' -m conntrack --ctstate NEW -j ACCEPT')
                net.get(plc['gateway_name']).cmd('sudo iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT')
                net.get(plc['gateway_name']).cmd('sudo iptables -t nat -F POSTROUTING')
                net.get(plc['gateway_name']).cmd('sudo iptables -t nat -A POSTROUTING -o '+plc['gateway_name']+'-eth0  -j MASQUERADE')
                net.get(plc['gateway_name']).cmd('sudo sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"')

                net.get(plc['gateway_name']).cmd('route add default gw ' + plc['provider_ip'])

                net.get(plc['gateway_name']).cmd('sudo iptables -A PREROUTING -t nat -i ' + plc[
                    'gateway_name'] + '-eth0 -p tcp --dport ' + self.cpppo_port + ' -j DNAT --to ' +
                                                 plc['local_ip'] + ':' + self.cpppo_port)

                net.get(plc['gateway_name']).cmd('sudo iptables -A FORWARD -p tcp -d ' + plc[
                    'local_ip'] + ' --dport ' + self.cpppo_port + ' -j ACCEPT')

                net.get(plc['gateway_name']).popen('tcpdump -i any -w ' + str(Path(self.data["output_path"])/(plc['gateway_name']+".pcap")), stderr=sys.stderr, stdout=sys.stdout)

            net.get('r0').popen('tcpdump -i r0-eth0 -w ' + str(
                Path(self.data["output_path"]) / ('r0-eth0' + ".pcap")), stderr=sys.stderr, stdout=sys.stdout)
            net.get('r0').popen('tcpdump -i r0-eth1 -w ' + str(
                Path(self.data["output_path"]) / ('r0-eth1' + ".pcap")), stderr=sys.stderr, stdout=sys.stdout)

        # # Set the default gateway of the SCADA
        # net.get('scada').cmd('route add default gw ' + self.supervisor_ip)
