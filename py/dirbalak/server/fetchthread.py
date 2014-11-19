import threading
import logging
import Queue
from dirbalak.server import suicide
import multiprocessing.pool
import time


class FetchThread(threading.Thread):
    def __init__(self):
        CONCURRENCY = 16
        self._pool = multiprocessing.pool.ThreadPool(CONCURRENCY)
        self._enqueued = 0
        self._dequeued = 0
        self._queue = Queue.Queue()
        self._traverseNeeded = False
        self._hashes = dict()
        self._postTraverseCallbacks = []
        threading.Thread.__init__(self)
        self.daemon = True

    def start(self, multiverse):
        self._multiverse = multiverse
        threading.Thread.start(self)

    def enqueue(self, mirror):
        self._enqueued += 1
        self._pool.apply_async(self._fetchSubthread, args=(mirror,))

    def mustTraverse(self):
        self._traverseNeeded = True

    def _fetchSubthread(self, mirror):
        logging.info("Fetching gitURL %(url)s", dict(url=mirror.gitURL()))
        try:
            mirror.fetch()
        except:
            logging.exception("Unable to fetch '%(url)s'", dict(url=mirror.gitURL()))
            time.sleep(10)
            self.enqueue(mirror)
            self._dequeued += 1
            return
        self._queue.put(mirror)

    def addPostTraverseCallback(self, callback):
        self._postTraverseCallbacks.append(callback)

    def run(self):
        try:
            while True:
                self._work()
        except:
            logging.exception("Fetch Thread terminates, commiting suicide")
            suicide.killSelf()

    def _work(self):
        mirror = self._queue.get()
        self._dequeued += 1
        hash = mirror.hash('origin/master')
        if hash != self._hashes.get(mirror.gitURL(), None):
            self._traverseNeeded = True
        self._hashes[mirror.gitURL()] = hash
        if self._traverseNeeded and self._dequeued == self._enqueued:
            logging.info("Fetched all, starting traverse")
            self._traverseNeeded = False
            self._multiverse.traverse()
            for callback in self._postTraverseCallbacks:
                callback()
        else:
            logging.info("Still missing %(fetches)d fetches", dict(
                fetches=self._enqueued - self._dequeued))
