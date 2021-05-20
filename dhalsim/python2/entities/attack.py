from abc import ABCMeta, abstractmethod


class Attack:
    """Defines an attack executed by a PLC (device or network attack)

    :param name: The name of the attack
    :param start: The start time of the attack
    :param end: The end time of the attack
    """
    __metaclass__ = ABCMeta

    def __init__(self, name, start, end):
        """Constructor method
        """
        self.name = name
        self.start = start
        self.end = end

    @abstractmethod
    def apply(self, generic_plc):
        """Applies an attack rule using a given PLC

        :param generic_plc: the PLC that will apply the attack
        """
        pass


class DeviceAttack(Attack):
    """
    Defines a Device Attack, which is an attack that will perform an action on a given PLC

    :param name: The name of the attack
    :param target: The PLC target of the attack
    :param actuators: The actuators that will be attacked
    :param command: The command to execute on the actuators
    :param start: The start time of the attack
    :param end: The end time of the attack
    """
    def __init__(self, name, target, actuators, command, start, end):
        super(DeviceAttack, self).__init__(name, start, end)
        self.target = target
        self.actuators = actuators
        self.command = command

    def apply(self, plc):
        """Applies the Device Attack on a given PLC

        :param plc: The PLC that will apply the action
        """
        curr_time = plc.get_master_clock()
        print("Checking attack time: " + str(curr_time))
        if self.start <= curr_time <= self.end:
            print("Attack applied")
            for actuator in self.actuators:
                plc.set_tag(actuator, self.command)
