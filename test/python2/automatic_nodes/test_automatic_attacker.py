import signal
import subprocess
import sys

import pytest
from mock import call, ANY
from pathlib import Path

from dhalsim.python2.automatic_attacker import AttackerControl, NoSuchAttack


@pytest.fixture
def offline_after_one_process(mocker):
    process = mocker.Mock()
    process.poll.side_effect = [42, 42]
    process.send_signal.return_value = None
    process.terminate.return_value = None
    process.kill.return_value = None
    return process


@pytest.fixture
def offline_after_three_process(mocker):
    process = mocker.Mock()
    process.poll.side_effect = [None, None, 42]
    process.send_signal.return_value = None
    process.terminate.return_value = None
    process.kill.return_value = None
    return process


@pytest.fixture
def subprocess_mock(mocker):
    process = mocker.Mock()
    process.Popen.return_value = 42
    process.open.return_value = "testLoc"
    Path(__file__).parent.absolute()
    return process


@pytest.fixture
def patched_auto_attack(mocker, subprocess_mock):
    mocker.patch.object(AttackerControl, "__init__", return_value=None)
    mocker.patch("subprocess.Popen", subprocess_mock.Popen)
    mocker.patch("__builtin__.open", subprocess_mock.open)
    logger_mock = mocker.Mock()

    auto_attack = AttackerControl(None, None)
    auto_attack.logger = logger_mock

    return auto_attack, logger_mock


def test_terminate(patched_auto_attack, offline_after_three_process, offline_after_one_process):
    auto_attack, logger_mock = patched_auto_attack
    auto_attack.tcp_dump_process = offline_after_three_process
    auto_attack.attacker_process = offline_after_one_process

    auto_attack.terminate()

    logger_mock.debug.assert_called()

    offline_after_three_process.send_signal.assert_called_once_with(signal.SIGINT)
    assert offline_after_three_process.wait.call_count == 1
    assert offline_after_three_process.poll.call_count == 2
    assert offline_after_three_process.terminate.call_count == 1
    assert offline_after_three_process.kill.call_count == 1

    offline_after_one_process.send_signal.assert_called_once_with(signal.SIGINT)
    assert offline_after_one_process.wait.call_count == 1
    assert offline_after_one_process.poll.call_count == 2
    assert offline_after_one_process.terminate.call_count == 0
    assert offline_after_one_process.kill.call_count == 0


def test_main(mocker, patched_auto_attack, offline_after_three_process, offline_after_one_process):
    auto_attack, logger_mock = patched_auto_attack
    mocker.patch.object(AttackerControl, "start_tcpdump_capture", return_value=offline_after_one_process)
    mocker.patch.object(AttackerControl, "start_attack", return_value=offline_after_three_process)
    mocker.patch.object(AttackerControl, "terminate", return_value=None)

    auto_attack.main()

    offline_after_three_process.send_signal.assert_not_called()
    offline_after_three_process.wait.assert_not_called()
    assert offline_after_three_process.poll.call_count == 3
    offline_after_three_process.terminate.assert_not_called()
    offline_after_three_process.kill.assert_not_called()

    offline_after_one_process.send_signal.assert_not_called()
    offline_after_one_process.wait.assert_not_called()
    offline_after_one_process.poll.assert_not_called()
    offline_after_one_process.terminate.assert_not_called()
    offline_after_one_process.kill.assert_not_called()


def test_start_tcpdump_capture(patched_auto_attack, subprocess_mock):
    auto_attack, logger_mock = patched_auto_attack
    auto_attack.output_path = Path("testPath")
    auto_attack.this_attacker_data = {"interface": "testInterface"}

    assert auto_attack.start_tcpdump_capture() == 42
    subprocess_mock.Popen.assert_called_once_with(
        ['tcpdump', '-i', "testInterface", '-w',
         "testPath/testInterface.pcap"], shell=False)


def test_start_attack_exists(patched_auto_attack, subprocess_mock):
    auto_attack, logger_mock = patched_auto_attack
    auto_attack.intermediate_yaml = "testYaml"
    auto_attack.attacker_index = 1
    auto_attack.this_attacker_data = {"type": "mitm"}

    assert auto_attack.start_attack() == 42
    subprocess_mock.Popen.assert_called_once_with(
        ["python3", ANY, "testYaml", "1"], shell=False, stderr=sys.stderr, stdout=sys.stdout)


def test_start_attack_not_exists(patched_auto_attack, subprocess_mock):
    auto_attack, logger_mock = patched_auto_attack
    auto_attack.intermediate_yaml = "testYaml"
    auto_attack.attacker_index = 1
    auto_attack.this_attacker_data = {"type": "not_real"}

    with pytest.raises(NoSuchAttack):
        auto_attack.start_attack()
