import signal
import subprocess

import pytest
from mock import call, ANY
from pathlib import Path

from dhalsim.python2.automatic_plc import PlcControl


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
def patched_auto_plc(mocker, subprocess_mock):
    mocker.patch.object(PlcControl, "__init__", return_value=None)
    mocker.patch("subprocess.Popen", subprocess_mock.Popen)
    mocker.patch("__builtin__.open", subprocess_mock.open)
    logger_mock = mocker.Mock()

    auto_plc = PlcControl(None, None)
    auto_plc.logger = logger_mock

    return auto_plc, logger_mock


def test_terminate(patched_auto_plc, offline_after_three_process, offline_after_one_process):
    auto_plc, logger_mock = patched_auto_plc
    auto_plc.process_tcp_dump = offline_after_three_process
    auto_plc.plc_process = offline_after_one_process

    auto_plc.terminate()

    assert logger_mock.debug.call_count == 2
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


def test_main(mocker, patched_auto_plc, offline_after_three_process, offline_after_one_process):
    auto_plc, logger_mock = patched_auto_plc
    mocker.patch.object(PlcControl, "start_tcpdump_capture", return_value=offline_after_one_process)
    mocker.patch.object(PlcControl, "start_plc", return_value=offline_after_three_process)
    mocker.patch.object(PlcControl, "terminate", return_value=None)

    auto_plc.main()

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


def test_start_tcpdump_capture(patched_auto_plc, subprocess_mock):
    auto_plc, logger_mock = patched_auto_plc
    auto_plc.output_path = Path("testPath")
    auto_plc.this_plc_data = {"interface": "testInterface"}

    assert auto_plc.start_tcpdump_capture() == 42
    subprocess_mock.Popen.assert_called_once_with(
        ['tcpdump', '-i', "testInterface", '-w',
         "testPath/testInterface.pcap"], shell=False, stderr="testLoc", stdout="testLoc")


def test_start_plc(patched_auto_plc, subprocess_mock):
    auto_plc, logger_mock = patched_auto_plc
    auto_plc.intermediate_yaml = "testYaml"
    auto_plc.plc_index = 1
    auto_plc.data = {"log_level": "info"}

    assert auto_plc.start_plc() == 42
    subprocess_mock.Popen.assert_called_once_with(
        ["python2", ANY, "testYaml", "1"], shell=False,
        stderr="testLoc", stdout="testLoc")
