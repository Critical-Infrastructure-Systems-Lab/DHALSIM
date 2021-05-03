from dhalsim.static.Controls.AbstractControl import Control


class BelowControl(Control):
    """Applies the BELOW control rule using a given PLC

    :param generic_plc: the PLC that will apply the control actions
    """

    def apply(self, generic_plc):
        dep_val = generic_plc.getSensorState(self.dependant)
        if dep_val < self.value:
            generic_plc.setActuatorState(self.action, self.actuator)


class AboveControl(Control):
    """Applies the ABOVE control rule using a given PLC

    :param generic_plc: the PLC that will apply the control actions
    """

    def apply(self, generic_plc):
        dep_val = generic_plc.getSensorState(self.dependant)
        if dep_val > self.value:
            generic_plc.setActuatorState(self.action, self.actuator)


class TimeControl(Control):
    """Applies the TIME control rule using a given PLC

    :param generic_plc: the PLC that will apply the control actions
    """

    def apply(self, generic_plc):
        dep_val = generic_plc.getSensorState(self.dependant)
        if dep_val == self.value:
            generic_plc.setActuatorState(self.action, self.actuator)
