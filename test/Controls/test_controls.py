import pytest
import pytest_mock

from dhalsim.static.Controls.ConcreteControl import BelowControl, AboveControl, TimeControl


# def test_apply_BelowControl(mocker):
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
#     b_control = BelowControl("testActuator", "OPEN", "testTank", 42)
#
#     mocker.patch('os.remove')
#     assert 1 == 1
