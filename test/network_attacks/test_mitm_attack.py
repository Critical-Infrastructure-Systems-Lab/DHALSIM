import subprocess
import threading

import pytest
from pathlib import Path

from dhalsim.network_attacks.utilities import launch_arp_poison
from dhalsim.network_attacks.mitm_attack import MitmAttack


@pytest.fixture
def intermediate_yaml_path():
    return Path("test/auxilary_testing_files/intermediate_yaml_network_attacks.yaml")


@pytest.fixture
def yaml_index():
    return 0


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

    mocker.patch("subprocess.Popen", return_value=process)
    return process


@pytest.fixture
def thread_mock(mocker):
    thread = mocker.Mock()
    thread.start.return_value = None

    mocker.patch("threading.Thread", return_value=thread)
    return thread


@pytest.fixture
def launch_arp_poison_mock(mocker):
    return mocker.patch('dhalsim.network_attacks.mitm_attack.launch_arp_poison', return_value=None)


@pytest.fixture
def attack(intermediate_yaml_path, yaml_index):
    return MitmAttack(intermediate_yaml_path, yaml_index)


def test_init(intermediate_yaml_path, yaml_index, os_mock):
    mitm_attack = MitmAttack(intermediate_yaml_path, yaml_index)

    assert mitm_attack.yaml_index == yaml_index
    assert mitm_attack.attacker_ip == "192.168.1.4"
    assert mitm_attack.target_plc_ip == "192.168.1.1"
    assert os_mock.system.call_count == 1


def test_setup(os_mock, subprocess_mock, attack, thread_mock, launch_arp_poison_mock, mocker):
    # Mock self.update_tags_dict()
    mocker.patch.object(MitmAttack, "update_tags_dict", return_value=None)
    attack.setup()

    assert os_mock.system.call_count == 5
    subprocess.Popen.assert_called_with(
        ['/usr/bin/python2', '-m', 'cpppo.server.enip', '--print', '--address', '192.168.1.4:44818',
         'V_ER2i:1=REAL', 'T2:1=REAL'], shell=False)
    assert attack.update_tags_dict.call_count == 1
    assert threading.Thread.call_count == 1
    assert thread_mock.start.call_count == 1
    assert launch_arp_poison_mock.call_count == 1


def test_receive_original_tags(subprocess_mock, attack, mocker):
    attack.receive_original_tags()

    subprocess.Popen.assert_called_with(
        ['/usr/bin/python2', '-m', 'cpppo.server.enip.client', '--print', '--address',
         '192.168.1.1:44818', 'V_ER2i:1', 'T2:1'], shell=False, stdout=-1)
    assert subprocess_mock.communicate.call_count == 1


def test_update_tags_dict(mocker, attack):
    # Mock self.receive_original_tags() as this function is already tested
    mocker.patch.object(MitmAttack, "receive_original_tags", return_value=None)
    attack.tags = {
        "V_ER2i": 1,
        "T2": 0.1
    }
    attack.update_tags_dict()

    assert attack.tags == {
        "V_ER2i": 1,
        "T2": 0.2
    }
