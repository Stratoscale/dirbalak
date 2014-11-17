from upseto import gitwrapper
from upseto import run
from dirbalak import config
from dirbalak import filelock
from dirbalak import manifest
from dirbalak import lastvaluescache
import upseto.manifest
import solvent.manifest
import os
import time


class RepoMirror:
    _LOCK_TIMEOUT = 2 * 60

    def __init__(self, gitURL):
        self._gitURL = gitURL
        self._gitHTTPSURL = self._httpsURL(gitURL)
        self._identifier = gitURL.replace(":", "_").replace("/", "_").replace("@", "_")
        self._cloneDirectory = os.path.join(config.REPO_MIRRORS_BASEDIR, self._identifier)
        self._lock = filelock.FileLock(self._cloneDirectory + ".lock")
        self._git = None
        self._upsetoManifestsCache = lastvaluescache.LastValuesCache()
        self._solventManifestsCache = lastvaluescache.LastValuesCache()
        self._dirbalakManifestsCache = lastvaluescache.LastValuesCache()
        self._hashExistsCache = lastvaluescache.LastValuesCache()
        self.upsetoManifest = self._upsetoManifestsCache.getter(
            self._upsetoManifestGetter, self._hashIsHex)
        self.solventManifest = self._solventManifestsCache.getter(
            self._solventManifestGetter, self._hashIsHex)
        self.dirbalakManifest = self._dirbalakManifestsCache.getter(
            self._dirbalakManifestGetter, self._hashIsHex)

    def gitURL(self):
        return self._gitURL

    def existing(self):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            if not os.path.isdir(self._cloneDirectory):
                raise Exception("'%s' not cloned, can't assume existing" % self._gitURL)
            self._git = gitwrapper.GitWrapper.existing(self._gitHTTPSURL, self._cloneDirectory)

    def fetch(self):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            if os.path.isdir(self._cloneDirectory):
                self._git = gitwrapper.GitWrapper.existing(self._gitHTTPSURL, self._cloneDirectory)
                self._git.fetch()
            else:
                os.makedirs(self._cloneDirectory)
                self._git = gitwrapper.GitWrapper.clone(self._gitHTTPSURL, self._cloneDirectory)

    def _upsetoManifestGetter(self, hash):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            self._git.checkout(hash)
            return upseto.manifest.Manifest.fromDirOrNew(self._git.directory())

    def _hashIsHex(self, hash):
        return len(hash) == 40

    def _solventManifestGetter(self, hash):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            self._git.checkout(hash)
            return solvent.manifest.Manifest.fromDirOrNew(self._git.directory())

    def _dirbalakManifestGetter(self, hash):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            self._git.checkout(hash)
            return manifest.Manifest.fromDirOrNew(self._git.directory())

    def hash(self, branch):
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            return self._git.hash(branch)

    def hashExists(self, branch):
        if self._hashExistsCache.get(branch):
            return True
        with self._lock.lock(timeout=self._LOCK_TIMEOUT):
            try:
                self._git.checkout(branch)
                self._hashExistsCache.set(branch, True)
                return True
            except:
                return False

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
            result = dict(broken=False)
            try:
                left, right = self._git.run(
                    ['rev-list', '--count', '--left-right', '%s...origin/master' % hash]).strip().split('\t')
                left, right = int(left), int(right)
                result['commits'] = left + right
                if right > 0:
                    timeDeltaSeconds = time.time() - self.commitTimestamp('origin/master~%d' % (right - 1))
                    if timeDeltaSeconds > 0:
                        result['time'] = timeDeltaSeconds
            except:
                result['broken'] = True
            return result

    def _httpsURL(self, gitURL):
        PREFIX = "git@github.com:"
        SUFFIX = ".git"
        if gitURL.startswith(PREFIX):
            result = "https://github.com/" + gitURL[len(PREFIX):]
            if not result.endswith(SUFFIX):
                result += SUFFIX
            return result
        return gitURL
