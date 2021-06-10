import sys
import time

import pytest
import yaml
from mininet.net import Mininet
from mininet.link import TCLink

from dhalsim.python2.topo.complex_topo import ComplexTopo


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


@pytest.fixture
def unmodified_yaml(tmpdir):
    dict = {"plcs": [{"name": "PLC1", }, {"name": "PLC2", }, ], }
    file = tmpdir.join("intermediate.yaml")
    with file.open(mode='w') as intermediate_yaml:
        yaml.dump(dict, intermediate_yaml)
    return file


@pytest.fixture
def topo(unmodified_yaml):
    return ComplexTopo(unmodified_yaml)


@pytest.fixture
def net(topo):
    net = Mininet(topo=topo, autoSetMacs=False, link=TCLink)
    net.start()
    topo.setup_network(net)
    time.sleep(0.2)
    yield net
    net.stop()


@pytest.mark.integrationtest
@pytest.mark.parametrize("host1, host2",
                         [("r0", "r1"), ("r0", "r2"), ("r0", "r3"), ("r2", "PLC1"), ("r3", "PLC2"),
                          ("r1", "scada")])
@pytest.mark.flaky(max_runs=3)
def test_ping(net, host1, host2):
    assert net.ping(hosts=[net.get(host1), net.get(host2)]) == 0.0


@pytest.mark.integrationtest
@pytest.mark.parametrize("host1, host2",
                         [("r0", "r1"), ("r0", "r2"), ("r0", "r3"), ("r1", "s1"), ("r2", "s2"),
                          ("r3", "s3"), ("s2", "PLC1"), ("s3", "PLC2"),
                          ("s1", "scada")])
def test_links(net, host1, host2):
    print(net.linksBetween(net.get(host1), net.get(host2)))
    assert net.linksBetween(net.get(host1), net.get(host2)) != []


@pytest.mark.integrationtest
@pytest.mark.parametrize('host1, host2, mac1, mac2',
                         [('r0', 'r1', 'aa:bb:cc:dd:00:', 'aa:bb:cc:dd:04:'),
                          ('r0', 'r2', 'aa:bb:cc:dd:00:', 'aa:bb:cc:dd:04:'),
                          ('r0', 'r3', 'aa:bb:cc:dd:00:', 'aa:bb:cc:dd:04:'),
                          ('r1', 's1', 'aa:bb:cc:dd:03:', ''),
                          ('r2', 's2', 'aa:bb:cc:dd:03:', ''),
                          ('r3', 's3', 'aa:bb:cc:dd:03:', ''),
                          ('s2', 'PLC1', '', 'aa:bb:cc:dd:02:'),
                          ('s3', 'PLC2', '', 'aa:bb:cc:dd:02:'),
                          ('s1', 'scada', '', 'aa:bb:cc:dd:01:')])
def test_mac_prefix(net, host1, host2, mac1, mac2):
    links = net.linksBetween(net.get(host1), net.get(host2))
    assert links != []
    link = links[0]
    full_mac_1 = link.intf1.MAC().lower()
    full_mac_2 = link.intf2.MAC().lower()
    assert (full_mac_1.startswith(mac1.lower()) and full_mac_2.startswith(mac2.lower())) or (
            full_mac_1.startswith(mac2.lower()) and full_mac_2.startswith(mac1.lower()))


@pytest.mark.integrationtest
def test_number_of_links(net):
    assert len(net.links) == 9


@pytest.mark.integrationtest
@pytest.mark.parametrize("server, client, server_ip",
                         [("PLC1", "r0", "10.0.2.1"), ("PLC2", "r0", "10.0.3.1"),
                          ("PLC1", "PLC2", "10.0.2.1"), ("PLC2", "PLC1", "10.0.3.1"),
                          ("PLC1", "scada", "10.0.2.1"), ("PLC2", "scada", "10.0.3.1")])
@pytest.mark.flaky(max_runs=3)
def test_reachability(net, server, client, server_ip):
    net.get(server).cmd("echo 'test' | nc -q1 -l 44818 &")
    time.sleep(0.1)
    response = net.get(client).cmd("wget -qO - {ip}:44818".format(ip=server_ip))
    assert response.rstrip() == "test"
