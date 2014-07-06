from dirbalak import repomirrorcache
from upseto import gitwrapper
import collections
import logging


Dependency = collections.namedtuple(
    "Dependency", "gitURL hash requiringURL requiringURLHash type masterHash")


class Traverse:
    def __init__(self):
        self._visitedTuples = set()
        self._dependencies = []

    def dependencies(self):
        return self._dependencies

    def traverse(self, gitURL, hash):
        mirror = repomirrorcache.get(gitURL)
        hash = mirror.branchName(hash)
        self._traverse(gitURL, hash, None, None, 'root')

    def _traverse(self, gitURL, hash, requiringURL, requiringURLHash, type):
        try:
            tuple = gitURL, hash, requiringURL, requiringURLHash
            if tuple in self._visitedTuples:
                return
            self._visitedTuples.add(tuple)

            mirror = repomirrorcache.get(gitURL)
            masterHash = mirror.hash('origin/master')
            hash = mirror.branchName(hash)

            dep = Dependency(
                gitURL=gitURL, hash=hash, requiringURL=requiringURL,
                requiringURLHash=requiringURLHash, type=type, masterHash=masterHash)
            self._dependencies.append(dep)

            self._traverse(gitURL, 'origin/master', None, None, 'master')
            for requirement in mirror.upsetoManifest(hash).requirements():
                self._traverse(requirement['originURL'], requirement['hash'], gitURL, hash, 'upseto')
            basenameForBuild = self._basenameForBuild(mirror, hash)
            for requirement in mirror.solventManifest(hash).requirements():
                basename = gitwrapper.originURLBasename(requirement['originURL'])
                type = 'dirbalak_build_rootfs' if basename == basenameForBuild else 'solvent'
                self._traverse(requirement['originURL'], requirement['hash'], gitURL, hash, type)
        except:
            logging.error(
                "Exception while handling '%(gitURL)s'/%(hash)s "
                "('%(type)s' dependency of '%(requiringURL)s'/%(requiringURLHash)s)", dict(
                    gitURL=gitURL, hash=hash, requiringURL=requiringURL, requiringURLHash=requiringURLHash,
                    type=type))
            raise

    def _basenameForBuild(self, mirror, hash):
        try:
            return mirror.dirbalakManifest(hash).buildRootFSRepositoryBasename()
        except KeyError:
            return None
