""" EPYNET Classes """
from . import epanet2
from .baseobject import BaseObject, lazy_property
from .curve import Curve

class Link(BaseObject):
    """ EPANET Link Class """

    properties = {'flow': epanet2.EN_FLOW}

    def __init__(self, uid, network):
        super(Link, self).__init__(uid, network)
        self.from_node = None
        self.to_node = None

    def get_index(self, uid):
        if not self._index:
            self._index = self.network().ep.ENgetlinkindex(uid)
        return self._index

    def set_object_value(self, code, value):
        index = self.get_index(self.uid)
        return self.network().ep.ENsetlinkvalue(index, code, value)

    def get_object_value(self, code):
        index = self.get_index(self.uid)
        return self.network().ep.ENgetlinkvalue(index, code)

    @property
    def index(self):
        return self.get_index(self.uid)

    # upstream and downstream nodes
    @lazy_property
    def upstream_node(self):
        if self.flow >= 0:
            return self.from_node
        else:
            return self.to_node

    @lazy_property
    def downstream_node(self):
        if self.flow >= 0:
            return self.to_node
        else:
            return self.from_node

    @lazy_property
    def vertices(self):
        return self.network().get_vertices(self.uid)

    @lazy_property
    def path(self):
        return [self.from_node.coordinates] + self.vertices + [self.to_node.coordinates]

class Pipe(Link):
    """ EPANET Pipe Class """
    link_type = 'pipe'

    static_properties = {'diameter': epanet2.EN_DIAMETER, 'length': epanet2.EN_LENGTH,
                         'roughness': epanet2.EN_ROUGHNESS, 'minorloss': epanet2.EN_MINORLOSS,
                         'initstatus': epanet2.EN_INITSTATUS, 'status': epanet2.EN_STATUS}
    properties = {'flow': epanet2.EN_FLOW, 'headloss': epanet2.EN_HEADLOSS, 'velocity': epanet2.EN_VELOCITY}

    @lazy_property
    def check_valve(self):
        type_code = self.network().ep.ENgetlinktype(self.index)
        return (type_code == epanet2.EN_CVPIPE)


class Pump(Link):
    """ EPANET Pump Class """
    link_type = 'pump'

    static_properties = {'length': epanet2.EN_LENGTH, 'initstatus': epanet2.EN_INITSTATUS, 
                         'speed': epanet2.EN_INITSETTING}
    properties = {'flow': epanet2.EN_FLOW, 'energy': epanet2.EN_ENERGY, 'status': epanet2.EN_STATUS,
                  'velocity': epanet2.EN_VELOCITY}

    @property
    def velocity(self):
        return 1.0

    @property
    def curve(self):
        curve_index = self.network().ep.ENgetheadcurveindex(self.index)
        curve_uid = self.network().ep.ENgetcurveid(curve_index)
        return Curve(curve_uid, self.network())

    @curve.setter
    def curve(self, value):
        if isinstance(value, int):
            curve_index = value
        elif isinstance(value, str):
            curve_index = self.network().ep.ENgetcurveindex(value)
        elif isinstance(value, Curve):
            curve_index = value.index
        else:
            raise ValueError("Invalid input for curve")

        # set network as unsolved
        self.network().solved = False
        self.network().ep.ENsetheadcurveindex(self.index, curve_index)


class Valve(Link):
    """ EPANET Valve Class """

    static_properties = {'setting': epanet2.EN_INITSETTING, 'initstatus': epanet2.EN_INITSTATUS,
                         'diameter': epanet2.EN_DIAMETER}
    properties = {'velocity': epanet2.EN_VELOCITY, 'flow': epanet2.EN_FLOW, 'status': epanet2.EN_STATUS}

    link_type = 'valve'

    types = {3: "PRV", 4: "PSV", 5: "PBV", 6: "FCV", 7: "TCV", 8: "GPV"}

    @lazy_property
    def valve_type(self):
        try:
            type_code = self.network().ep.ENgetlinktype(self.index)
        except Exception as e:
            print(e)
            raise e
        return self.types[type_code]
