from upseto import gitwrapper
from dirbalak import traversefilterreachable


class TraverseFilterBuildBanned:
    def __init__(self, multiverse, dependencies):
        self._multiverse = multiverse
        self._dependencies = dependencies
        self._filtered = self._filterOutBuildBanned()
        self._filter = traversefilterreachable.TraverseFilterReachable(self._filtered)
        self._roots = []
        self._reachNonBanned()
        self._reachable = self._filter.dependencies()
        self._result = self._roots + list(self._filter.dependencies())

    def dependencies(self):
        return self._result

    def _filterOutBuildBanned(self):
        return [dep for dep in self._dependencies if not self._gitURLBuildBanned(dep.requiringURL)]

    def _gitURLBuildBanned(self, gitURL):
        if gitURL is None:
            return False
        basename = gitwrapper.originURLBasename(gitURL)
        project = self._multiverse.projects.get(basename, None)
        if project is None:
            return True
        return bool(project.buildBanned())

    def _reachNonBanned(self):
        for dependency in self._filtered:
            if dependency.type != 'master':
                continue
            if self._gitURLBuildBanned(dependency.gitURL):
                continue
            self._roots.append(dependency)
            self._filter.includeRecursiveByExactHashes(dependency.gitURL, dependency.hash)
