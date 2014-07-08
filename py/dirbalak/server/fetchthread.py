import threading
import logging
import Queue
from dirbalak.server import suicide


class FetchThread(threading.Thread):
    def __init__(self):
        self._queue = Queue.Queue()
        self._event = threading.Event()
        self._traverseNeeded = False
        self._hashes = dict()
        threading.Thread.__init__(self)
        self.daemon = True

    def start(self, multiverse):
        self._multiverse = multiverse
        threading.Thread.start(self)

    def enqueue(self, mirror):
        self._queue.put(mirror)

    def run(self):
        try:
            while True:
                self._work()
        except:
            logging.exception("Fetch Thread terminates, commiting suicide")
            suicide.killSelf()

    def _work(self):
        mirror = self._queue.get()
        logging.info("Fetching gitURL %(url)s", dict(url=mirror.gitURL()))
        mirror.fetch()
        hash = mirror.hash('origin/master')
        if hash != self._hashes.get(mirror.gitURL(), None):
            self._traverseNeeded = True
        self._hashes[mirror.gitURL()] = hash
        if self._traverseNeeded and self._queue.empty():
            self._traverseNeeded = False
            self._multiverse.traverse()
