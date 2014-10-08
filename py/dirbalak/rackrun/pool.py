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

    def __init__(self, jobQueue, jobDoneCallback):
        self._jobQueue = jobQueue
        self._jobDoneCallback = jobDoneCallback
        self._jobQueueLock = threading.Lock()
        self._hostThreads = []
        threading.Thread.__init__(self)
        self.daemon = True
        threading.Thread.start(self)

    def run(self):
        while True:
            assert self._hostThreads == []
            try:
                client = clientfactory.factory()
                self._connectionToProviderIsLive = True
                client.setConnectionToProviderInterruptedCallback(self._connectionToProviderInterrupted)
                try:
                    self._runPoolOverRackattackClient(client)
                finally:
                    client.close()
            except:
                logging.exception("Rackattack Client failed, retrying")
                time.sleep(10)
            finally:
                for thread in self._hostThreads:
                    logging.info("Waiting for host thread to terminate")
                    thread.join(10 * 60)
                    if thread.isAlive():
                        logging.error("Host thread still alive 10 minutes after rackattack client failure")
                    else:
                        logging.info("Host thread terminated")
            self._hostThreads = []

    def _runPoolOverRackattackClient(self, client):
        lastAllocationFailedException = None
        while self._connectionToProviderIsLive:
            if len(self._hostThreads) >= len(self._NICENESS):
                time.sleep(15)
                continue
            try:
                host = officialbuildhost.OfficialBuildHost(
                    client, self._NICENESS[len(self._hostThreads)])
            except Exception as e:
                if str(e) != lastAllocationFailedException:
                    lastAllocationFailedException = str(e)
                    logging.info(
                        "Unable to allocate more hosts, will not repeat exception: %(exception)s",
                        dict(exception=str(e)))
                time.sleep(15)
                continue
            lastAllocationFailedException = None
            logging.info("Allocated a host")
            self._hostThreads.append(hostthread.HostThread(
                self._jobQueue, self._jobQueueLock, host, self._remove, self._jobDoneCallback))
        logging.warning("Pool loop exists (since connection to provider was interrupted)")

    def _connectionToProviderInterrupted(self):
        logging.warning(
            "Recreating a host pool since connection to provider was interrupted - expect build failure "
            "around here")
        self._connectionToProviderIsLive = False

    def _remove(self, thread):
        logging.info("Host thread terminated, %(threads)d left" % dict(threads=len(self._hostThreads) - 1))
        self._hostThreads.remove(thread)
