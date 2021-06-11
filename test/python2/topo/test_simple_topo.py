import sys
import time

import pytest
import yaml
from mininet.net import Mininet
from mininet.link import TCLink

from dhalsim.python2.topo.simple_topo import SimpleTopo, TooManyNodes


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


@pytest.fixture
def unmodified_dict():
    return {"plcs": [{"name": "PLC1", }, {"name": "PLC2", }, ], }


@pytest.fixture
def filled_dict():
    return {'plcs': [{'gateway_name': 'r0', 'name': 'PLC1', 'local_ip': '192.168.1.1',
                      'gateway_inbound_mac': 'AA:BB:CC:DD:00:01', 'gateway': '192.168.1.254',
                      'public_ip': '192.168.1.1', 'mac': 'AA:BB:CC:DD:02:01',
                      'gateway_ip': '192.168.1.254', 'interface': 'PLC1-eth0', 'switch_name': 's1'},
                     {'gateway_name': 'r0', 'name': 'PLC2', 'local_ip': '192.168.1.2',
                      'gateway_inbound_mac': 'AA:BB:CC:DD:00:01', 'gateway': '192.168.1.254',
                      'public_ip': '192.168.1.2', 'mac': 'AA:BB:CC:DD:02:02',
                      'gateway_ip': '192.168.1.254', 'interface': 'PLC2-eth0',
                      'switch_name': 's1'}],
            'scada': {'gateway_name': 'r0', 'name': 'scada', 'local_ip': '192.168.2.1',
                      'gateway_inbound_mac': 'AA:BB:CC:DD:00:02', 'public_ip': '192.168.2.1',
                      'mac': 'AA:BB:CC:DD:01:01', 'gateway_ip': '192.168.2.254',
                      'interface': 'scada-eth0', 'switch_name': 's2'}}


@pytest.fixture
def topo_fixture(mocker, tmpdir, unmodified_dict):
    mocker.patch('mininet.net.Mininet.randMac', return_value="00:1D:9C:C7:B0:70")

    c = tmpdir.join("intermediate.yaml")
    with c.open(mode='w') as intermediate_yaml:
        yaml.dump(unmodified_dict, intermediate_yaml)

    return SimpleTopo(c)


@pytest.fixture
def net(topo_fixture):
    net = Mininet(topo=topo_fixture, autoSetMacs=False, link=TCLink)
    net.start()
    topo_fixture.setup_network(net)
    time.sleep(0.2)
    yield net
    net.stop()


def test_writeback_yaml(tmpdir, topo_fixture, filled_dict):
    with tmpdir.join("intermediate.yaml").open(mode='r') as intermediate_yaml:
        dump = yaml.safe_load(intermediate_yaml)
    assert dump == filled_dict


def test_host_amount_network(topo_fixture):
    # Expecting 4 hosts; 2 PLCs, a router, a scada and a plant
    assert len(topo_fixture.hosts()) == 4


def test_host_names(topo_fixture):
    assert topo_fixture.hosts()[0] == 'PLC1'
    assert topo_fixture.hosts()[1] == 'PLC2'
    assert topo_fixture.hosts()[2] == 'r0'
    assert topo_fixture.hosts()[3] == 'scada'


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
    assert topo_fixture.links()[2][1] == 's2'
    assert topo_fixture.links()[2][0] == 'scada'
    # Link from switch 1 to PLC2
    assert topo_fixture.links()[3][1] == 's1'
    assert topo_fixture.links()[3][0] == 'PLC1'
    # Link from switch 2 to scada
    assert topo_fixture.links()[4][1] == 's1'
    assert topo_fixture.links()[4][0] == 'PLC2'


@pytest.mark.integrationtest
@pytest.mark.parametrize("host1, host2",
                         [("r0", "PLC1"), ("r0", "PLC2"), ("r0", "scada")])
@pytest.mark.flaky(max_runs=3)
def test_ping(net, host1, host2):
    assert net.ping(hosts=[net.get(host1), net.get(host2)]) == 0.0


