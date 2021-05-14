# import unittest
# from unittest.mock import MagicMock, call
import sys
import pytest

from dhalsim.python2.entities.control import AboveControl, BelowControl, TimeControl


# @pytest.fixture
# def mock_plc1():
#     mock = MagicMock()
#     mock.get_tag.return_value = 20
#     mock.set_tag.return_value = None
#     mock.get_master_clock.return_value = 43
#     return mock
#
#
# @pytest.fixture
# def mock_plc2():
#     mock = MagicMock()
#     mock.get_tag.return_value = 3000
#     mock.set_tag.return_value = None
#     mock.get_master_clock.return_value = 10
#     return mock


@pytest.fixture
def below_fixture():
    return BelowControl("testActuator1", "action1", "testTank1", 41)


@pytest.fixture
def above_fixture():
    return AboveControl("testActuator2", "action2", "testTank2", 42)


@pytest.fixture
def time_fixture():
    return TimeControl("testActuator3", "action3", 43)


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


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
    assert time_fixture.value == 43


# @pytest.mark.skip(reason="miniCPS not installed on runner")
# def test_apply_true_BelowControl(mocker, below_fixture, mock_plc1):
#     # mocker.patch(
#     #     'dhalsim.entities.generic_plc.GenericPlc',
#     #     mock_plc1
#     # )
#
#     assert below_fixture.apply(mock_plc1) is None
#     # Assert call.get tag called, and below value was true
#     expected = [call.get_tag('testTank1'), call.set_tag('action1', 'testActuator1')]
#     assert mock_plc1.mock_calls == expected
#
#
# @pytest.mark.skip(reason="miniCPS not installed on runner")
# def test_apply_false_BelowControl(mocker, below_fixture, mock_plc2):
#     # mocker.patch(
#     #     'dhalsim.entities.generic_plc.GenericPlc',
#     #     mock_plc2
#     # )
#
#     assert below_fixture.apply(mock_plc2) is None
#     # Assert call.get tag called, and below value was false
#     expected = [call.get_tag('testTank1')]
#     assert mock_plc2.mock_calls == expected
#
#
# @pytest.mark.skip(reason="miniCPS not installed on runner")
# def test_apply_true_AboveControl(mocker, above_fixture, mock_plc2):
#     # mocker.patch(
#     #     'dhalsim.entities.generic_plc.GenericPlc',
#     #     mock_plc2
#     # )
#
#     assert above_fixture.apply(mock_plc2) is None
#     # Assert call.get tag called, and above value was true
#     expected = [call.get_tag('testTank2'), call.set_tag('action2', 'testActuator2')]
#     assert mock_plc2.mock_calls == expected
#
#
# @pytest.mark.skip(reason="miniCPS not installed on runner")
# def test_apply_false_AboveControl(mocker, above_fixture, mock_plc1):
#     # mocker.patch(
#     #     'dhalsim.entities.generic_plc.GenericPlc',
#     #     mock_plc1
#     # )
#
#     assert above_fixture.apply(mock_plc1) is None
#     # Assert call.get tag called, and above value was false
#     expected = [call.get_tag('testTank2')]
#     assert mock_plc1.mock_calls == expected
#
#
# @pytest.mark.skip(reason="miniCPS not installed on runner")
# def test_apply_true_TimeControl(mocker, time_fixture, mock_plc1):
#     # mocker.patch(
#     #     'dhalsim.entities.generic_plc.GenericPlc',
#     #     mock_plc1
#     # )
#
#     assert time_fixture.apply(mock_plc1) is None
#     # Assert call.get tag called, and time == is true
#     expected = [call.get_master_clock(), call.set_tag('action3', 'testActuator3')]
#     assert mock_plc1.mock_calls == expected
#
#
# @pytest.mark.skip(reason="miniCPS not installed on runner")
# def test_apply_false_TimeControl(mocker, time_fixture, mock_plc2):
#     # mocker.patch(
#     #     'dhalsim.entities.generic_plc.GenericPlc',
#     #     mock_plc2
#     # )
#
#     assert time_fixture.apply(mock_plc2) is None
#     # Assert call.get tag called, and above value was true
#     expected = [call.get_master_clock()]
#     assert mock_plc2.mock_calls == expected
