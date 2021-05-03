class Error(Exception):
    """Base class for exceptions in this module."""


class InvalidControlActionError(Error):
    """Raised when the requested control action is invalid"""


class Control:
    """Defines a control for a PLC to enforce

    :param actuator: actuator that the rule will apply to
    :param action: action that will be performed (OPEN or CLOSED)
    :param dependant: value that the condition depends on (such as value of tank T0)
    :param condition: type of condition (<, >, TIME)
    :param value: value that is checked (t0 > value, time == value) etc
    """
    def __init__(self, actuator: str, action: str, dependant: str, condition: str, value):
        """Constructor method
        """
        self.actuator = actuator
        self.action = action
        self.dependant = dependant
        self.condition = condition
        self.value = value

    def apply(self, generic_plc):
        """Applies a control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        # Get value of dependent
        dep_val = generic_plc.getSensorState(self.dependant)

        if self.action == ">":
            if dep_val > self.value:
                generic_plc.setActuatorState(self.action, self.actuator)
        elif self.action == "<":
            if dep_val < self.value:
                generic_plc.setActuatorState(self.action, self.actuator)
        elif self.action == "TIME":
            if dep_val == self.value:
                generic_plc.setActuatorState(self.action, self.actuator)
        else:
            raise InvalidControlActionError("Invalid control action (need '<', '>', 'TIME')")


