from typing import List


class PlcConfig:
    """Initializes a PlcConfig.

    :param name: the name of the PLC
    :type name: str
    :param sensors: the sensors the PLC can read
    :type name: List[str]
    :param actuators: the actuators the PLC can control
    :type name: List[str]
    :param mac: the MAC address of the PLC
    :type name: str, optional
    :param ip: the ip address of the PLC
    :type name: str, optional
    """
    def __init__(self, name: str, sensors: List[str], actuators: List[str],
                 mac: str = None, ip: str = None):
        """Constructor method
        """
        self.name = name
        self.sensors = sensors
        self.actuators = actuators
        self.mac = mac
        self.ip = ip
