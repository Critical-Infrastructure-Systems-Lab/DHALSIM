import sys
import pytest

from dhalsim.python2.entities.attack import TimeAttack, TriggerBelowAttack, TriggerAboveAttack, TriggerBetweenAttack

@pytest.fixture
def time_attack():
    return TimeAttack("TestTimeAttack", ["P_RAW1", "P_RAW2"], "closed", 2, 4)

@pytest.fixture
def trigger_attack_above():
    return TriggerAboveAttack("TestAboveAttack", ["P_RAW1", "P_RAW2"], "closed", "T1", 0.20)

@pytest.fixture
def trigger_attack_below():
    return TriggerBelowAttack("TestBelowAttack", ["P_RAW1", "P_RAW2"], "closed", "T1", 0.20)

@pytest.fixture
def trigger_between_attack():
    return TriggerBetweenAttack("TestBetweenAttack", ["P_RAW1", "P_RAW2"], "closed", "T1", 0.10, 0.16)

# Test that we are running python 2.7
def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7

def test_time_properties(time_attack):
    assert time_attack.name == "TestTimeAttack"
    assert time_attack.actuators == ["P_RAW1", "P_RAW2"]
    assert time_attack.command == "closed"
    assert time_attack.start == 2
    assert time_attack.end == 4

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
