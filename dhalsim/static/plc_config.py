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
                 mac: str = None, ip: str = None, db_path = None, db_name = None):
        """Constructor method
        """
        self.db_path = db_path
        self.db_name = db_name
        self.name = name
        self.sensors = sensors
        self.actuators = actuators
        self.mac = mac
        self.ip = ip

    @property
    def tags(self):
        tags = []
        for sensor in self.sensors:
            tags.append((sensor, 1, "REAL"))
        for actuator in self.actuators:
            tags.append((actuator, 1, "REAL"))
        return tags
        

    @property
    def server(self):
        return {
            'address': self.ip,
            'tags': self.tags
        }

    @property
    def protocol(self):
        return {
            'name': 'enip',
            'mode': 1,
            'server': self.server
        }

    @property
    def state(self):
        return {
            'name': self.db_name,
            'path': self.db_path
        }
