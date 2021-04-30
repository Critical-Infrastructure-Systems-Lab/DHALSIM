class PlcConfig:
    def __init__(self, name, mac, sensors, actuators):
        """
        Initializes a PlcConfig.

        :param name: the name of the PLC
        :param mac: the MAC address of the PLC
        :param sensors: the sensors the PLC can read
        :param actuators: the actuators the PLC can control
        """
        self.name = name
        self.mac = mac
        self.sensors = sensors
        self.actuators = actuators
