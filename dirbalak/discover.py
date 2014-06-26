from dirbalak import traverse
from dirbalak import graph
from dirbalak import repomirrorcache
from dirbalak import describetime
from upseto import gitwrapper


class Discover:
    _CONTINUOUS_INTEGRATION_VIOLATION_TIME = 14 * 24 * 60 * 60

    def __init__(self, projects, objectStore):
        self._rootProjects = projects
        self._objectStore = objectStore
        self._dependencies = []
        self._cachedGraph = None
        self._traverse = traverse.Traverse(visitMaster=True)
        for project in projects:
            for dependency in self._traverse.traverse(project, 'origin/master'):
                self._dependencies.append(dependency)

    def renderText(self):
        return "\n".join([str(d) for d in self._dependencies])

    def makeGraph(self):
        if self._cachedGraph is None:
            self._cachedGraph = self._makeGraph()
        return self._cachedGraph

    def _makeGraph(self):
        graphInstance = graph.Graph()
        for dep in self._dependencies:
            basename = gitwrapper.originURLBasename(dep.gitURL)
            graphInstance.setNodeAttributes(basename, label=basename, cluster=self._cluster(basename))
            if dep.requiringURL is not None:
                if dep.requiringURLHash != 'origin/master':
                    continue
                if dep.type == 'upseto':
                    style = 'solid'
                elif dep.type == 'solvent':
                    style = 'dashed'
                else:
                    raise AssertionError("Unknown type %s" % dep.type)
                mirror = repomirrorcache.get(dep.gitURL)
                distance = mirror.distanceFromMaster(dep.hash)
                requiringBasename = gitwrapper.originURLBasename(dep.requiringURL)
                graphInstance.setNodeAttributes(
                    requiringBasename, label=requiringBasename, cluster=self._cluster(requiringBasename))
                graphInstance.addArc(
                    basename, requiringBasename, style=style,
                    ** self._attributesFromDistanceFromMaster(distance))
        return graphInstance

    def _attributesFromDistanceFromMaster(self, distance):
        if distance is None:
            return {}
        else:
            label = "behind:\\n%d commits" % distance['commits']
            color = "#000000"
            if 'time' in distance:
                label += "\\n%s" % describetime.describeTime(distance['time'])
                if distance['time'] > self._CONTINUOUS_INTEGRATION_VIOLATION_TIME:
                    color = "#FF0000"
                else:
                    color = "#990000"
            return dict(color=color, label=label)

    def _cluster(self, basename):
        return 'rootfs' if basename.startswith('rootfs-') else 'projects'
