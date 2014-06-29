from dirbalak import repomirrorcache
import collections


Dependency = collections.namedtuple(
    "Dependency", "gitURL hash requiringURL requiringURLHash type masterHash")


class Traverse:
    def __init__(self):
        self._visitedTuples = set()

    def traverse(self, gitURL, hash):
        for x in self._traverse(gitURL, hash, None, None, 'root'):
            yield x

    def _traverse(self, gitURL, hash, requiringURL, requiringURLHash, type):
        tuple = gitURL, hash, requiringURL, requiringURLHash
        if tuple in self._visitedTuples:
            return
        self._visitedTuples.add(tuple)

        mirror = repomirrorcache.get(gitURL)
        masterHash = mirror.hash('origin/master')
        if hash == masterHash:
            hash = 'origin/master'

        dep = Dependency(
            gitURL=gitURL, hash=hash, requiringURL=requiringURL,
            requiringURLHash=requiringURLHash, type=type, masterHash=masterHash)
        yield dep

        for x in self._traverse(gitURL, 'origin/master', None, None, 'master'):
            yield x
        for requirement in mirror.upsetoManifest(hash).requirements():
            for x in self._traverse(requirement['originURL'], requirement['hash'], gitURL, hash, 'upseto'):
                yield x
        for requirement in mirror.solventManifest(hash).requirements():
            for x in self._traverse(requirement['originURL'], requirement['hash'], gitURL, hash, 'solvent'):
                yield x
