from upseto import gitwrapper
from dirbalak.rackrun import solventofficiallabels
from dirbalak.rackrun import buildstate
from dirbalak.rackrun import traversefilterbuildbanned
from dirbalak import repomirrorcache
from dirbalak.server import tojs
import collections
import logging


class JobQueue:
    NON_MASTER_DEPENDENCIES = 1
    MASTERS_NOT_BUILT = 2
    MASTERS_WHICH_BUILD_ONLY_FAILED = 3
    MASTERS_REBUILD = 4

    def __init__(self, officialObjectStore, multiverse):
        self._officialObjectStore = officialObjectStore
        self._multiverse = multiverse
        self._buildState = buildstate.BuildState()
        self._queue = dict()
        self._reversedMap = dict()
        self._cantBeBuilt = dict()
        self._rotation = {
            self.NON_MASTER_DEPENDENCIES: 0,
            self.MASTERS_NOT_BUILT: 0,
            self.MASTERS_WHICH_BUILD_ONLY_FAILED: 0,
            self.MASTERS_REBUILD: 0}
        self._interPriorityRotation = [
            self.NON_MASTER_DEPENDENCIES, self.MASTERS_NOT_BUILT,
            self.MASTERS_WHICH_BUILD_ONLY_FAILED, self.MASTERS_REBUILD]

    def next(self):
        self._interPriorityRotation.append(self._interPriorityRotation.pop(0))
        for key in self._interPriorityRotation:
            for job in self._queue.get(key, []):
                if not job['inProgress']:
                    job['inProgress'] = True
                    self._buildState.inProgress(job['gitURL'], job['hexHash'])
                    self._rotateQueueByOne(self._queue, key)
                    self._toJS()
                    return job

    def done(self, job, success):
        self._buildState.done(job['gitURL'], job['hexHash'], success)
        self.recalculate()

    def queue(self):
        return self._queue

    def cantBeBuilt(self):
        return self._cantBeBuilt

    def recalculate(self):
        labels = solventofficiallabels.SolventOfficialLabels(self._officialObjectStore)
        self._reversedMap = dict()
        self._cantBeBuilt = dict()
        filtered = traversefilterbuildbanned.TraverseFilterBuildBanned(
            self._multiverse,
            self._multiverse.getTraverse().dependencies())
        for dep in filtered.dependencies():
            basename = gitwrapper.originURLBasename(dep.gitURL)
            if basename not in self._multiverse.projects:
                logging.info("Will not build project '%(project)s' not in the multiverse file", dict(
                    project=basename))
                continue
            project = self._multiverse.projects[basename]
            hexHash = dep.hash if dep.hash != 'origin/master' else dep.masterHash
            projectDict = dict(
                basename=basename, hash=dep.hash, gitURL=dep.gitURL, submit=False,
                hexHash=hexHash, buildRootFS=project.buildRootFS())
            buildState = self._buildState.get(dep.gitURL, hexHash)
            projectDict.update(buildState)
            unbuiltRequirements = self._unbuiltRequirements(dep.gitURL, dep.hash, labels)
            if unbuiltRequirements:
                self._cantBeBuilt[(basename, dep.hash)] = unbuiltRequirements
                continue
            if project.buildBanned():
                logging.info(
                    "Will not put project '%(project)s' in queue, is build banned '%(message)s'",
                    dict(project=basename, message=project.buildBanned()))
                continue
            if dep.hash == "origin/master":
                mirror = repomirrorcache.get(dep.gitURL)
                if labels.built(basename, mirror.hash('origin/master')):
                    self._put(projectDict, self.MASTERS_REBUILD)
                else:
                    if buildState['failures'] > 0 and buildState['successes'] == 0:
                        projectDict['submit'] = True
                        self._put(projectDict, self.MASTERS_WHICH_BUILD_ONLY_FAILED)
                    else:
                        projectDict['submit'] = True
                        self._put(projectDict, self.MASTERS_NOT_BUILT)
            else:
                if not labels.built(basename, dep.hash):
                    projectDict['submit'] = True
                    projectDict['requiringBasename'] = gitwrapper.originURLBasename(dep.requiringURL)
                    self._put(projectDict, self.NON_MASTER_DEPENDENCIES)
        self._reverseMap()
        self._toJS()

    def _toJS(self):
        tojs.set('queue/queue', self._queue)
        tojs.set('queue/cantBeBuilt', [
            dict(basename=basename, hash=hash, unbuiltRequirements=unbuiltRequirements)
            for (basename, hash), unbuiltRequirements in self._cantBeBuilt.iteritems()])

    def _unbuiltRequirements(self, gitURL, hash, labels):
        result = []
        for dep in self._multiverse.getTraverse().dependencies():
            if dep.requiringURL != gitURL or dep.requiringURLHash != hash:
                continue
            basename = gitwrapper.originURLBasename(dep.gitURL)
            mirror = repomirrorcache.get(dep.gitURL)
            hexHash = dep.hash if dep.hash != 'origin/master' else mirror.hash('origin/master')
            if not labels.built(basename, hexHash):
                result.append(dict(basename=basename, hash=dep.hash))
        return result

    def _reverseMap(self):
        queue = dict()
        for priority, project in self._reversedMap.values():
            queue.setdefault(priority, []).append(project)
        for key in queue:
            deque = collections.deque(queue[key])
            deque.rotate(self._rotation[key])
            queue[key] = list(deque)
        self._queue = queue

    def _rotateQueueByOne(self, queue, key):
        assert key in queue
        self._rotation[key] -= 1
        deque = collections.deque(queue[key])
        deque.rotate(-1)
        queue[key] = list(deque)

    def _put(self, project, priority):
        key = (project['basename'], project['hash'])
        currentPriority = self._reversedMap.get(key, (10000, None))[0]
        if currentPriority > priority:
            project['priority'] = priority
            self._reversedMap[key] = (priority, project)
