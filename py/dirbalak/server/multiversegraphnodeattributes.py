from upseto import gitwrapper


class MultiverseGraphNodeAttributes:
    def __init__(self, multiverse):
        self._multiverse = multiverse

    def attributes(self, gitURL):
        basename = gitwrapper.originURLBasename(gitURL)
        project = self._multiverse.projects[basename]
        return dict(cluster=project.group(), URL="/project/%s" % basename)
