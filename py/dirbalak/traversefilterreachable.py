from upseto import gitwrapper


class TraverseFilterReachable:
    def __init__(self, dependencies):
        self._dependencies = dependencies
        self._filtered = set()
        self._reachableBasenames = set()
        self._reachableHashes = set()

    def includeRecursiveByBasenames(self, projectBasename):
        self._reachableBasenames.add(projectBasename)
        while True:
            before = len(self._reachableBasenames)
            for dependency in self._dependencies:
                if dependency.requiringURL is None:
                    continue
                basename = gitwrapper.originURLBasename(dependency.requiringURL)
                if basename in self._reachableBasenames:
                    self._filtered.add(dependency)
                    self._reachableBasenames.add(gitwrapper.originURLBasename(dependency.gitURL))
            if len(self._reachableBasenames) == before:
                break

    def includeRecursiveByExactHashes(self, url, hash):
        basename = gitwrapper.originURLBasename(url)
        self._reachableHashes.add((basename, hash))
        while True:
            before = len(self._reachableHashes)
            for dependency in self._dependencies:
                if dependency.requiringURL is None:
                    continue
                basename = gitwrapper.originURLBasename(dependency.requiringURL)
                exact = (basename, dependency.requiringURLHash)
                if exact in self._reachableHashes:
                    self._filtered.add(dependency)
                    basename = gitwrapper.originURLBasename(dependency.gitURL)
                    self._reachableHashes.add((basename, dependency.hash))
            if len(self._reachableHashes) == before:
                break

    def dependencies(self):
        return self._filtered
