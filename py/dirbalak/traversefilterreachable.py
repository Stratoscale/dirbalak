from upseto import gitwrapper


class TraverseFilterReachable:
    def __init__(self, dependencies):
        self._dependencies = dependencies
        self._filtered = set()
        self._reachable = set()

    def includeRecursive(self, projectBasename):
        self._reachable.add(projectBasename)
        while True:
            before = len(self._reachable)
            for dependency in self._dependencies:
                if dependency.requiringURL is None:
                    continue
                basename = gitwrapper.originURLBasename(dependency.requiringURL)
                if basename in self._reachable:
                    self._filtered.add(dependency)
                    self._reachable.add(gitwrapper.originURLBasename(dependency.gitURL))
            if len(self._reachable) == before:
                break

    def dependencies(self):
        return self._filtered
