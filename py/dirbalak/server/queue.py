from upseto import gitwrapper
from dirbalak.server import solventofficiallabels
from dirbalak import repomirrorcache
from dirbalak.server import tojs


class Queue:
    NON_MASTER_DEPENDENCIES = 1
    MASTERS_NOT_BUILT = 2
    MASTERS_WHICH_BUILD_ONLY_FAILED = 3
    MASTERS_REBUILD = 4

    def __init__(self, officialObjectStore, multiverse):
        self._officialObjectStore = officialObjectStore
        self._multiverse = multiverse
        self._queue = dict()
        self._reversedMap = dict()
        self._cantBeBuilt = dict()

    def recalculate(self):
        labels = solventofficiallabels.SolventOfficialLabels(self._officialObjectStore)
        self._reversedMap = dict()
        self._cantBeBuilt = dict()
        for dep in self._multiverse.getTraverse().dependencies():
            basename = gitwrapper.originURLBasename(dep.gitURL)
            projectDict = dict(basename=basename, hash=dep.hash)
            unbuiltRequirements = self._unbuiltRequirements(dep.gitURL, dep.hash, labels)
            if unbuiltRequirements:
                self._cantBeBuilt[(basename, dep.hash)] = unbuiltRequirements
                continue
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
        self._queue = queue

    def _put(self, project, priority):
        key = (project['basename'], project['hash'])
        currentPriority = self._reversedMap.get(key, (10000, None))[0]
        if currentPriority > priority:
            project['priority'] = priority
            self._reversedMap[key] = (priority, project)
