from dhalsim.static.controls.AbstractControl import Control
from dhalsim.entities.generic_plc import GenericPlc


class BelowControl(Control):
    """Defines a BELOW control, which takes as a parameter a dependant

    :param dependant: value that the condition depends on (such as value of tank T0)
    """

    def __init__(self, actuator: str, action: str, dependant: str, value):
        super(BelowControl, self).__init__(actuator, action, value)
        self.dependant = dependant

    def apply(self, generic_plc: GenericPlc):
        """Applies the BELOW control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        dep_val = generic_plc.get_tag(self.dependant)
        if dep_val < self.value:
            generic_plc.set_tag(self.action, self.actuator)


class AboveControl(Control):
    """Defines a ABOVE control, which takes as a parameter a dependant

    :param dependant: value that the condition depends on (such as value of tank T0)
    """

    def __init__(self, actuator: str, action: str, dependant: str, value):
        super(AboveControl, self).__init__(actuator, action, value)
        self.dependant = dependant

    def apply(self, generic_plc: GenericPlc):
        """Applies the ABOVE control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        dep_val = generic_plc.get_tag(self.dependant)
        if dep_val > self.value:
            generic_plc.set_tag(self.action, self.actuator)


class TimeControl(Control):
    """Defines a TIME control, which takes no additional parameters
    """

    def apply(self, generic_plc: GenericPlc):
        """Applies the TIME control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        curr_time = generic_plc.get_master_clock()
        if curr_time == self.value:
            generic_plc.set_tag(self.action, self.actuator)
