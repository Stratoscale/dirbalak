from twisted.web import resource
from dirbalak import scriptolog


class ScriptologResource(resource.Resource):
    def __init__(self, multiverse):
        self._multiverse = multiverse
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        return _Scriptolog(self._multiverse, path)


class _Scriptolog(resource.Resource):
    def __init__(self, multiverse, basename):
        self._multiverse = multiverse
        self._basename = basename
        self._project = multiverse.projects[basename]
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        scriptologist = scriptolog.Scriptolog(self._multiverse.getTraverse())
        if path == "updateAllDependencies":
            return _Static(scriptologist.updateAllDependencies(self._project.gitURL()), 'text/plain')
        else:
            raise Exception("Unknown script '%s'" % path)


class _Static(resource.Resource):
    def __init__(self, contents, mimeType):
        self._contents = contents
        self._mimeType = mimeType
        resource.Resource.__init__(self)

    def render(self, request):
        if 'filename' in request.args:
            request.setHeader(
                "Content-Disposition", 'attachment; filename="%s";' % request.args['filename'][0])
        request.setHeader("Content-Type", self._mimeType)
        return self._contents
