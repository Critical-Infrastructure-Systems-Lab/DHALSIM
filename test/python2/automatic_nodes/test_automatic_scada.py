import signal
import subprocess

import pytest
from mock import call, ANY
from pathlib import Path

from dhalsim.python2.automatic_scada import ScadaControl


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
def patched_auto_scada(mocker, subprocess_mock):
    mocker.patch.object(ScadaControl, "__init__", return_value=None)
    mocker.patch("subprocess.Popen", subprocess_mock.Popen)
    mocker.patch("__builtin__.open", subprocess_mock.open)
    logger_mock = mocker.Mock()

    auto_scada = ScadaControl(None)
    auto_scada.logger = logger_mock

    return auto_scada, logger_mock


def test_terminate(patched_auto_scada, offline_after_three_process, offline_after_one_process):
    auto_scada, logger_mock = patched_auto_scada
    auto_scada.process_tcp_dump = offline_after_three_process
    auto_scada.scada_process = offline_after_one_process

    auto_scada.terminate()

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


def test_main(mocker, patched_auto_scada, offline_after_three_process, offline_after_one_process):
    auto_scada, logger_mock = patched_auto_scada
    mocker.patch.object(ScadaControl, "start_tcpdump_capture", return_value=offline_after_one_process)
    mocker.patch.object(ScadaControl, "start_scada", return_value=offline_after_three_process)
    mocker.patch.object(ScadaControl, "terminate", return_value=None)

    auto_scada.main()

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


def test_start_tcpdump_capture(patched_auto_scada, subprocess_mock):
    auto_scada, logger_mock = patched_auto_scada
    auto_scada.output_path = Path("testPath")
    auto_scada.data = {"scada": {"interface": "testInterface"}}

    assert auto_scada.start_tcpdump_capture() == 42
    subprocess_mock.Popen.assert_called_once_with(
        ['tcpdump', '-i', "testInterface", '-w',
         "testPath/scada-eth0.pcap"], shell=False, stderr="testLoc", stdout="testLoc")


def test_start_scada(patched_auto_scada, subprocess_mock):
    auto_scada, logger_mock = patched_auto_scada
    auto_scada.intermediate_yaml = "testYaml"
    auto_scada.plc_index = 1
    auto_scada.data = {"log_level": "info"}

    assert auto_scada.start_scada() == 42
    subprocess_mock.Popen.assert_called_once_with(
        ["python2", ANY, "testYaml"], shell=False,
        stderr="testLoc", stdout="testLoc")
