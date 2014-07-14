from upseto import gitwrapper


class Scriptolog:
    def __init__(self, traverse):
        self._traverse = traverse

    def updateAllDependencies(self, gitURL):
        dependsOn = list(self._dependsOn(gitURL))
        script = [
            "#!/bin/bash",
            "set -e",
            "cd /tmp",
            "rm -fr scriptolog",
            "mkdir scriptolog",
            "cd scriptolog",
            "git clone %s" % gitURL,
            "cd %s" % gitwrapper.originURLBasename(gitURL)] + \
            self._updatedUpsetoManifest(dependsOn) + \
            self._updatedSolventManifest(dependsOn) + [
            "git add .",
            "git commit -m 'Updated all deps to latest master'",
            "git push origin master",
            "cd /tmp",
            "rm -fr scriptolog"]
        return "\n".join(script)

    def _dependsOn(self, gitURL):
        for dep in self._traverse.dependencies():
            if dep.requiringURL != gitURL:
                continue
            if dep.requiringURLHash != 'origin/master':
                continue
            yield dep

    def _updatedUpsetoManifest(self, dependsOn):
        if len([d for d in dependsOn if d.type == 'upseto']) == 0:
            return []
        upsetoManifest = "requirements:\n" + "\n".join(
            "- hash: %s\n  originURL: %s" % (d.masterHash, d.gitURL) for d in dependsOn
            if d.type == "upseto")
        return ["cat > upseto.manifest << EOF", upsetoManifest, "EOF"]

    def _updatedSolventManifest(self, dependsOn):
        if len([d for d in dependsOn if d.type in ['solvent', 'dirbalak_build_rootfs']]) == 0:
            return []
        solventManifest = "requirements:\n" + "".join(
            "- hash: %s\n  originURL: %s\n" % (d.masterHash, d.gitURL) for d in dependsOn
            if d.type in ['solvent', 'dirbalak_build_rootfs'])
        return ["cat > solvent.manifest << EOF", solventManifest, "EOF"]
