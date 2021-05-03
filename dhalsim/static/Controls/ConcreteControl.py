from dhalsim.static.Controls.AbstractControl import Control


class BelowControl(Control):
    def apply(self, generic_plc):
        dep_val = generic_plc.getSensorState(self.dependant)
        if dep_val < self.value:
            generic_plc.setActuatorState(self.action, self.actuator)


class AboveControl(Control):
    def apply(self, generic_plc):
        dep_val = generic_plc.getSensorState(self.dependant)
        if dep_val > self.value:
            generic_plc.setActuatorState(self.action, self.actuator)


class TimeControl(Control):
    def apply(self, generic_plc):
        dep_val = generic_plc.getSensorState(self.dependant)
        if dep_val == self.value:
            generic_plc.setActuatorState(self.action, self.actuator)