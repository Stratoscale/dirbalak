from upseto import gitwrapper
from upseto import run
from dirbalak import config
from dirbalak import filelock
from dirbalak import manifest
import upseto.manifest
import solvent.manifest
import os


class RepoMirror:
    _LOCK_TIMEOUT = 2 * 60

    def __init__(self, gitURL):
        self._gitURL = gitURL
        self._identifier = gitURL.replace(":", "_").replace("/", "_").replace("@", "_")
        self._cloneDirectory = os.path.join(config.REPO_MIRRORS_BASEDIR, self._identifier)
        self._lock = filelock.FileLock(self._cloneDirectory + ".lock")
        self._git = None

    def gitURL(self):
        return self._gitURL

    def existing(self):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            if not os.path.isdir(self._cloneDirectory):
                raise Exception("'%s' not cloned, can't assume existing" % self._gitURL)
            self._git = gitwrapper.GitWrapper.existing(self._gitURL, self._cloneDirectory)

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

    def dirbalakManifest(self, hash):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            self._git.checkout(hash)
            return manifest.Manifest.fromDirOrNew(self._git.directory())

    def hash(self, branch):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            return self._git.hash(branch)

    def branchName(self, hash):
        masterHash = self.hash('origin/master')
        if hash == masterHash:
            return 'origin/master'
        else:
            return hash

    def replicate(self, destination):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            run.run(["sudo", "cp", "-a", self._cloneDirectory, destination + "/"])

    def run(self, command, hash):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            self._git.checkout(hash)
            return run.run(command, cwd=self._git.directory())

    def commitTimestamp(self, hash):
        return int(self._git.run(['log', '-1', '--pretty=tformat:%at', hash]).strip())

    def distanceFromMaster(self, hash):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            if hash == 'origin/master' or hash == self._git.hash('origin/master'):
                return None
            result = {}
            timeDeltaSeconds = self.commitTimestamp('origin/master') - self.commitTimestamp(hash)
            if timeDeltaSeconds > 0:
                result['time'] = timeDeltaSeconds
            left, right = self._git.run(
                ['rev-list', '--count', '--left-right', '%s...origin/master' % hash]).strip().split('\t')
            result['commits'] = int(left) + int(right)
            return result
