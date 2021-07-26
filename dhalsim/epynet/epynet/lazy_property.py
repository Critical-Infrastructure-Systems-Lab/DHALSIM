def lazy_property(fn):
    '''Decorator that makes a property lazy-evaluated.
    '''
    attr_name = fn.__name__

    @property
    def _lazy_property(self):
        if attr_name not in self._values:
            self._values[attr_name] = fn(self)
        return self._values[attr_name]
    return _lazy_property
