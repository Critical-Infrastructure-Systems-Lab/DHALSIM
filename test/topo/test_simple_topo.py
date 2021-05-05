from dhalsim.static.plc_config import PlcConfig
from dhalsim.topo.simple_topo import SimpleTopo
from dhalsim.static.controls.ConcreteControl import *
import pytest

@pytest.fixture
def control_list_fixture():
    return [TimeControl("testActuator1", "CLOSED", 5), BelowControl("testActuator1", "CLOSED", "testSensor2", 5)]


@pytest.fixture
def topo_fixture(control_list_fixture):
    return SimpleTopo([
        PlcConfig('TestPLC1', ['testSensor1', 'testSensor2'], ['testActuator1', 'testActuator2'], control_list_fixture),
        PlcConfig('TestPLC2', ['testSensor3'], ['testActuator3'], control_list_fixture)
    ])


def test_host_amount_network(topo_fixture):
    # Expecting 4 hosts; 2 PLCs, a router and a scada
    assert len(topo_fixture.hosts()) == 4


def test_host_names(topo_fixture):
    assert topo_fixture.hosts()[0] == 'TestPLC1'
    assert topo_fixture.hosts()[1] == 'TestPLC2'
    assert topo_fixture.hosts()[2] == 'r0'
    assert topo_fixture.hosts()[3] == 'scada'


def test_host_ips(topo_fixture):
    assert topo_fixture.nodeInfo('TestPLC1')['ip'] == '192.168.1.1/24'
    assert topo_fixture.nodeInfo('TestPLC2')['ip'] == '192.168.1.2/24'
    assert topo_fixture.nodeInfo('r0')['ip'] == '192.168.1.254/24'
    assert topo_fixture.nodeInfo('scada')['ip'] == '192.168.2.1/24'


def test_host_gateways(topo_fixture):
    assert topo_fixture.nodeInfo('TestPLC1')['defaultRoute'] == 'via 192.168.1.254/24'
    assert topo_fixture.nodeInfo('TestPLC2')['defaultRoute'] == 'via 192.168.1.254/24'
    assert topo_fixture.nodeInfo('scada')['defaultRoute'] == 'via 192.168.2.254/24'


def test_router_link_props(topo_fixture):
    assert topo_fixture.linkInfo('s1', 'r0')['intfName2'] == 'r0-eth1'
    assert topo_fixture.linkInfo('s1', 'r0')['params2'] == {'ip': '192.168.1.254/24'}
    assert topo_fixture.linkInfo('s2', 'r0')['intfName2'] == 'r0-eth2'
    assert topo_fixture.linkInfo('s2', 'r0')['params2'] == {'ip': '192.168.2.254/24'}


def test_links_amount(topo_fixture):
    assert len(topo_fixture.links()) == 5


def test_links_endpoints(topo_fixture):
    # Link from switch 1 to router
    assert topo_fixture.links()[0][0] == 's1'
    assert topo_fixture.links()[0][1] == 'r0'
    # Link from switch2 to router
    assert topo_fixture.links()[1][0] == 's2'
    assert topo_fixture.links()[1][1] == 'r0'
    # Link from switch 1 to PLC1
    assert topo_fixture.links()[2][0] == 's1'
    assert topo_fixture.links()[2][1] == 'TestPLC1'
    # Link from switch 1 to PLC2
    assert topo_fixture.links()[3][0] == 's1'
    assert topo_fixture.links()[3][1] == 'TestPLC2'
    # Link from switch 2 to scada
    assert topo_fixture.links()[4][0] == 's2'
    assert topo_fixture.links()[4][1] == 'scada'
