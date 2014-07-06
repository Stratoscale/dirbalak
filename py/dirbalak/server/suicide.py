import os
import time
import signal


def killSelf():
    for i in xrange(5):
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(10)
    os.kill(os.getpid(), signal.SIGKILL)
