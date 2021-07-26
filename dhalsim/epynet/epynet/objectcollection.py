import collections
import pandas as pd

class ObjectCollection(dict):

    # magic methods to transform collection attributes to Pandas Series or, if we return classes, another list
    def __getattr__(self,name):
        values = {}

        for key, item in self.items():
            values[item.uid] = getattr(item,name)

        if isinstance(values[item.uid], pd.Series):
            return pd.concat(values,axis=1)

        return pd.Series(values)

    def __setattr__(self, name, value):

        if isinstance(value, pd.Series):
            for key, item in self.items():
                setattr(item,name,value[item.uid])
            return

        for key, item in self.items():
            setattr(item,name,value)

    def __getitem__(self, key):
        # support for index slicing through pandas
        if isinstance(key, pd.Series):
            ids = key[key==True].index
            return_dict = ObjectCollection()
            for uid in ids:
                obj = super(ObjectCollection, self).__getitem__(uid)
                return_dict[uid] = obj
            return return_dict

        return super(ObjectCollection, self).__getitem__(key)

    def __iter__(self):
        return iter(self.values())
