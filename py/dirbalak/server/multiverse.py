from dirbalak.server import project
from dirbalak import traverse
import yaml


class Multiverse:
    def __init__(self, data, fetchThread, model):
        self._data = data
        self._fetchThread = fetchThread
        self._model = model
        self.projects = dict()
        for projectData in data['PROJECTS']:
            projectInstance = project.Project(
                fetchThread=fetchThread, model=model, ** projectData)
            self.projects[projectInstance.basename()] = projectInstance

    @classmethod
    def load(cls, filename, fetchThread, model):
        with open(filename) as f:
            data = yaml.load(f.read())
        return cls(data, fetchThread, model)

    def traverse(self):
        self._traverse = traverse.Traverse()
        for project in self.projects.values():
            self._traverse.traverse(project.gitURL(), 'origin/master')
        for project in self.projects.values():
            project.setTraverse(self._traverse)

    def getTraverse(self):
        return self._traverse

    def needsFetch(self, reason):
        for project in self.projects.values():
            project.needsFetch(reason)
