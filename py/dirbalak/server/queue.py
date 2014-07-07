from upseto import gitwrapper
from dirbalak.server import solventofficiallabels
from dirbalak import repomirrorcache


class Queue:
    NON_MASTER_DEPENDENCIES = 1
    MASTERS_NOT_BUILT = 2
    MASTERS_WHICH_BUILD_ONLY_FAILED = 3
    MASTERS_REBUILD = 4

    def __init__(self, model, officialObjectStore):
        self._model = model
        self._officialObjectStore = officialObjectStore
        self._queue = dict()
        self._reversedMap = dict()

    def calculate(self, traverse):
        labels = solventofficiallabels.SolventOfficialLabels(self._officialObjectStore)
        self._reversedMap = dict()
        for dep in traverse.dependencies():
            basename = gitwrapper.originURLBasename(dep.gitURL)
            projectDict = dict(basename=basename, hash=dep.hash)
            if dep.hash == "origin/master":
                mirror = repomirrorcache.get(dep.gitURL)
                if labels.built(basename, mirror.hash('origin/master')):
                    self._put(projectDict, self.MASTERS_REBUILD)
                else:
                    self._put(projectDict, self.MASTERS_NOT_BUILT)
            else:
                if not labels.built(basename, dep.hash):
                    projectDict['requiringBasename'] = gitwrapper.originURLBasename(dep.requiringURL)
                    self._put(projectDict, self.NON_MASTER_DEPENDENCIES)
        self._reverseMap()
        self._model.set('queue/queue', self._queue)

    def _reverseMap(self):
        queue = dict()
        for priority, project in self._reversedMap.values():
            queue.setdefault(priority, []).append(project)
        self._queue = queue

    def _put(self, project, priority):
        key = (project['basename'], project['hash'])
        currentPriority = self._reversedMap.get(key, (10000, None))[0]
        if currentPriority > priority:
            project['priority'] = priority
            self._reversedMap[key] = (priority, project)
