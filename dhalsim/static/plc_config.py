from typing import List

from dhalsim.static.controls import ConcreteControl


class PlcConfig:
    """This houses all the properties a PLC can have.
    This object will be given to a :class:`dhalsim.entities.generic_plc.GenericPlc`.

    :param name: The name of the PLC
    :type name: str
    :param sensors: The sensors the PLC can read
    :type sensors: List[str]
    :param actuators: The actuators the PLC can control
    :type actuators: List[str]
    :param controls: The list of controls that the PLC will enforce
    :type controls: List[ConcreteControl]
    :param mac: The MAC address of the PLC
    :type mac: str, optional
    :param ip: The ip address of the PLC
    :type ip: str, optional
    :param db_path: The path to the sqlite file used as database
    :type db_path: str, optional
    :param db_name: The table name in the sqlite database (used by all PLCs)
    :type db_name: str, optional
    """

    def __init__(self, name: str, sensors: List[str], actuators: List[str],
                 controls: List[ConcreteControl], mac: str = None, ip: str = None, db_path=None, db_name=None):
        """Constructor method
        """
        self.db_path = db_path
        self.db_name = db_name
        self.name = name
        self.sensors = sensors
        self.actuators = actuators
        self.controls = controls
        self.mac = mac
        self.ip = ip

    @property
    def tags(self):
        """
        Returns a list of aal the tags corresponding to this PLC by using the sensors and actuators.

        :return: A list of tags that correspond to this PLC
        :rtype: List
        """
        tags = []
        for sensor in self.sensors:
            tags.append((sensor, 1, "REAL"))
        for actuator in self.actuators:
            tags.append((actuator, 1, "REAL"))
        return tags

    @property
    def server(self):
        """
        Makes a server dict with its IP and tags

        :return: A server dict.
        """
        return {
            'address': self.ip,
            'tags': self.tags
        }

    @property
    def protocol(self):
        """
        Makes a protocol dict with a protocol name (enip), a mode (1) and the `server` dict.
        This dict is required by minicps

        :return: A protocol dict.
        """
        return {
            'name': 'enip',
            'mode': 1,
            'server': self.server
        }

    @property
    def state(self):
        """
        Makes a state dict with a database name, and a database path.
        This should be the same for all PLCs
        This dict is required by minicps

        :return: A state dict.
        """
        return {
            'name': self.db_name,
            'path': self.db_path
        }
