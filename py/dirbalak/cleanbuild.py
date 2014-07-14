import os
import logging
from dirbalak import repomirrorcache
from upseto import run
from upseto import gitwrapper
from dirbalak import config
import re
import subprocess


class CleanBuild:
    _MOUNT_BIND = ["proc", "dev", "sys"]

    def __init__(self, gitURL, hash, submit):
        self._gitURL = gitURL
        self._hash = hash
        self._submit = submit
        self._mirror = repomirrorcache.get(self._gitURL)

    def go(self):
        self._configureEnvironment()
        self._verifiyDependenciesExist()
        buildRootFSLabel = self._findBuildRootFSLabel()
        self._unmountBinds()
        self._checkOutBuildRootFS(buildRootFSLabel)
        git = self._cloneSources()
        self._checkOutDependencies(git)
        self._mountBinds()
        try:
            self._upsetoCheckRequirements(git)
            self._make(git)
            if self._submit:
                logging.info("Submitting")
                run.run(["sudo", "-E", "solvent", "submitbuild"], cwd=git.directory())
                run.run([
                    "make", "-f", self._makefileForTargetThatMayNotExist("submit"), "submit"],
                    cwd=git.directory())
            self._whiteboxTest(git)
            self._rackTest(git)
            if self._submit:
                run.run(["sudo", "-E", "solvent", "approve"], cwd=git.directory())
                run.run([
                    "make", "-f", self._makefileForTargetThatMayNotExist("approve"), "approve"],
                    cwd=git.directory())
        finally:
            self._unmountBinds()

    def _verifiyDependenciesExist(self):
        self._mirror.run(["solvent", "checkrequirements"], hash=self._hash)

    def _checkOutBuildRootFS(self, buildRootFSLabel):
        logging.info("checking out build chroot at label '%(label)s'", dict(label=buildRootFSLabel))
        run.run([
            "sudo", "solvent", "bringlabel", "--label", buildRootFSLabel,
            "--destination", config.BUILD_CHROOT])
        run.run([
            "sudo", "cp", "-a", "/etc/hosts", "/etc/resolv.conf", os.path.join(config.BUILD_CHROOT, "etc")])
        run.run([
            "sudo", "sed", 's/.*requiretty.*//', "-i", os.path.join(config.BUILD_CHROOT, "etc", "sudoers")])
        with open("/etc/solvent.conf") as f:
            contents = f.read()
        modified = re.sub("LOCAL_OSMOSIS:.*", "LOCAL_OSMOSIS: localhost:1010", contents)
        with open(os.path.join(config.BUILD_CHROOT, "tmp", "solvent.conf"), "w") as f:
            f.write(modified)
        run.run([
            "sudo", "mv", os.path.join(config.BUILD_CHROOT, "tmp", "solvent.conf"),
            os.path.join(config.BUILD_CHROOT, "etc", "solvent.conf")])

    def _checkOutDependencies(self, git):
        run.run(["sudo", "solvent", "fulfillrequirements"], cwd=git.directory())

    def _cloneSources(self):
        logging.info("Cloning git repo inside chroot")
        self._mirror.replicate(config.BUILD_DIRECTORY)
        git = gitwrapper.GitWrapper.existing(self._gitURL, config.BUILD_DIRECTORY)
        git.checkout(self._hash)
        return git

    def _upsetoCheckRequirements(self, git):
        relative = git.directory()[len(config.BUILD_CHROOT):]
        if os.path.exists(os.path.join(git.directory(), "upseto.manifest")):
            logging.info("Verifying upseto requirements")
            run.run([
                "sudo", "chroot", config.BUILD_CHROOT, "sh", "-c",
                "cd %s; upseto checkRequirements --show" % relative])

    def _make(self, git, arguments=""):
        relative = git.directory()[len(config.BUILD_CHROOT):]
        logging.info("Running make %(arguments)s", dict(arguments=arguments))
        run.run([
            "sudo", "chroot", config.BUILD_CHROOT, "sh", "-c",
            "cd %s; make %s" % (relative, arguments)])

    def _whiteboxTest(self, git):
        pass

    def _rackTest(self, git):
        pass

    def _findBuildRootFSLabel(self):
        mani = self._mirror.dirbalakManifest(self._hash)
        try:
            return mani.buildRootFSLabel()
        except KeyError:
            buildRootFSGitBasename = mani.buildRootFSRepositoryBasename()
            label = self._mirror.run([
                'solvent', 'printlabel', '--product', 'rootfs',
                '--repositoryBasename', buildRootFSGitBasename], hash=self._hash)
            return label.strip()

    def _makefileForTargetThatMayNotExist(self, target):
        tempMakefile = os.path.join(config.BUILD_CHROOT, "tmp", "Makefile")
        with open(tempMakefile, "w") as f:
            f.write("include Makefile\n%s:\n" % target)
        return tempMakefile

    def _unmountBinds(self):
        for mountBind in self._MOUNT_BIND:
            subprocess.call(
                ["sudo", "umount", os.path.join(config.BUILD_CHROOT, mountBind)],
                stdout=open("/dev/null", "w"), stderr=subprocess.STDOUT)

    def _mountBinds(self):
        for mountBind in self._MOUNT_BIND:
            run.run([
                "sudo", "mount", "-o", "bind", "/" + mountBind,
                os.path.join(config.BUILD_CHROOT, mountBind)])

    def _configureEnvironment(self):
        if 'OFFICIAL' in os.environ.get('SOLVENT_CONFIG', ""):
            return
        os.environ['SOLVENT_CLEAN'] = 'Yes'
