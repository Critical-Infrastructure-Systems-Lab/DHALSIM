from dhalsim.python2.topo.simple_topo import SimpleTopo
from mininet.net import Mininet
from mininet.link import TCLink
import pytest
import yaml


@pytest.fixture
def unmodified_dict():
    return {"plcs": [{"name": "PLC1", }, {"name": "PLC2", }, ], }


@pytest.fixture
def filled_dict():
    return {'scada': {'interface': 'scada-eth0', 'ip': '192.168.2.1', 'name': 'scada'},
            'plcs': [{'public_ip': '192.168.1.1', 'mac': '00:1D:9C:C7:B0:70', 'name': 'PLC1',
                      'local_ip': '192.168.1.1', 'interface': 'PLC1-eth0',
                      'gateway': '192.168.1.254'},
                     {'public_ip': '192.168.1.2', 'mac': '00:1D:9C:C7:B0:70', 'name': 'PLC2',
                      'local_ip': '192.168.1.2', 'interface': 'PLC2-eth0',
                      'gateway': '192.168.1.254'}]}


@pytest.fixture
def topo_fixture(mocker, tmpdir, unmodified_dict):
    mocker.patch('mininet.net.Mininet.randMac', return_value="00:1D:9C:C7:B0:70")

    c = tmpdir.join("intermediate.yaml")
    with c.open(mode='w') as intermediate_yaml:
        yaml.dump(unmodified_dict, intermediate_yaml)

    return SimpleTopo(c)


def test_writeback_yaml(tmpdir, topo_fixture, filled_dict):
    with tmpdir.join("intermediate.yaml").open(mode='r') as intermediate_yaml:
        dump = yaml.safe_load(intermediate_yaml)
    assert dump == filled_dict


def test_host_amount_network(topo_fixture):
    # Expecting 4 hosts; 2 PLCs, a router, a scada and a plant
    assert len(topo_fixture.hosts()) == 5


def test_host_names(topo_fixture):
    assert topo_fixture.hosts()[0] == 'PLC1'
    assert topo_fixture.hosts()[1] == 'PLC2'
    assert topo_fixture.hosts()[2] == 'plant'
    assert topo_fixture.hosts()[3] == 'r0'
    assert topo_fixture.hosts()[4] == 'scada'


def test_host_ips(topo_fixture):
    print(topo_fixture.nodeInfo('PLC1'))
    assert topo_fixture.nodeInfo('PLC1')['ip'] == '192.168.1.1/24'
    assert topo_fixture.nodeInfo('PLC2')['ip'] == '192.168.1.2/24'
    assert topo_fixture.nodeInfo('r0')['ip'] == '192.168.1.254/24'
    assert topo_fixture.nodeInfo('scada')['ip'] == '192.168.2.1/24'


def test_host_gateways(topo_fixture):
    assert topo_fixture.nodeInfo('PLC1')['defaultRoute'] == 'via 192.168.1.254/24'
    assert topo_fixture.nodeInfo('PLC2')['defaultRoute'] == 'via 192.168.1.254/24'
    assert topo_fixture.nodeInfo('scada')['defaultRoute'] == 'via 192.168.2.254/24'


def test_router_link_props(topo_fixture):
    assert topo_fixture.linkInfo('s1', 'r0')['intfName2'] == 'r0-eth1'
    assert topo_fixture.linkInfo('s1', 'r0')['params2'] == {'ip': '192.168.1.254/24'}
    assert topo_fixture.linkInfo('s2', 'r0')['intfName2'] == 'r0-eth2'
    assert topo_fixture.linkInfo('s2', 'r0')['params2'] == {'ip': '192.168.2.254/24'}


def test_links_amount(topo_fixture):
    assert len(topo_fixture.links()) == 5


def test_links_endpoints(topo_fixture):
    print(topo_fixture.links())
    # Link from switch 1 to router
    assert topo_fixture.links()[0][0] == 's2'
    assert topo_fixture.links()[0][1] == 'r0'
    # Link from switch2 to router
    assert topo_fixture.links()[1][0] == 's1'
    assert topo_fixture.links()[1][1] == 'r0'
    # Link from switch 1 to PLC1
    assert topo_fixture.links()[2][0] == 's2'
    assert topo_fixture.links()[2][1] == 'scada'
    # Link from switch 1 to PLC2
    assert topo_fixture.links()[3][0] == 's1'
    assert topo_fixture.links()[3][1] == 'PLC1'
    # Link from switch 2 to scada
    assert topo_fixture.links()[4][0] == 's1'
    assert topo_fixture.links()[4][1] == 'PLC2'
