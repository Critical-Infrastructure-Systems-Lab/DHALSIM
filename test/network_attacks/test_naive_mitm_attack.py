import threading
from pathlib import Path

import fnfqueue
import pytest
import yaml

from dhalsim.network_attacks.naive_attack import SyncedAttack, PacketAttack


@pytest.fixture
def intermediate_yaml_path():
    return Path("test/auxilary_testing_files/intermediate_yaml_network_attacks.yaml")


@pytest.fixture
def os_mock(mocker):
    mocked_os = mocker.Mock()
    mocked_os.system.return_value = None

    mocker.patch("os.system", mocked_os.system)
    return mocked_os


@pytest.fixture
def subprocess_mock(mocker):
    process = mocker.Mock()
    process.communicate.return_value = None
    process.wait.return_value = None
    process.terminate.return_value = None

    mocker.patch("subprocess.Popen", return_value=process)
    return process


@pytest.fixture
def thread_mock(mocker):
    thread = mocker.Mock()
    thread.start.return_value = None
    thread.join.return_value = None

    mocker.patch("threading.Thread", return_value=thread)
    return thread


@pytest.fixture
def fnfqueue_mock(mocker, fnfqueue_bound_mock):
    queue = mocker.Mock()
    queue.close.return_value = None
    queue.bind.return_value = fnfqueue_bound_mock

    mocker.patch("fnfqueue.Connection", return_value=queue)
    return queue


@pytest.fixture
def fnfqueue_bound_mock(mocker):
    q = mocker.Mock()
    q.set_mode.return_value = None
    q.unbind.return_value = None

    return q


@pytest.fixture
def launch_arp_poison_mock(mocker):
    return mocker.patch('dhalsim.network_attacks.naive_attack.launch_arp_poison', return_value=None)


@pytest.fixture
def restore_arp_mock(mocker):
    return mocker.patch('dhalsim.network_attacks.naive_attack.restore_arp', return_value=None)


@pytest.fixture
def attack_time(intermediate_yaml_path, mocker):
    mocker.patch.object(SyncedAttack, 'initialize_db', return_value=None)
    return PacketAttack(intermediate_yaml_path, 1)


@pytest.fixture
def attack_above(intermediate_yaml_path, mocker):
    mocker.patch.object(SyncedAttack, 'initialize_db', return_value=None)
    return PacketAttack(intermediate_yaml_path, 2)


@pytest.fixture
def attack_below(intermediate_yaml_path, mocker):
    mocker.patch.object(SyncedAttack, 'initialize_db', return_value=None)
    return PacketAttack(intermediate_yaml_path, 3)


@pytest.fixture
def attack_between(intermediate_yaml_path, mocker):
    mocker.patch.object(SyncedAttack, 'initialize_db', return_value=None)
    return PacketAttack(intermediate_yaml_path, 4)


def test_init(intermediate_yaml_path, os_mock, mocker):
    mocker.patch.object(SyncedAttack, 'initialize_db', return_value=None)
    packet_attack = PacketAttack(intermediate_yaml_path, 1)

    assert packet_attack.yaml_index == 1
    with intermediate_yaml_path.open() as yaml_file:
        data = yaml.load(yaml_file, Loader=yaml.FullLoader)
        assert packet_attack.intermediate_yaml == data
        assert packet_attack.intermediate_attack == data['network_attacks'][1]
        assert packet_attack.intermediate_plc == data['plcs'][1]
    assert packet_attack.attacker_ip == "192.168.1.5"
    assert packet_attack.target_plc_ip == "192.168.1.1"
    assert os_mock.system.call_count == 1
    assert packet_attack.state == 0


def test_setup(os_mock, attack_time, thread_mock, launch_arp_poison_mock, fnfqueue_mock, fnfqueue_bound_mock):
    attack_time.setup()

    assert os_mock.system.call_count == 5
    assert launch_arp_poison_mock.call_count == 1
    assert fnfqueue.Connection.call_count == 1
    fnfqueue_mock.bind.assert_called_with(1)
    fnfqueue_bound_mock.set_mode.assert_called_with(fnfqueue.MAX_PAYLOAD, fnfqueue.COPY_PACKET)
    assert attack_time.run_thread == True
    assert threading.Thread.call_count == 1
    assert thread_mock.start.call_count == 1


def test_interrupt_from_state_1(attack_time, mocker):
    mocker.patch.object(PacketAttack, 'teardown', return_value=None)
    attack_time.state = 1
    attack_time.interrupt()

    assert attack_time.teardown.call_count == 1


def test_interrupt_from_state_0(attack_time, mocker):
    mocker.patch.object(PacketAttack, 'teardown', return_value=None)
    attack_time.state = 0
    attack_time.interrupt()

    assert attack_time.teardown.call_count == 0


def test_teardown(attack_time, restore_arp_mock, os_mock, thread_mock, fnfqueue_mock, fnfqueue_bound_mock):
    attack_time.thread = thread_mock
    attack_time.queue = fnfqueue_mock
    attack_time.q = fnfqueue_bound_mock
    attack_time.teardown()

    assert restore_arp_mock.call_count == 1
    assert os_mock.system.call_count == 4
    assert attack_time.run_thread == False
    assert fnfqueue_bound_mock.unbind.call_count == 1
    assert fnfqueue_mock.close.call_count == 1
    assert thread_mock.join.call_count == 1


def test_time_trigger_true(attack_time, mocker):
    mocker.patch.object(SyncedAttack, "get_master_clock", return_value=5)
    assert attack_time.check_trigger()


def test_time_trigger_false(attack_time, mocker):
    mocker.patch.object(SyncedAttack, "get_master_clock", return_value=12)
    assert not attack_time.check_trigger()


def test_above_trigger_true(attack_above, mocker):
    mocker.patch.object(SyncedAttack, "receive_tag", return_value=0.20)
    assert attack_above.check_trigger()


def test_above_trigger_false(attack_above, mocker):
    mocker.patch.object(SyncedAttack, "receive_tag", return_value=0.19)
    assert not attack_above.check_trigger()


def test_below_trigger_true(attack_below, mocker):
    mocker.patch.object(SyncedAttack, "receive_tag", return_value=0.10)
    assert attack_below.check_trigger()


def test_below_trigger_false(attack_below, mocker):
    mocker.patch.object(SyncedAttack, "receive_tag", return_value=0.11)
    assert not attack_below.check_trigger()


def test_between_trigger_true(attack_between, mocker):
    mocker.patch.object(SyncedAttack, "receive_tag", return_value=0.20)
    assert attack_between.check_trigger()


def test_between_trigger_false(attack_between, mocker):
    mocker.patch.object(SyncedAttack, "receive_tag", return_value=0.21)
    assert not attack_between.check_trigger()