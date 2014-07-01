from dirbalak import manifest


class SetOperation:
    def __init__(self, key, value):
        self._key = key
        self._value = value

    def go(self):
        mani = manifest.Manifest.fromLocalDirOrNew()
        if self._key == "buildRootFSRepositoryBasename":
            mani.setBuildRootFSRepositoryBasename(self._value)
        elif self._key == "buildRootFSLabel":
            mani.setBuildRootFSLabel(self._value)
        else:
            raise AssertionError("Unknown key %s" % self._key)
        mani.save()
