import sys
import time

import pytest
import yaml
from mininet.net import Mininet
from mininet.link import TCLink
from netaddr import IPNetwork, IPAddress

from dhalsim.python2.topo.simple_topo import SimpleTopo


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


@pytest.fixture
def unmodified_yaml(tmpdir):
    dict = {'plcs': [{'name': 'PLC1', }, {'name': 'PLC2', }, ],
            'network_attacks': [{'name': 'attack1', 'target': 'PLC2'}, {'name': 'attack2', 'target': 'PLC2'},
                                {'name': 'attack3', 'target': 'PLC1'}, {'name': 'attack4', 'target': 'scada'}, ]}
    file = tmpdir.join('intermediate.yaml')
    with file.open(mode='w') as intermediate_yaml:
        yaml.dump(dict, intermediate_yaml)
    return file


@pytest.fixture
def topo(unmodified_yaml):
    return SimpleTopo(unmodified_yaml)


@pytest.fixture
def net(topo):
    net = Mininet(topo=topo, autoSetMacs=True, link=TCLink)
    net.start()
    topo.setup_network(net)
    time.sleep(0.2)
    yield net
    net.stop()


@pytest.mark.integrationtest
@pytest.mark.parametrize('host1, host2',
                         [('r0', 'PLC1'), ('r0', 'PLC2'), ('r0', 'scada'), ('r0', 'attack1'), ('r0', 'attack2'),
                          ('r0', 'attack3'), ('r0', 'attack4'), ('PLC1', 'attack1'), ('PLC1', 'attack2'),
                          ('PLC1', 'attack3'), ('PLC1', 'attack4'), ('PLC2', 'attack1'), ('PLC2', 'attack2'),
                          ('PLC2', 'attack3'), ('PLC2', 'attack4'), ('scada', 'attack1'), ('scada', 'attack2'),
                          ('scada', 'attack3'), ('scada', 'attack4')])
@pytest.mark.flaky(max_runs=3)
def test_ping(net, host1, host2):
    assert net.ping(hosts=[net.get(host1), net.get(host2)]) == 0.0


@pytest.mark.integrationtest
@pytest.mark.parametrize('host1, host2',
                         [('r0', 's1'), ('r0', 's2'), ('s1', 'PLC1'), ('s1', 'PLC2'), ('s1', 'attack1'),
                          ('s1', 'attack2'), ('s1', 'attack3'), ('s2', 'scada'), ('s2', 'attack4')])
def test_links(net, host1, host2):
    assert net.linksBetween(net.get(host1), net.get(host2)) != []


@pytest.mark.integrationtest
def test_number_of_links(net):
    assert len(net.links) == 9


@pytest.mark.integrationtest
@pytest.mark.parametrize('hosts',
                         [['PLC1', 'PLC2', 'attack1', 'attack2', 'attack3'], ['scada', 'attack4']])
def test_double_ips(net, hosts):
    ip_list = [net.get(node).IP() for node in hosts]
    assert len(ip_list) == len(set(ip_list))


@pytest.mark.integrationtest
@pytest.mark.parametrize('host, subnet',
                         [('PLC1', "192.168.1.0/24"), ('PLC2', "192.168.1.0/24"), ('attack1', "192.168.1.0/24"),
                          ('attack2', "192.168.1.0/24"), ('attack3', "192.168.1.0/24"), ('scada', "192.168.2.0/24"),
                          ('attack4', "192.168.2.0/24")])
def test_subnet_ips(net, host, subnet):
    assert IPAddress(net.get(host).IP()) in IPNetwork(subnet)


@pytest.mark.integrationtest
@pytest.mark.parametrize("server, client, server_ip",
                         [("PLC1", "r0", "192.168.1.1"), ("PLC2", "r0", "192.168.1.2"),
                          # ("PLC1", "PLC2", "192.168.1.1"), ("PLC2", "PLC1", "192.168.1.2"),
                          ("PLC1", "scada", "192.168.1.1"), ("PLC2", "scada", "192.168.1.2")])
@pytest.mark.flaky(max_runs=3)
def test_reachability(net, server, client, server_ip):
    net.get(server).cmd("echo 'test' | netcat -l 44818 &")
    time.sleep(0.1)
    response = net.get(client).cmd("wget -qO - {ip}:44818".format(ip=server_ip))
    assert response.rstrip() == "test"
