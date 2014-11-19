import yaml
import os
import solvent.manifest


class Manifest:
    _FILENAME = "dirbalak.manifest"

    def __init__(self, data, directory):
        assert isinstance(data, dict)
        self._data = data
        self._directory = directory

    def buildRootFSRepositoryBasename(self):
        return self._data['BUILD_ROOTFS_REPOSITORY_BASENAME']

    def buildRootFSLabel(self):
        return self._data['BUILD_ROOTFS_LABEL']

    def makefileFilename(self):
        return self._data.get('MAKEFILE_FILENAME', 'Makefile')

    def setBuildRootFSRepositoryBasename(self, value):
        if 'BUILD_ROOTFS_LABEL' in self._data:
            raise Exception(
                "Manifest may not contain both BUILD_ROOTFS_LABEL and BUILD_ROOTFS_REPOSITORY_BASENAME")
        self._assertBasenameInSolventRequirements(value)
        self._data['BUILD_ROOTFS_REPOSITORY_BASENAME'] = value

    def setBuildRootFSLabel(self, value):
        if 'BUILD_ROOTFS_REPOSITORY_BASENAME' in self._data:
            raise Exception(
                "Manifest may not contain both BUILD_ROOTFS_LABEL and BUILD_ROOTFS_REPOSITORY_BASENAME")
        self._data['BUILD_ROOTFS_LABEL'] = value

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
