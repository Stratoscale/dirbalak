import logging
import threading
import time
import datetime
from dirbalak.rackrun import config
from dirbalak.server import tojs


class HostThread(threading.Thread):
    def __init__(self, queue, queueLock, host, removeCallback):
        self._queue = queue
        self._queueLock = queueLock
        self._host = host
        self._removeCallback = removeCallback
        self._host.setForceReleaseCallback(self._allocationForcelyReleased)
        threading.Thread.__init__(self)
        self.daemon = True
        threading.Thread.start(self)

    def run(self):
        try:
            logging.info("Setting up host")
            self._host.setUp(config.GITHUB_NETRC_FILE)
            logging.info("Done setting up host")
            tojs.addToBuildHostsList(self._host.ipAddress())
            try:
                self._hostEventsKey = "buildHost/%s" + self._host.ipAddress()
                self._jobToJS(None)
                while True:
                    self._buildOne()
            finally:
                tojs.removeFromBuildHostsList(self._host.ipAddress())
        except:
            logging.exception("rack run host thread dies")
        finally:
            self._removeCallback(self)

    def _jobToJS(self, job):
        tojs.set("buildHost/%s" % self._host.ipAddress(), dict(ipAddress=self._host.ipAddress(), job=job))
        if job is None:
            tojs.appendEvent(self._hostEventsKey, dict(type="text", text="Became idle"))
        else:
            tojs.appendEvent(self._hostEventsKey, dict(
                type="job_started", host=self._host.ipAddress(), job=job))

    def _projectEvent(self, job, buildID, type):
        tojs.appendEvent("project/" + job['basename'], dict(
            type=type, job=job, buildID=buildID, host=self._host.ipAddress()))

    def _allocationForcelyReleased(self):
        self._host.close()

    def _buildOne(self):
        with self._queueLock:
            job = self._queue.next()
        if job is None:
            time.sleep(15)
            return
        logging.info("Received job, building: '%(job)s'", dict(job=job))
        buildID = "%s_%s" % (datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), job['hexHash'])
        self._jobToJS(job)
        self._projectEvent(job, buildID, "build_started")
        try:
            self._host.build(
                gitURL=job['gitURL'], hash=job['hexHash'], submit=job['submit'],
                buildRootFS=job['buildRootFS'], logbeamBuildID=buildID)
        except:
            logging.exception("Job failed: '%(job)s'", dict(job=job))
            with self._queueLock:
                self._queue.done(job, False)
            tojs.appendEvent(self._hostEventsKey, dict(type="text", text="Job failed"))
            self._projectEvent(job, buildID, "build_failed")
            raise
        else:
            logging.info("Job succeeded: '%(job)s'", dict(job=job))
            with self._queueLock:
                self._queue.done(job, True)
            self._projectEvent(job, buildID, "build_succeeded")
            tojs.appendEvent(self._hostEventsKey, dict(type="text", text="Job succeeded"))
        finally:
            self._jobToJS(None)
