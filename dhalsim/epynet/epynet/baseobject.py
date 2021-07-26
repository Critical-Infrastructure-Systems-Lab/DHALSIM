import pandas as pd
import warnings
import weakref


def lazy_property(fn):
    '''Decorator that makes a property lazy-evaluated.
    '''
    attr_name = fn.__name__

    @property
    def _lazy_property(self):
        if attr_name not in self._values.keys():
            self._values[attr_name] = fn(self)
        return self._values[attr_name]
    return _lazy_property

class BaseObject(object):

    static_properties = {}
    properties = {}

    def __init__(self, uid, network):

        # the object index
        self.uid = uid
        # weak reference to the network
        self.network = weakref.ref(network)
        # cache of values
        self._values = {}
        # dictionary of calculation results, only gets
        # filled during solve() method
        self.results = {}
        # list of times
        self.times = []
        # index caching
        self._index = None

    def get_index(self, uid):
        raise NotImplementedError

    def set_object_value(self, code, value):
        raise NotImplementedError

    def get_object_value(self, code):
        raise NotImplementedError

    def reset(self):
        self._values = {}
        self.results = {}
        self.times = []

    def __str__(self):
        return "<epynet."+self.__class__.__name__ + " with id '" + self.uid + "'>"

    def __getattr__(self, name):

        if name in self.static_properties.keys():
            return self.get_property(self.static_properties[name])

        elif name in self.properties.keys():
            if not self.network().solved:
                warnings.warn("requesting dynamic properties from an unsolved network")
            if self.results == {}:
                return self.get_property(self.properties[name])
            else:
                return pd.Series(self.results[name], index=self.times)
        else:
            raise AttributeError('Nonexistant Attribute', name)

    def __setattr__(self, name, value):
        if name in self.properties.keys():
            if name == 'status':
                self.set_static_property(self.properties[name], value)
            else:
                raise AttributeError("Illegal Assignment to Computed Value")

        if name in self.static_properties.keys():
            self.set_static_property(self.static_properties[name], value)
        else:
            super(BaseObject, self).__setattr__(name, value)

    def set_static_property(self, code, value):
        # set network as unsolved
        self.network().solved = False
        self._values[code] = value
        self.set_object_value(code, value)

    def get_property(self, code):
        if code not in self._values.keys():
            self._values[code] = self.get_object_value(code)
        return self._values[code]

