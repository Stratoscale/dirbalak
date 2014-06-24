from upseto import gitwrapper
from dirbalak import config
from dirbalak import filelock
import upseto.manifest
import solvent.manifest
import os


class RepoMirror:
    _LOCK_TIMEOUT = 2 * 60

    def __init__(self, gitURL):
        self._gitURL = gitURL
        self._identifier = gitURL.replace(":", "_").replace("/", "_")
        self._cloneDirectory = os.path.join(config.REPO_MIRRORS_BASEDIR, self._identifier)
        self._lock = filelock.FileLock(self._cloneDirectory + ".lock")
        self._git = None

    def fetch(self):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            if os.path.isdir(self._cloneDirectory):
                self._git = gitwrapper.GitWrapper.existing(self._gitURL, self._cloneDirectory)
                self._git.fetch()
            else:
                os.makedirs(self._cloneDirectory)
                self._git = gitwrapper.GitWrapper.clone(self._gitURL, self._cloneDirectory)

    def upsetoManifest(self, hash):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            self._git.checkout(hash)
            return upseto.manifest.Manifest.fromDirOrNew(self._git.directory())

    def solventManifest(self, hash):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            self._git.checkout(hash)
            return solvent.manifest.Manifest.fromDirOrNew(self._git.directory())

    def hash(self, branch):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            self._git.hash(branch)
