from twisted.web import resource
from dirbalak import traversefilter
from dirbalak import traversefilterreachable
from dirbalak import dependencygraph
from dirbalak.server import multiversegraphnodeattributes
from dirbalak.server import tojs
import logging


class GraphsResource(resource.Resource):
    def __init__(self, multiverse):
        resource.Resource.__init__(self)
        self._allProjects = _AllProjects(multiverse)
        self._projectFolder = _ProjectFolder(multiverse)
        self.putChild("allProjects", self._allProjects)
        self.putChild("project", self._projectFolder)

    def update(self):
        self._allProjects.clearCache()
        self._projectFolder.clearCache()
        tojs.increment("graph/generation")
        logging.info("Graph must refresh")


class _AllProjects(resource.Resource):
    def __init__(self, multiverse):
        self._multiverse = multiverse
        self._cache = dict()
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        png, map = self._make(request)
        if path == "map":
            return _Static(map, 'text/html')
        else:
            return _Static(png, 'image/png')

    def clearCache(self):
        self._cache = dict()

    def _make(self, request):
        solventRootFSArcs = request.args['solventRootFSArcs'][0]
        dirbalakBuildRootFSArcs = request.args['dirbalakBuildRootFSArcs'][0]
        if (solventRootFSArcs, dirbalakBuildRootFSArcs) not in self._cache:
            filtered = traversefilter.TraverseFilter(
                traverse=self._multiverse.getTraverse(),
                solventRootFSArcs=solventRootFSArcs,
                dirbalakBuildRootFSArcs=dirbalakBuildRootFSArcs).dependencies()
            attributesCallback = multiversegraphnodeattributes.MultiverseGraphNodeAttributes(
                self._multiverse).attributes
            graph = dependencygraph.DependencyGraph(filtered, attributesCallback).makeGraph()
            self._cache[(solventRootFSArcs, dirbalakBuildRootFSArcs)] = graph.pngAndMap()
        return self._cache[(solventRootFSArcs, dirbalakBuildRootFSArcs)]


class _ProjectFolder(resource.Resource):
    def __init__(self, multiverse):
        self._multiverse = multiverse
        self._cache = dict()
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        project = self._multiverse.projects[path]
        return _ProjectRenderer(project, self._cache, self._multiverse)

    def clearCache(self):
        self._cache = dict()


class _ProjectRenderer(resource.Resource):
    def __init__(self, project, cache, multiverse):
        self._project = project
        self._cache = cache.setdefault(project.basename(), dict())
        self._multiverse = multiverse
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        png, map = self._make(request)
        if path == "map":
            return _Static(map, 'text/html')
        else:
            return _Static(png, 'image/png')

    def _make(self, request):
        solventRootFSArcs = request.args['solventRootFSArcs'][0]
        dirbalakBuildRootFSArcs = request.args['dirbalakBuildRootFSArcs'][0]
        if (solventRootFSArcs, dirbalakBuildRootFSArcs) not in self._cache:
            filtered = traversefilter.TraverseFilter(
                traverse=self._multiverse.getTraverse(),
                solventRootFSArcs=solventRootFSArcs,
                dirbalakBuildRootFSArcs=dirbalakBuildRootFSArcs).dependencies()
            filter = traversefilterreachable.TraverseFilterReachable(filtered)
            filter.includeRecursive(self._project.basename())
            attributesCallback = multiversegraphnodeattributes.MultiverseGraphNodeAttributes(
                self._multiverse).attributes
            graph = dependencygraph.DependencyGraph(filter.dependencies(), attributesCallback).makeGraph()
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
