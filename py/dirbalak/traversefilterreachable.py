from upseto import gitwrapper


class TraverseFilterReachable:
    def __init__(self, dependencies):
        self._dependencies = dependencies
        self._filtered = set()
        self._reachableHashes = set()

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
