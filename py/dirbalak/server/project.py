from dirbalak import repomirrorcache
from upseto import gitwrapper


class Project:
    def __init__(self, gitURL, owner, group, fetchThread, model):
        self._gitURL = gitURL
        self._owner = owner
        self._group = group
        self._fetchThread = fetchThread
        self._model = model
        self._basename = gitwrapper.originURLBasename(gitURL)
        repomirrorcache.fetch = False
        self._mirror = repomirrorcache.get(gitURL)
        self._traverse = None

    def gitURL(self):
        return self._gitURL

    def group(self):
        return self._group

    def basename(self):
        return self._basename

    def needsFetch(self, reason):
        self._model.appendEvent("project/" + self._basename, "Needs Fetch due to %s" % reason)
        self._fetchThread.enqueue(self._mirror)

    def setTraverse(self, traverse):
        self._traverse = traverse
        self._addToProjectsList()
        asDict = dict(
            name=self._basename,
            gitURL=self._gitURL, owner=self._owner, group=self._group,
            lastCommit=self._mirror.commitTimestamp('origin/master'),
            dependsOn=self._dependsOn(), dependedBy=self._dependedBy())
        self._model.set("project/%s" % self._basename, asDict)

    def _addToProjectsList(self):
        project = dict(
            basename=self._basename, gitURL=self._gitURL,
            owner=self._owner, group=self._group)
        self._model.addToProjectsList(project)

    def _dependsOn(self):
        result = []
        for dep in self._traverse.dependencies():
            if dep.requiringURL != self._gitURL:
                continue
            if dep.requiringURLHash != 'origin/master':
                continue
            mirror = repomirrorcache.get(dep.gitURL)
            result.append(dict(
                basename=gitwrapper.originURLBasename(dep.gitURL),
                hash=dep.hash,
                distanceFromMaster=mirror.distanceFromMaster(dep.hash),
                type=dep.type))
        return result

    def _dependedBy(self):
        result = []
        for dep in self._traverse.dependencies():
            if dep.gitURL != self._gitURL:
                continue
            if dep.requiringURLHash != 'origin/master':
                continue
            result.append(dict(
                basename=gitwrapper.originURLBasename(dep.requiringURL),
                hash=dep.hash,
                distanceFromMaster=self._mirror.distanceFromMaster(dep.hash),
                type=dep.type))
        return result
