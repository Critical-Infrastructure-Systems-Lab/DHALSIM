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
    net = Mininet(topo=topo, autoSetMacs=True, link=TCLink)
    net.start()
    topo.setup_network(net)
    time.sleep(0.2)
    yield net
    net.stop()


@pytest.mark.integrationtest
@pytest.mark.parametrize("host1, host2",
                         [("r0", "r1"), ("r0", "r2"), ("r0", "r3"), ("r1", "PLC1"), ("r2", "PLC2"),
                          ("r3", "scada")])
def test_ping(net, host1, host2):
    assert net.ping(hosts=[net.get(host1), net.get(host2)]) == 0.0


@pytest.mark.integrationtest
@pytest.mark.parametrize("host1, host2",
                         [("r0", "r1"), ("r0", "r2"), ("r0", "r3"), ("r1", "s1"), ("r2", "s2"),
                          ("r3", "s3"), ("s1", "PLC1"), ("s2", "PLC2"),
                          ("s3", "scada")])
def test_links(net, host1, host2):
    assert net.linksBetween(net.get(host1), net.get(host2)) != []


@pytest.mark.integrationtest
def test_number_of_links(net):
    assert len(net.links) == 9


@pytest.mark.integrationtest
@pytest.mark.parametrize("server, client, server_ip",
                         [("PLC1", "r0", "10.0.1.1"), ("PLC2", "r0", "10.0.2.1"),
                          ("PLC1", "PLC2", "10.0.1.1"), ("PLC2", "PLC1", "10.0.2.1"),
                          ("PLC1", "scada", "10.0.1.1"), ("PLC2", "scada", "10.0.2.1")])
def test_reachability(net, server, client, server_ip):
    net.get(server).cmd("echo 'test' | nc -q1 -l 44818 &")
    time.sleep(0.1)
    response = net.get(client).cmd("wget -qO - {ip}:44818".format(ip=server_ip))
    assert response.rstrip() == "test"
