from dirbalak import graph
from dirbalak import repomirrorcache
from dirbalak import describetime
from upseto import gitwrapper


class DependencyGraph:
    _CONTINUOUS_INTEGRATION_VIOLATION_TIME = 14 * 24 * 60 * 60

    def __init__(self, dependencies, getNodeAttributesCallback):
        self._dependencies = dependencies
        self._getNodeAttributesCallback = getNodeAttributesCallback
        self._cachedGraph = None

    def renderText(self):
        return "\n".join([str(d) for d in self._dependencies]) + \
            "\n\n" + self.makeGraph().renderAsTreeText()

    def makeGraph(self):
        if self._cachedGraph is None:
            self._cachedGraph = self._makeGraph()
        return self._cachedGraph

    def _makeGraph(self):
        graphInstance = graph.Graph(dict(ranksep=0.7))
        for dep in self._dependencies:
            self._addNodeToGraph(graphInstance, dep.gitURL)
            if dep.requiringURL is not None:
                if dep.requiringURLHash != 'origin/master':
                    continue
                self._addNodeToGraph(graphInstance, dep.requiringURL)
                self._addArcToGraph(graphInstance, dep)
        return graphInstance

    def _lineStyleFromDependencyType(self, type):
        if type == 'upseto':
            return 'solid'
        elif type == 'solvent':
            return 'dashed'
        elif type == 'dirbalak_build_rootfs':
            return 'dotted'
        else:
            raise AssertionError("Unknown type %s" % type)

    def _addArcToGraph(self, graphInstance, dep):
        basename = gitwrapper.originURLBasename(dep.gitURL)
        mirror = repomirrorcache.get(dep.gitURL)
        distance = mirror.distanceFromMaster(dep.hash)
        requiringBasename = gitwrapper.originURLBasename(dep.requiringURL)
        graphInstance.addArc(
            requiringBasename, basename, style=self._lineStyleFromDependencyType(dep.type),
            ** self._attributesFromDistanceFromMaster(distance))

    def _addNodeToGraph(self, graphInstance, gitURL):
        basename = gitwrapper.originURLBasename(gitURL)
        attributes = self._getNodeAttributesCallback(gitURL)
        attributes['label'] = basename
        graphInstance.setNodeAttributes(basename, **attributes)

    def _attributesFromDistanceFromMaster(self, distance):
        if distance is None:
            return {}
        else:
            if distance['broken']:
                return dict(color="orange", label="broken")
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
