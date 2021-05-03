from abc import ABC, abstractmethod


# todo import genericPLC once completed

class Control(ABC):
    """Defines a control for a PLC to enforce

    :param actuator: actuator that the rule will apply to
    :param action: action that will be performed (OPEN or CLOSED)
    :param dependant: value that the condition depends on (such as value of tank T0)
    :param value: value that is checked (t0 > value, time == value) etc
    """

    def __init__(self, actuator: str, action: str, dependant: str, value):
        """Constructor method
        """
        self.actuator = actuator
        self.action = action
        self.dependant = dependant
        self.value = value
        super().__init__()

    @abstractmethod
    def apply(self, generic_plc):
        """Applies a control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        pass
