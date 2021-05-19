from abc import ABCMeta, abstractmethod


# todo import genericPLC once completed

class Control:
    """Defines a control for a PLC to enforce

    :param actuator: actuator that the rule will apply to
    :param action: action that will be performed (OPEN or CLOSED)
    :param value: value that is checked (t0 > value, time == value) etc
    """
    __metaclass__ = ABCMeta

    def __init__(self, actuator, action, value):
        """Constructor method
        """
        self.actuator = actuator
        self.action = action
        self.value = value

    @abstractmethod
    def apply(self, generic_plc):
        """Applies a control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        pass


class BelowControl(Control):
    """Defines a BELOW control, which takes as a parameter a dependant

    :param dependant: value that the condition depends on (such as value of tank T0)
    """

    def __init__(self, actuator, action, dependant, value):
        super(BelowControl, self).__init__(actuator, action, value)
        self.dependant = dependant

    def apply(self, generic_plc):
        """Applies the BELOW control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        dep_val = generic_plc.get_tag(self.dependant)
        # print("Get " + str(self.dependant) + " from " + generic_plc.intermediate_plc["name"] + " result is " + dep_val)
        if dep_val < self.value:
            generic_plc.set_tag(self.actuator, self.action)
            # print(generic_plc.intermediate_plc["name"] + " applied " + str(self) + " because dep_val " + str(dep_val))

    def __str__(self):
        return "Control if {dependant} < {value} then set {actuator} to {action}".format(
            dependant=self.dependant, value=self.value, actuator=self.actuator, action=self.action)


class AboveControl(Control):
    """Defines a ABOVE control, which takes as a parameter a dependant

    :param dependant: value that the condition depends on (such as value of tank T0)
    """

    def __init__(self, actuator, action, dependant, value):
        super(AboveControl, self).__init__(actuator, action, value)
        self.dependant = dependant

    def apply(self, generic_plc):
        """Applies the ABOVE control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        dep_val = generic_plc.get_tag(self.dependant)
        if dep_val > self.value:
            generic_plc.set_tag(self.actuator, self.action)
            # print(generic_plc.intermediate_plc["name"] + " applied " + str(self) + " because dep_val " + str(dep_val))

    def __str__(self):
        return "Control if {dependant} > {value} then set {actuator} to {action}".format(
            dependant=self.dependant, value=self.value, actuator=self.actuator, action=self.action)


class TimeControl(Control):
    """Defines a TIME control, which takes no additional parameters
    """

    def apply(self, generic_plc):
        """Applies the TIME control rule using a given PLC

        :param generic_plc: the PLC that will apply the control actions
        """
        curr_time = generic_plc.get_master_clock()
        if curr_time == self.value:
            generic_plc.set_tag(self.actuator, self.action)
            # print(generic_plc.intermediate_plc["name"] + " applied " + str(self) + " because curr_time " + str(curr_time))

    def __str__(self):
        return "Control if time = {value} then set {actuator} to {action}".format(
            value=self.value, actuator=self.actuator, action=self.action)
