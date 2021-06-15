import signal
import subprocess

import pytest
from mock import call, ANY
from pathlib import Path

from dhalsim.python2.automatic_plant import PlantControl


@pytest.fixture
def offline_after_three_process(mocker):
    process = mocker.Mock()
    process.poll.side_effect = [None, None, 42]
    process.send_signal.return_value = None
    process.terminate.return_value = None
    process.kill.return_value = None
    return process


@pytest.fixture
def subprocess_mock(mocker, offline_after_three_process):
    process = mocker.Mock()
    process.Popen.return_value = offline_after_three_process
    process.open.return_value = "testLoc"
    Path(__file__).parent.absolute()
    return process


@pytest.fixture
def patched_auto_plant(mocker, subprocess_mock):
    mocker.patch.object(PlantControl, "__init__", return_value=None)
    mocker.patch("subprocess.Popen", subprocess_mock.Popen)
    mocker.patch("__builtin__.open", subprocess_mock.open)
    logger_mock = mocker.Mock()

    auto_plant = PlantControl(None)
    auto_plant.logger = logger_mock

    return auto_plant, logger_mock


def test_terminate(patched_auto_plant, offline_after_three_process):
    auto_plant, logger_mock = patched_auto_plant
    auto_plant.simulation_process = offline_after_three_process

    auto_plant.terminate()

    logger_mock.debug.assert_called()

    offline_after_three_process.send_signal.assert_called_once_with(signal.SIGINT)
    assert offline_after_three_process.wait.call_count == 1
    assert offline_after_three_process.poll.call_count == 2
    assert offline_after_three_process.terminate.call_count == 1
    assert offline_after_three_process.kill.call_count == 1


def test_main(mocker, patched_auto_plant, offline_after_three_process, subprocess_mock):
    auto_plant, logger_mock = patched_auto_plant
    mocker.patch.object(PlantControl, "terminate", return_value=None)
    auto_plant.intermediate_yaml = "plant_yaml"

    auto_plant.main()

    subprocess_mock.Popen.assert_called_once_with(["python3", ANY, "plant_yaml"])

    offline_after_three_process.send_signal.assert_not_called()
    offline_after_three_process.wait.assert_not_called()
    assert offline_after_three_process.poll.call_count == 3
    offline_after_three_process.terminate.assert_not_called()
    offline_after_three_process.kill.assert_not_called()
