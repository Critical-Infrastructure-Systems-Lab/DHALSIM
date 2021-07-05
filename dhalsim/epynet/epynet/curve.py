from . import epanet2
import weakref

class Curve(object):

    def __init__(self, uid, network):
        self.uid = uid
        self.network = weakref.ref(network)

    def __str__(self):
        return "<epynet."+self.__class__.__name__ + " with id '" + self.uid + "'>"

    @property
    def index(self):
        return self.network().ep.ENgetcurveindex(self.uid)

    @property
    def values(self):
        return self.network().ep.ENgetcurve(self.index)

    @values.setter
    def values(self, value):
        self.network().ep.ENsetcurve(self.index, value)
