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
        self._buildRootFSlabel = config.DEFAULT_BUILD_ROOTFS_LABEL
        self._mirror = repomirrorcache.get(self._gitURL)

    def go(self):
        os.environ['SOLVENT_CLEAN'] = 'Yes'
        self._verifiyDependenciesExist()
        self._checkOutBuildRootFS()
        self._checkOutDependencies()
        git = self._cloneSources()
        self._make(git)
        if self._submit:
            run.run(["sudo", "-E", "solvent", "submitbuild"], cwd=git.directory())
        self._whiteboxTest(git)
        self._rackTest(git)
        if self._submit:
            run.run(["sudo", "-E", "solvent", "approve"], cwd=git.directory())

    def _verifiyDependenciesExist(self):
        assert len(self._mirror.upsetoManifest(self._hash).requirements()) == 0
        assert len(self._mirror.solventManifest(self._hash).requirements()) == 0

    def _checkOutBuildRootFS(self):
        logging.info("checking out build chroot at label '%(label)s'", dict(label=self._buildRootFSlabel))
        run.run([
            "sudo", "solvent", "bringlabel", "--label", self._buildRootFSlabel,
            "--destination", config.BUILD_CHROOT])
        run.run([
            "sudo", "cp", "-a", "/etc/hosts", "/etc/resolv.conf", os.path.join(config.BUILD_CHROOT, "etc")])

    def _checkOutDependencies(self):
        pass

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