@pytest.mark.integrationtest
@pytest.mark.parametrize("host1, host2",
                         [("r0", "s1"), ("r0", "s2"), ("s1", "PLC1"), ("s1", "PLC2"),
                          ("s2", "scada")])
def test_links(net, host1, host2):
    assert net.linksBetween(net.get(host1), net.get(host2)) != []


@pytest.mark.integrationtest
@pytest.mark.parametrize('host1, host2, mac1, mac2',
                         [('r0', 's1', 'aa:bb:cc:dd:00:01', ''),
                          ('r0', 's2', 'aa:bb:cc:dd:00:02', ''),
                          ('s1', 'PLC1', '', 'aa:bb:cc:dd:02:'),
                          ('s1', 'PLC2', '', 'aa:bb:cc:dd:02:'),
                          ('s2', 'scada', '', 'aa:bb:cc:dd:01:')])
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
    assert len(net.links) == 5


@pytest.mark.integrationtest
@pytest.mark.parametrize("server, client, server_ip",
                         [("PLC1", "r0", "192.168.1.1"), ("PLC2", "r0", "192.168.1.2"),
                          # ("PLC1", "PLC2", "192.168.1.1"), ("PLC2", "PLC1", "192.168.1.2"),
                          ("PLC1", "scada", "192.168.1.1"), ("PLC2", "scada", "192.168.1.2")])
@pytest.mark.flaky(max_runs=3)
def test_reachability(net, server, client, server_ip):
    net.get(server).cmd("echo 'test' | nc -q1 -l 44818 &")
    time.sleep(0.1)
    response = net.get(client).cmd("wget -qO - {ip}:44818".format(ip=server_ip))
    assert response.rstrip() == "test"


@pytest.mark.parametrize('plcs, network_attacks',
                         [
                             (10, 10),
                             (0, 250),
                             (250, 0),
                             (10, 240),
                         ])
def test_not_to_many_nodes_good_weather(plcs, network_attacks):
    plcs = [i for i in range(plcs)]
    network_attacks = [i for i in range(network_attacks)]
    SimpleTopo.check_amount_of_nodes({'plcs': plcs, 'network_attacks': network_attacks})


@pytest.mark.parametrize('network_attacks',
                         [
                             10,
                             250,
                             0,
                         ])
def test_not_to_many_nodes_no_plcs_good_weather(network_attacks):
    network_attacks = [i for i in range(network_attacks)]
    SimpleTopo.check_amount_of_nodes({'network_attacks': network_attacks})


@pytest.mark.parametrize('plcs',
                         [
                             10,
                             250,
                             0,
                         ])
def test_not_to_many_nodes_no_network_attacks_good_weather(plcs):
    plcs = [i for i in range(plcs)]
    SimpleTopo.check_amount_of_nodes({'plcs': plcs})


@pytest.mark.parametrize('plcs, network_attacks',
                         [
                             (10, 241),
                             (0, 251),
                             (251, 0),
                             (11, 240),
                         ])
def test_not_to_many_nodes_bad_weather(plcs, network_attacks):
    plcs = [i for i in range(plcs)]
    network_attacks = [i for i in range(network_attacks)]
    with pytest.raises(TooManyNodes):
        SimpleTopo.check_amount_of_nodes({'plcs': plcs, 'network_attacks': network_attacks})


@pytest.mark.parametrize('network_attacks',
                         [
                             251,
                             1000000,
                         ])
def test_not_to_many_nodes_no_plcs_bad_weather(network_attacks):
    network_attacks = [i for i in range(network_attacks)]
    with pytest.raises(TooManyNodes):
        SimpleTopo.check_amount_of_nodes({'network_attacks': network_attacks})


@pytest.mark.parametrize('plcs',
                         [
                             251,
                             100000,
                         ])
def test_not_to_many_nodes_no_network_attacks_bad_weather(plcs):
    plcs = [i for i in range(plcs)]
    with pytest.raises(TooManyNodes):
        SimpleTopo.check_amount_of_nodes({'plcs': plcs})
