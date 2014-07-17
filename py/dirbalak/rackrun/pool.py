from rackattack import clientfactory
from dirbalak.rackrun import officialbuildhost
from dirbalak.rackrun import hostthread
import logging
import threading
import time


class Pool(threading.Thread):
    _TIMEOUT = 8 * 60
    _NICENESS = [0]
#    _NICENESS = [0, 0.2, 0.8, 0.9, 1]

    def __init__(self, queue):
        self._queue = queue
        self._queueLock = threading.Lock()
        self._client = clientfactory.factory()
        self._hostThreads = []
        threading.Thread.__init__(self)
        self.daemon = True
        threading.Thread.start(self)

    def run(self):
        lastAllocationFailedException = None
        while True:
            if len(self._hostThreads) >= len(self._NICENESS):
                time.sleep(15)
                continue
            try:
                host = officialbuildhost.OfficialBuildHost(
                    self._client, self._NICENESS[len(self._hostThreads)])
            except Exception as e:
                if str(e) != lastAllocationFailedException:
                    lastAllocationFailedException = str(e)
                    logging.info(
                        "Unable to allocate more hosts, will not repeat exception: %(exception)s",
                        dict(exception=str(e)))
                time.sleep(15)
                continue
            logging.info("Allocated a host")
            self._hostThreads.append(hostthread.HostThread(
                self._queue, self._queueLock, host, self._remove))

    def _remove(self, thread):
        logging.info("Host thread terminated")
        self._hostThreads.remove(thread)
