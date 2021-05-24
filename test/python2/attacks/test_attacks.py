import sys
import pytest
import pytest_mock
from mock import MagicMock, call

from dhalsim.python2.entities.attack import TimeAttack, TriggerBelowAttack, TriggerAboveAttack, TriggerBetweenAttack


@pytest.fixture
def time_attack():
    return TimeAttack("TestTimeAttack", ["P_RAW1", "P_RAW2"], "closed", 20, 40)


@pytest.fixture
def trigger_attack_above():
    return TriggerAboveAttack("TestAboveAttack", ["P_RAW1", "P_RAW2"], "closed", "T1", 0.20)


@pytest.fixture
def trigger_attack_below():
    return TriggerBelowAttack("TestBelowAttack", ["P_RAW1", "P_RAW2"], "closed", "T1", 0.20)


@pytest.fixture
def trigger_between_attack():
    return TriggerBetweenAttack("TestBetweenAttack", ["P_RAW1", "P_RAW2"], "closed", "T1", 0.10, 0.16)


@pytest.fixture
def mock_plc1(mocker):
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC',
        mock_plc1
    )
    mock = MagicMock()
    mock.get_tag.return_value = 0.35
    mock.set_tag.return_value = None
    mock.get_master_clock.return_value = 30
    return mock


@pytest.fixture
def mock_plc2(mocker):
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC',
        mock_plc2
    )
    mock = MagicMock()
    mock.get_tag.return_value = 0.15
    mock.set_tag.return_value = None
    mock.get_master_clock.return_value = 10
    return mock


# Test that we are running python 2.7
def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


def test_time_properties(time_attack):
    assert time_attack.name == "TestTimeAttack"
    assert time_attack.actuators == ["P_RAW1", "P_RAW2"]
    assert time_attack.command == "closed"
    assert time_attack.start == 20
    assert time_attack.end == 40


def test_trigger_above_properties(trigger_attack_above):
    assert trigger_attack_above.name == "TestAboveAttack"
    assert trigger_attack_above.actuators == ["P_RAW1", "P_RAW2"]
    assert trigger_attack_above.command == "closed"
    assert trigger_attack_above.sensor == "T1"
    assert trigger_attack_above.value == 0.20


def test_trigger_below_properties(trigger_attack_below):
    assert trigger_attack_below.name == "TestBelowAttack"
    assert trigger_attack_below.actuators == ["P_RAW1", "P_RAW2"]
    assert trigger_attack_below.command == "closed"
    assert trigger_attack_below.sensor == "T1"
    assert trigger_attack_below.value == 0.20


def test_trigger_between_attack(trigger_between_attack):
    assert trigger_between_attack.name == "TestBetweenAttack"
    assert trigger_between_attack.actuators == ["P_RAW1", "P_RAW2"]
    assert trigger_between_attack.command == "closed"
    assert trigger_between_attack.sensor == "T1"
    assert trigger_between_attack.lower_value == 0.10
    assert trigger_between_attack.upper_value == 0.16


def test_time_attack_apply_true(time_attack, mock_plc1):
    assert time_attack.apply(mock_plc1) is None
    mock_plc1.get_master_clock.assert_called_with()
    mock_plc1.set_tag.assert_any_call('P_RAW1', 'closed')
    mock_plc1.set_tag.assert_any_call('P_RAW2', 'closed')


def test_time_attack_apply_false(time_attack, mock_plc2):
    assert time_attack.apply(mock_plc2) is None
    mock_plc2.get_master_clock.assert_called_with()
    mock_plc2.set_tag.assert_not_called()


def test_above_attack_apply_true(trigger_attack_above, mock_plc1):
    assert trigger_attack_above.apply(mock_plc1) is None
    mock_plc1.get_tag.assert_called_with('T1')
    mock_plc1.set_tag.assert_any_call('P_RAW1', 'closed')
    mock_plc1.set_tag.assert_any_call('P_RAW2', 'closed')


def test_above_attack_apply_false(trigger_attack_above, mock_plc2):
    assert trigger_attack_above.apply(mock_plc2) is None
    mock_plc2.get_tag.assert_called_with('T1')
    mock_plc2.set_tag.assert_not_called()


def test_below_attack_apply_true(trigger_attack_below, mock_plc2):
    assert trigger_attack_below.apply(mock_plc2) is None
    mock_plc2.get_tag.assert_called_with('T1')
    mock_plc2.set_tag.assert_any_call('P_RAW1', 'closed')
    mock_plc2.set_tag.assert_any_call('P_RAW2', 'closed')


def test_below_attack_apply_false(trigger_attack_below, mock_plc1):
    assert trigger_attack_below.apply(mock_plc1) is None
    mock_plc1.get_tag.assert_called_with('T1')
    mock_plc1.set_tag.assert_not_called()


def test_between_attack_apply_true(trigger_between_attack, mock_plc2):
    assert trigger_between_attack.apply(mock_plc2) is None
    mock_plc2.get_tag.assert_called_with('T1')
    mock_plc2.set_tag.assert_any_call('P_RAW1', 'closed')
    mock_plc2.set_tag.assert_any_call('P_RAW2', 'closed')


def test_between_attack_apply_false(trigger_between_attack, mock_plc1):
    assert trigger_between_attack.apply(mock_plc1) is None
    mock_plc1.get_tag.assert_called_with('T1')
    mock_plc1.set_tag.assert_not_called()
