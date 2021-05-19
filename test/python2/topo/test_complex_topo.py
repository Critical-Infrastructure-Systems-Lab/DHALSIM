import sys
import time

import pytest
import yaml
from mininet.net import Mininet
from mininet.link import TCLink

from dhalsim.python2.topo.complex_topo import ComplexTopo


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
    yield net
    net.stop()


@pytest.mark.parametrize("host1,host2",
                         [("r0", "r1"), ("r0", "r2"), ("r1", "PLC1"), ("r2", "PLC2")])
def test_ping(net, host1, host2):
    assert net.ping(hosts=[net.get(host1), net.get(host2)]) == 0.0


def test_port_forward_1(net):
    net.get("PLC1").cmd("echo 'test' | netcat -q 1 -l 44818 &")
    response = net.get("r0").cmd("wget -qO - 10.0.1.1:44818")
    assert response.rstrip() == "test"


def test_port_forward_2(net):
    net.get("PLC2").cmd("echo 'test' | netcat -q 1 -l 44818 &")
    response = net.get("r0").cmd("wget -qO - 10.0.2.1:44818")
    assert response.rstrip() == "test"
