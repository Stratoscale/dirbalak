from upseto import gitwrapper
from upseto import run
from dirbalak import traverse
from dirbalak import repomirrorcache


class UnreferencedLabels:
    def __init__(self, projects, objectStore):
        self._projects = projects
        self._objectStore = objectStore
        self._labels = self._getLabels()

        self._references = set()
        self._traverse = traverse.Traverse()
        for project in projects:
            for dependency in self._traverse.traverse(project, 'origin/master'):
                self._addReferencesFromManifests(dependency)

        self._unreferenced = []
        for label in self._labels:
            basename, hash = self._basenameAndHashFromLabel(label)
            if (basename, hash) not in self._references:
                self._unreferenced.append(label)

    def unreferencedLabels(self):
        return self._unreferenced

    def _addReferencesFromManifests(self, dependency):
        mirror = repomirrorcache.get(dependency.gitURL)
        for requirement in mirror.upsetoManifest(dependency.hash).requirements():
            basename = gitwrapper.originURLBasename(requirement['originURL'])
            self._references.add((basename, requirement['hash']))
        for requirement in mirror.solventManifest(dependency.hash).requirements():
            basename = gitwrapper.originURLBasename(requirement['originURL'])
            self._references.add((basename, requirement['hash']))
        try:
            label = mirror.dirbalakManifest(dependency.hash).buildRootFSLabel()
        except KeyError:
            return
        self._references.add(self._basenameAndHashFromLabel(label))

    def _basenameAndHashFromLabel(self, label):
        parts = label.split("__")
        return (parts[1], parts[3])

    def _getLabels(self):
        return run.run(['osmosis', 'listlabels', '--objectStores', self._objectStore]).strip().split("\n")
