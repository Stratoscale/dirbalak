from twisted.web import resource
from dirbalak import traversefilter
from dirbalak import dependencygraph
from dirbalak.server import multiversegraphnodeattributes


class GraphsResource(resource.Resource):
    def __init__(self, multiverse):
        resource.Resource.__init__(self)
        self.putChild("allProjects", _AllProjects(multiverse))


class _AllProjects(resource.Resource):
    def __init__(self, multiverse):
        self._multiverse = multiverse
        self._cache = dict()
        self._traverse = None
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        png, map = self._make(request)
        if path == "map":
            return _Static(map, 'text/html')
        else:
            return _Static(png, 'image/png')

    def _make(self, request):
        if self._traverse != self._multiverse.getTraverse():
            self._cache = dict()
            self._traverse = self._multiverse.getTraverse()
        solventRootFSArcs = request.args['solventRootFSArcs'][0]
        dirbalakBuildRootFSArcs = request.args['dirbalakBuildRootFSArcs'][0]
        if (solventRootFSArcs, dirbalakBuildRootFSArcs) not in self._cache:
            filtered = traversefilter.TraverseFilter(
                traverse=self._traverse,
                solventRootFSArcs=solventRootFSArcs,
                dirbalakBuildRootFSArcs=dirbalakBuildRootFSArcs).dependencies()
            attributesCallback = multiversegraphnodeattributes.MultiverseGraphNodeAttributes(
                self._multiverse).attributes
            graph = dependencygraph.DependencyGraph(filtered, attributesCallback).makeGraph()
            self._cache[(solventRootFSArcs, dirbalakBuildRootFSArcs)] = graph.pngAndMap()
        return self._cache[(solventRootFSArcs, dirbalakBuildRootFSArcs)]


class _Static(resource.Resource):
    def __init__(self, contents, mimeType):
        self._contents = contents
        self._mimeType = mimeType
        resource.Resource.__init__(self)

    def render(self, request):
        request.setHeader("Content-Type", self._mimeType)
        return self._contents
