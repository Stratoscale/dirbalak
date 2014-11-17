import collections


class LastValuesCache:
    def __init__(self, maximumValues=100):
        self._maximumValues = maximumValues
        self._cache = collections.OrderedDict()

    def get(self, key):
        return self._cache.get(key, None)

    def set(self, key, value):
        self._cache[key] = value
        while len(self._cache) > self._maximumValues:
            self._cache.pop(0)

    def getter(self, getter, limitKeys=lambda x: True):
        def _get(key):
            value = self.get(key)
            if value is None:
                value = getter(key)
            if limitKeys(key):
                self.set(key, value)
            return value
        return _get
