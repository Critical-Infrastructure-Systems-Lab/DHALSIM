from dhalsim.static.Controls.AbstractControl import Control


# todo import genericPLC once completed

class BelowControl(Control):
    """Defines a BELOW control, which takes as a parameter a dependant

    :param dependant: value that the condition depends on (such as value of tank T0)
    """
    def __init__(self, actuator: str, action: str, dependant: str, value):
        super(BelowControl, self).__init__(actuator, action, value)
        self.dependant = dependant

    def apply(self, generic_plc):
        """Applies the BELOW control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        dep_val = generic_plc.getSensorState(self.dependant)
        if dep_val < self.value:
            generic_plc.setActuatorState(self.action, self.actuator)


class AboveControl(Control):
    """Defines a ABOVE control, which takes as a parameter a dependant

    :param dependant: value that the condition depends on (such as value of tank T0)
    """
    def __init__(self, actuator: str, action: str, dependant: str, value):
        super(AboveControl, self).__init__(actuator, action, value)
        self.dependant = dependant

    def apply(self, generic_plc):
        """Applies the ABOVE control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        dep_val = generic_plc.getSensorState(self.dependant)
        if dep_val > self.value:
            generic_plc.setActuatorState(self.action, self.actuator)


class TimeControl(Control):
    """Defines a TIME control, which takes no additional parameters
    """

    def apply(self, generic_plc):
        """Applies the TIME control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        curr_time = generic_plc.getMasterClock
        if curr_time == self.value:
            generic_plc.setActuatorState(self.action, self.actuator)
