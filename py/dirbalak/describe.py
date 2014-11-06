from dirbalak import traverse
from dirbalak import graph
from dirbalak import traversefilter
from dirbalak import traversefilterreachable
from upseto import gitwrapper


class Describe:
    def __init__(self, gitURL, hash, dirbalakBuildRootFSArcs=True, solventRootFSArcs=True):
        self._gitURL = gitURL
        self._hash = hash
        self._dirbalakBuildRootFSArcs = dirbalakBuildRootFSArcs
        self._solventRootFSArcs = solventRootFSArcs
        traverseInstance = traverse.Traverse(visitMasterBranchOfEachDependency=False)
        traverseInstance.traverse(gitURL, hash)
        filter = traversefilter.TraverseFilter(
            traverseInstance, dirbalakBuildRootFSArcs=dirbalakBuildRootFSArcs,
            solventRootFSArcs=solventRootFSArcs)
        reachable = traversefilterreachable.TraverseFilterReachable(filter.dependencies())
        reachable.includeRecursiveByExactHashes(gitURL, hash)
        self._dependencies = reachable.dependencies()
        self._graph = graph.Graph(dict(nodesep=2, ranksep=2.5))
        self._createGraph()

    def renderText(self):
        return "\n".join([str(d) for d in self._dependencies]) + \
            "\n\n" + self._graph.renderAsTreeText()

    def makeGraph(self):
        return self._graph

    def _createGraph(self):
        for dep in self._dependencies:
            self._addNode(dep.gitURL, dep.hash, dep.broken)
            if dep.requiringURL is not None:
                self._addNode(dep.requiringURL, dep.requiringURLHash, False)
                self._graph.addArc(
                    self._nodeName(dep.requiringURL, dep.requiringURLHash),
                    self._nodeName(dep.gitURL, dep.hash),
                    style=self._lineStyleFromDependencyType(dep.type),
                    ** self._arcAttributes(dep))

    def _nodeName(self, gitURL, hash):
        basename = gitwrapper.originURLBasename(gitURL)
        return basename + '/' + hash

    def _addNode(self, gitURL, hash, broken):
        basename = gitwrapper.originURLBasename(gitURL).replace('-', '_')
        name = self._nodeName(gitURL, hash)
        hash = 'master' if hash == 'origin/master' else hash[:8]
        attributes = dict(label=basename + "\\n" + hash, cluster=basename)
        if broken:
            attributes['color'] = 'red'
        self._graph.setNodeAttributes(name, **attributes)

    def _lineStyleFromDependencyType(self, type):
        if type == 'upseto':
            return 'solid'
        elif type == 'solvent':
            return 'dashed'
        elif type == 'dirbalak_build_rootfs':
            return 'dotted'
        else:
            raise AssertionError("Unknown type %s" % type)

    def _arcAttributes(self, dep):
        if dep.broken:
            return dict(color="#FF0000")
        return dict()
