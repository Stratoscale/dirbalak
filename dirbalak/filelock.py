import fcntl
import os
import contextlib
import time

class FileLock:
    def __init__(self, lockFile):
        self._lockFile = lockFile
        if not os.path.isdir(os.path.dirname(lockFile)):
            os.makedirs(os.path.dirname(lockFile))
        self._lockFd = open(lockFile, "w")
        self._pid = os.getpid()

    @contextlib.contextmanager
    def lock(self, timeout=30):
        before = time.time()
        while time.time() - before < timeout:
            if self._acquireAttempt():
                yield
                self._release()
                return
            time.sleep(0.1)
        raise Exception("Timeout waiting for lock '%s' to free up" % self._lockFile)

    def _acquireAttempt(self):
        try:
            fcntl.flock(self._lockFd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except IOError:
            return False

    def _release(self):
        fcntl.flock(self._lockFd, fcntl.LOCK_UN)
