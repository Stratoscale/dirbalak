from dirbalak import traverse
from dirbalak import graph
from upseto import gitwrapper


class Discover:
    def __init__(self, projects):
        self._rootProjects = projects
        self._dependencies = []
        self._traverse = traverse.Traverse(visitMaster=True)
        for project in projects:
            for dependency in self._traverse.traverse(project, 'origin/master'):
                self._dependencies.append(dependency)

    def renderText(self):
        return "\n".join([str(d) for d in self._dependencies])

    def saveGraphPng(self, filename):
        graphInstance = graph.Graph()
        for dep in self._dependencies:
            basename = gitwrapper.originURLBasename(dep.gitURL)
            graphInstance.setNodeAttributes(basename, label=basename)
            if dep.requiringURL is not None:
                if dep.type == 'upseto':
                    style = 'solid'
                elif dep.type == 'solvent':
                    style = 'dashed'
                else:
                    raise AssertionError("Unknown type %s" % dep.type)
                requiringBasename = gitwrapper.originURLBasename(dep.requiringURL)
                graphInstance.setNodeAttributes(requiringBasename, label=requiringBasename)
                graphInstance.addArc(basename, requiringBasename, style=style)
        graphInstance.savePng(filename)
