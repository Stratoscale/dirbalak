from twisted.web import resource
from realtimewebui import rootresource


class Projects(resource.Resource):
    def getChild(self, path, request):
        return rootresource.Renderer("project.html", dict(project=path))
