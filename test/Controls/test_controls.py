import pytest
import pytest_mock

from dhalsim.static.Controls.ConcreteControl import BelowControl, AboveControl, TimeControl


@pytest.fixture
def below_fixture():
    return BelowControl("testActuator1", "action1", "testTank1", 41)


@pytest.fixture
def above_fixture():
    return AboveControl("testActuator2", "action2", "testTank2", 42)


@pytest.fixture
def time_fixture():
    return TimeControl("testActuator3", "action3", "testTank3", 43)


def test_below_properties(below_fixture):
    assert below_fixture.actuator == "testActuator1"
    assert below_fixture.action == "action1"
    assert below_fixture.dependant == "testTank1"
    assert below_fixture.value == 41


def test_above_properties(above_fixture):
    assert above_fixture.actuator == "testActuator2"
    assert above_fixture.action == "action2"
    assert above_fixture.dependant == "testTank2"
    assert above_fixture.value == 42


def test_time_properties(time_fixture):
    assert time_fixture.actuator == "testActuator3"
    assert time_fixture.action == "action3"
    assert time_fixture.dependant == "testTank3"
    assert time_fixture.value == 43

# todo add mock tests for apply using genericPLC methods once implemented

# def test_apply_BelowControl(mocker, below_fixture):
#     def mockSensorState(self, sensor):
#         return 1
#
#     def mockActuatorState(self, action, actuator):
#         return 1
#
#     mocker.patch(
#         # Call to generic PLC's 'getSensorState' function
#         'GenericPlC.getSensorState',
#         mockSensorState
#     )
#
#     mocker.patch(
#         # Call to generic PLC's 'setActuatorState' function
#         'GenericPlC.setActuatorState',
#         mockActuatorState
#     )
#
#     mocker.patch('os.remove')
#     assert 1 == 1
