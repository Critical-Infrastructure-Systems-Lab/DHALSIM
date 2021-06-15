import signal
import subprocess

import pytest
import yaml
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


@pytest.fixture
def plc_yaml():
    return Path("test/auxilary_testing_files/intermediate.yaml")


def test_init(plc_yaml):
    plc = PlcControl(plc_yaml, 0)
    assert plc.intermediate_yaml == plc_yaml
    assert plc.plc_index == 0
    assert plc.output_path == Path("temp/test/path")
    assert plc.process_tcp_dump is None
    assert plc.plc_process is None
    assert plc.logger is not None
    assert plc.this_plc_data == {'actuators': ['P_RAW1', 'V_PUB'],
                                 'attacks': [{'actuator': 'P_RAW1',
                                              'command': 'closed',
                                              'name': 'Close_PRAW1_from_iteration_5_to_10',
                                              'trigger': {'end': 10, 'start': 5, 'type': 'time'}},
                                             {'actuator': 'P_RAW1',
                                              'command': 'closed',
                                              'name': 'Close_PRAW1_when_T2_<_0.16',
                                              'trigger': {'sensor': 'T2', 'type': 'below', 'value': 0.16}}],
                                 'controls': [{'action': 'open',
                                               'actuator': 'V_PUB',
                                               'dependant': 'T0',
                                               'type': 'below',
                                               'value': 0.256},
                                              {'action': 'closed',
                                               'actuator': 'V_PUB',
                                               'dependant': 'T0',
                                               'type': 'above',
                                               'value': 0.448},
                                              {'action': 'closed',
                                               'actuator': 'P_RAW1',
                                               'dependant': 'T0',
                                               'type': 'below',
                                               'value': 0.256},
                                              {'action': 'open',
                                               'actuator': 'P_RAW1',
                                               'dependant': 'T2',
                                               'type': 'below',
                                               'value': 0.16},
                                              {'action': 'closed',
                                               'actuator': 'P_RAW1',
                                               'dependant': 'T2',
                                               'type': 'above',
                                               'value': 0.32},
                                              {'action': 'open',
                                               'actuator': 'V_PUB',
                                               'type': 'time',
                                               'value': 0},
                                              {'action': 'closed',
                                               'actuator': 'P_RAW1',
                                               'type': 'time',
                                               'value': 0}],
                                 'name': 'PLC1',
                                 'sensors': ['T0']}

    with plc_yaml.open(mode='r') as file:
        expected = yaml.safe_load(file)

    assert plc.data == expected


def test_terminate(patched_auto_plc, offline_after_three_process, offline_after_one_process):
    auto_plc, logger_mock = patched_auto_plc
    auto_plc.process_tcp_dump = offline_after_three_process
    auto_plc.plc_process = offline_after_one_process

    auto_plc.terminate()

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


@pytest.mark.timeout(1)
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
