from dirbalak import traverse
from dirbalak import repomirrorcache
from dirbalak import dependencygraph
from dirbalak import traversefilter
from upseto import gitwrapper
from upseto import run


class Discover:
    def __init__(
            self, projects, objectStore, clusterMap,
            dirbalakBuildRootFSArcs=True, solventRootFSArcs=True):
        self._rootProjects = projects
        self._objectStore = objectStore
        self._clusterMap = clusterMap
        self._dirbalakBuildRootFSArcs = dirbalakBuildRootFSArcs
        self._solventRootFSArcs = solventRootFSArcs
        traverseInstance = traverse.Traverse()
        for project in projects:
            traverseInstance.traverse(project, 'origin/master')
        filter = traversefilter.TraverseFilter(
            traverseInstance, dirbalakBuildRootFSArcs=dirbalakBuildRootFSArcs,
            solventRootFSArcs=solventRootFSArcs)
        self._graph = dependencygraph.DependencyGraph(filter.dependencies(), self._nodeAttributes)

    def renderText(self):
        return self._graph.renderText()

    def makeGraph(self):
        return self._graph.makeGraph()

    def _nodeAttributes(self, gitURL):
        mirror = repomirrorcache.get(gitURL)
        basename = gitwrapper.originURLBasename(mirror.gitURL())
        attributes = self._cluster(basename)
        attributes.update(self._fillColor(mirror, basename))
        return attributes

    def _cluster(self, basename):
        if basename not in self._clusterMap:
            return dict(cluster="others")
        return dict(cluster=self._clusterMap[basename])

    def _fillColor(self, mirror, basename):
        if self._objectStore is None:
            return {}
        hash = mirror.hash('origin/master')
        labelBase = 'solvent__%s__build__%s__' % (basename, hash)
        labels = run.run([
            'osmosis', 'listlabels', '^' + labelBase,
            '--objectStores', self._objectStore]).strip().split("\n")
        states = [label[len(labelBase):] for label in labels]
        if 'official' in states:
            return dict()
        elif 'clean' in states:
            return dict(style="filled", color="#DDDDDD", peripheries=1)
        else:
            return dict(style="filled", color="#888888", peripheries=1, text_build="NOT BUILT")
