import os
import logging
from dirbalak import repomirrorcache
from upseto import run
from upseto import gitwrapper
from dirbalak import config


class CleanBuild:
    def __init__(self, gitURL, hash, submit):
        self._gitURL = gitURL
        self._hash = hash
        self._submit = submit
        self._mirror = repomirrorcache.get(self._gitURL)

    def go(self):
        os.environ['SOLVENT_CLEAN'] = 'Yes'
        self._verifiyDependenciesExist()
        buildRootFSLabel = self._findBuildRootFSLabel()
        self._checkOutBuildRootFS(buildRootFSLabel)
        git = self._cloneSources()
        self._checkOutDependencies(git)
        self._make(git)
        if self._submit:
            run.run(["sudo", "-E", "solvent", "submitbuild"], cwd=git.directory())
        self._whiteboxTest(git)
        self._rackTest(git)
        if self._submit:
            run.run(["sudo", "-E", "solvent", "approve"], cwd=git.directory())

    def _verifiyDependenciesExist(self):
        self._mirror.run(["solvent", "checkrequirements"], hash=self._hash)

    def _checkOutBuildRootFS(self, buildRootFSLabel):
        logging.info("checking out build chroot at label '%(label)s'", dict(label=buildRootFSLabel))
        run.run([
            "sudo", "solvent", "bringlabel", "--label", buildRootFSLabel,
            "--destination", config.BUILD_CHROOT])
        run.run([
            "sudo", "cp", "-a", "/etc/hosts", "/etc/resolv.conf", os.path.join(config.BUILD_CHROOT, "etc")])

    def _checkOutDependencies(self, git):
        run.run(["sudo", "solvent", "fulfillrequirements"], cwd=git.directory())

    def _cloneSources(self):
        logging.info("Cloning git repo inside chroot")
        self._mirror.replicate(config.BUILD_DIRECTORY)
        git = gitwrapper.GitWrapper.existing(self._gitURL, config.BUILD_DIRECTORY)
        git.checkout(self._hash)
        return git

    def _make(self, git):
        relative = git.directory()[len(config.BUILD_CHROOT):]
        logging.info("Running make")
        run.run([
            "sudo", "chroot", config.BUILD_CHROOT, "sh", "-c",
            "cd %s; make" % relative])

    def _whiteboxTest(self, git):
        pass

    def _rackTest(self, git):
        pass

    def _findBuildRootFSLabel(self):
        mani = self._mirror.dirbalakManifest(self._hash)
        try:
            buildRootFSGitBasename = mani.buildRootFS()
        except KeyError:
            return config.DEFAULT_BUILD_ROOTFS_LABEL
        label = self._mirror.run([
            'solvent', 'printlabel', '--product', 'rootfs', '--repositoryBasename', buildRootFSGitBasename],
            hash=self._hash)
        return label.strip()
