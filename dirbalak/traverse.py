from dirbalak import repomirrorcache
import collections


Dependency = collections.namedtuple("Dependency", "gitURL hash requiringURL requiringURLHash type")


class Traverse:
    def __init__(self, visitMaster):
        self._visitMaster = visitMaster
        self._visitedTuples = set()

    def traverse(self, gitURL, hash):
        for x in self._traverse(gitURL, hash, None, None, 'root'):
            yield x

    def _traverse(self, gitURL, hash, requiringURL, requiringURLHash, type):
        tuple = gitURL, hash, requiringURL, requiringURLHash
        if tuple in self._visitedTuples:
            return
        self._visitedTuples.add(tuple)

        dep = Dependency(
            gitURL=gitURL, hash=hash, requiringURL=requiringURL,
            requiringURLHash=requiringURLHash, type=type)
        yield dep

        mirror = repomirrorcache.get(gitURL)
        if self._visitMaster:
            if mirror.hash('origin/master') != hash:
                for x in self._traverse(gitURL, 'origin/master', None, None, 'master'):
                    yield x
        for requirement in mirror.upsetoManifest(hash).requirements():
            for x in self._traverse(requirement['originURL'], requirement['hash'], gitURL, hash, 'upseto'):
                yield x
        for requirement in mirror.solventManifest(hash).requirements():
            for x in self._traverse(requirement['originURL'], requirement['hash'], gitURL, hash, 'solvent'):
                yield x
