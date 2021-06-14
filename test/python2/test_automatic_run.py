import pytest
from mock import call

from dhalsim.python2.automatic_run import GeneralCPS


@pytest.fixture
def online_process(mocker):
    process = mocker.Mock()
    process.poll.return_value = None
    return process


@pytest.fixture
def offline_after_five_process(mocker):
    process = mocker.Mock()
    process.poll.side_effect = [None, None, None, None, 42]
    return process


@pytest.fixture
def offline_after_three_process(mocker):
    process = mocker.Mock()
    process.poll.side_effect = [None, None, 42]
    return process


@pytest.fixture
def patched_auto_run(mocker):
    mocker.patch.object(GeneralCPS, "__init__", return_value=None)
    logger_mock = mocker.Mock()

    auto_run = GeneralCPS(None)
    auto_run.logger = logger_mock

    return auto_run, logger_mock


@pytest.mark.timeout(1)
def test_plant_shutdown_normal(patched_auto_run, online_process, offline_after_five_process):
    auto_run, logger_mock = patched_auto_run
    auto_run.plc_processes = [online_process]
    auto_run.attacker_processes = [online_process]
    auto_run.scada_process = online_process
    auto_run.plant_process = offline_after_five_process

    auto_run.poll_processes()

    assert logger_mock.debug.call_count == 1
    assert offline_after_five_process.poll.call_count == 5
    assert online_process.poll.call_count == 15


@pytest.mark.timeout(1)
def test_plc_process_shutdown(patched_auto_run, online_process, offline_after_three_process):
    auto_run, logger_mock = patched_auto_run
    auto_run.plc_processes = [online_process, offline_after_three_process]
    auto_run.attacker_processes = [online_process]
    auto_run.scada_process = online_process
    auto_run.plant_process = online_process

    auto_run.poll_processes()

    assert logger_mock.debug.call_count == 1
    assert offline_after_three_process.poll.call_count == 3
    assert online_process.poll.call_count == 9


@pytest.mark.timeout(1)
def test_attacker_process_shutdown(patched_auto_run, online_process, offline_after_three_process):
    auto_run, logger_mock = patched_auto_run
    auto_run.plc_processes = [online_process]
    auto_run.attacker_processes = [online_process, offline_after_three_process]
    auto_run.scada_process = online_process
    auto_run.plant_process = online_process

    auto_run.poll_processes()

    assert logger_mock.debug.call_count == 1
    assert offline_after_three_process.poll.call_count == 3
    assert online_process.poll.call_count == 10


@pytest.mark.timeout(1)
def test_scada_process_shutdown(patched_auto_run, online_process, offline_after_five_process):
    auto_run, logger_mock = patched_auto_run
    auto_run.plc_processes = [online_process]
    auto_run.attacker_processes = [online_process]
    auto_run.scada_process = offline_after_five_process
    auto_run.plant_process = online_process

    auto_run.poll_processes()

    assert logger_mock.debug.call_count == 1
    assert offline_after_five_process.poll.call_count == 5
    assert online_process.poll.call_count == 14
