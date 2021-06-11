import sys

import pytest
from mock import call, Mock
from scapy.layers.l2 import ARP, Ether

from dhalsim.network_attacks.utilities import spoof_arp_cache, launch_arp_poison, restore_arp, \
    get_mac


def test_python_version():
    assert sys.version_info.major is 3


@pytest.fixture
def get_mac_mock(mocker):
    macs = {
        '192.168.1.1': '42:aa:3d:69:21:bf',
        '192.168.1.2': 'aa:bb:cc:dd:ee:02',
    }

    mocked_get_mac = mocker.patch('dhalsim.network_attacks.utilities.get_mac')
    mocked_get_mac.side_effect = (lambda x: macs[x])

    return mocked_get_mac


@pytest.fixture
def send_mock(mocker):
    mocked_send = mocker.patch('dhalsim.network_attacks.utilities.send')
    return mocked_send


@pytest.fixture
def srp_mock(mocker):
    mocked_srp = mocker.patch('dhalsim.network_attacks.utilities.srp')
    return mocked_srp


def test_spoof_arp_cache(send_mock):
    spoof_arp_cache('192.168.1.1', '42:aa:3d:69:21:bf', '192.168.1.2')

    send_mock.assert_called_once_with(
        ARP(op=2, pdst='192.168.1.1', psrc='192.168.1.2', hwdst='42:aa:3d:69:21:bf'), verbose=False)


def test_launch_arp_poison(get_mac_mock, send_mock):
    launch_arp_poison('192.168.1.1', '192.168.1.2')

    get_mac_mock.assert_has_calls([call('192.168.1.1'), call('192.168.1.2')], any_order=True)
    assert get_mac_mock.call_count == 2

    send_mock.assert_has_calls([
        call(ARP(op=2, pdst='192.168.1.1', psrc='192.168.1.2', hwdst='42:aa:3d:69:21:bf'),
             verbose=False),
        call(ARP(op=2, pdst='192.168.1.2', psrc='192.168.1.1', hwdst='aa:bb:cc:dd:ee:02'),
             verbose=False)
    ], any_order=True)
    assert send_mock.call_count == 2


def test_restore_arp(get_mac_mock, send_mock):
    restore_arp('192.168.1.1', '192.168.1.2')

    get_mac_mock.assert_has_calls([call('192.168.1.1'), call('192.168.1.2')], any_order=True)
    assert get_mac_mock.call_count == 2

    send_mock.assert_has_calls([
        call(ARP(op=2, pdst='192.168.1.1', hwdst='42:aa:3d:69:21:bf', psrc='192.168.1.2',
                 hwsrc='aa:bb:cc:dd:ee:02'), verbose=False),
        call(ARP(op=2, pdst='192.168.1.2', hwdst='aa:bb:cc:dd:ee:02', psrc='192.168.1.1',
                 hwsrc='42:aa:3d:69:21:bf'), verbose=False)
    ], any_order=True)
    assert send_mock.call_count == 2


def test_get_mac(srp_mock):
    result = Mock()
    result.hwsrc = 'aa:bb:cc:dd:ee:03'
    srp_mock.return_value = [[[{}, result]]]

    assert get_mac('192.168.1.3') == 'aa:bb:cc:dd:ee:03'

    arp_packet = Ether(dst='ff:ff:ff:ff:ff:ff') / ARP(op=1, pdst='192.168.1.3')
    srp_mock.assert_called_once_with(arp_packet, timeout=2, verbose=False)
