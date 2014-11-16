from upseto import gitwrapper


class MultiverseGraphNodeAttributes:
    def __init__(self, multiverse):
        self._multiverse = multiverse

    def attributes(self, gitURL):
        basename = gitwrapper.originURLBasename(gitURL)
        if basename not in self._multiverse.projects:
            return dict(fillcolor='red', cluster="unknowns")
        project = self._multiverse.projects[basename]
        result = dict(cluster=project.group(), URL="/project/%s" % basename, shape="box", style="striped")
        if len(project.masterBuildHistory()) == 0:
            result['fillcolor'] = 'white'
        else:
            result['fillcolor'] = ":".join(
                "#AAFFAA" if r['successfull'] else "#FFAAAA" for r in project.masterBuildHistory())
        if project.buildBanned():
            result['color'] = 'red'
            result['penwidth'] = 1
        return result
