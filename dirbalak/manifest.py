import yaml
import os
import solvent.manifest


class Manifest:
    _FILENAME = "dirbalak.manifest"

    def __init__(self, data, directory):
        assert isinstance(data, dict)
        self._data = data
        self._directory = directory

    def buildRootFS(self):
        return self._data['buildRootFS']

    def setBuildRootFS(self, value):
        self._assertBasenameInSolventRequirements(value)
        self._data['buildRootFS'] = value

    def save(self):
        with open(self._FILENAME, "w") as f:
            f.write(yaml.dump(self._data, default_flow_style=False))

    @classmethod
    def fromDir(cls, directory):
        filename = os.path.join(directory, cls._FILENAME)
        with open(filename) as f:
            data = yaml.load(f.read())
        return cls(data, directory)

    @classmethod
    def fromDirOrNew(cls, directory):
        if cls._exists(directory):
            return cls.fromDir(directory)
        else:
            return cls(dict(), directory)

    @classmethod
    def fromLocalDir(cls):
        return cls.fromDir('.')

    @classmethod
    def fromLocalDirOrNew(cls):
        return cls.fromDirOrNew('.')

    @classmethod
    def _exists(cls, directory):
        return os.path.exists(os.path.join(directory, cls._FILENAME))

    def _assertBasenameInSolventRequirements(self, basename):
        solventManifest = solvent.manifest.Manifest.fromDir(self._directory)
        solventManifest.findRequirementByBasename(basename)
