from dirbalak.server import project
from dirbalak import traverse
from upseto import gitwrapper
import yaml


class Multiverse:
    def __init__(self, fetchThread):
        self._fetchThread = fetchThread
        self.projects = dict()

    @classmethod
    def load(cls, filename, fetchThread):
        result = cls(fetchThread)
        result.rereadMultiverseFile(filename)
        return result

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

    def rereadMultiverseFile(self, filename):
        with open(filename) as f:
            data = yaml.load(f.read())
        for projectData in data['PROJECTS']:
            basename = gitwrapper.originURLBasename(projectData['gitURL'])
            if basename in self.projects:
                projectInstance = self.projects[basename]
                projectInstance.update(** projectData)
            else:
                projectInstance = project.Project(fetchThread=self._fetchThread, ** projectData)
                self.projects[projectInstance.basename()] = projectInstance
        self.needsFetch("Reread multiverse file")
