from . import epanet2
import weakref


class Pattern(object):

    def __init__(self, uid, network):
        self.uid = uid
        self.network = weakref.ref(network)

    def __str__(self):
        return "<epynet."+self.__class__.__name__ + " with id '" + self.uid + "'>"

    @property
    def index(self):
        return self.network().ep.ENgetpatternindex(self.uid)

    @property
    def values(self):
        values = []
        n_values = self.network().ep.ENgetpatternlen(self.index)
        for n in range(1, n_values+1):
            values.append(self.network().ep.ENgetpatternvalue(self.index, n))
        return values

    @values.setter
    def values(self, value):
        self.network().ep.ENsetpattern(self.index, value)
