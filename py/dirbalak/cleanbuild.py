import os
import logging
from dirbalak import repomirrorcache
from upseto import run
from upseto import gitwrapper
from dirbalak import config
import re
import subprocess
import multiprocessing


class CleanBuild:
    _MOUNT_BIND = ["proc", "dev", "sys"]
    _TEMP_MAKEFILE = "/tmp/Makefile"

    def __init__(self, gitURL, hash, submit, buildRootFS):
        self._gitURL = gitURL
        self._hash = hash
        self._submit = submit
        self._buildRootFS = buildRootFS
        self._mirror = repomirrorcache.get(self._gitURL)

    def go(self):
        self._configureEnvironment()
        self._verifyDependenciesExist()
        buildRootFSLabel = self._findBuildRootFSLabel()
        self._unmountBinds()
        self._checkOutBuildRootFS(buildRootFSLabel)
        self._git = self._cloneSources()
        self._gitInChroot = self._git.directory()[len(config.BUILD_CHROOT):]
        self._checkOutDependencies()
        self._mountBinds()
        try:
            self._upsetoCheckRequirements()
            self._makeForATargetThatMayNotExist("prepareForCleanBuild")
            self._make()
            if self._submit:
                logging.info("Submitting")
                run.run(["sudo", "-E", "solvent", "submitbuild"], cwd=self._git.directory())
                run.run([
                    "make", "-f", self._makefileForTargetThatMayNotExist("submit"), "submit"],
                    cwd=self._git.directory())
            self._rackTest()
            if self._submit:
                run.run(["sudo", "-E", "solvent", "approve"], cwd=self._git.directory())
                run.run([
                    "make", "-f", self._makefileForTargetThatMayNotExist("approve"), "approve"],
                    cwd=self._git.directory())
        finally:
            self._unmountBinds()

    def _verifyDependenciesExist(self):
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
        modified = re.sub("LOCAL_OSMOSIS:.*", "LOCAL_OSMOSIS: 127.0.0.1:1010", contents)
        # todo: change 127.0.0.1 -> localhost
        with open(os.path.join(config.BUILD_CHROOT, "tmp", "solvent.conf"), "w") as f:
            f.write(modified)
        run.run([
            "sudo", "mv", os.path.join(config.BUILD_CHROOT, "tmp", "solvent.conf"),
            os.path.join(config.BUILD_CHROOT, "etc", "solvent.conf")])

    def _checkOutDependencies(self):
        run.run(["sudo", "solvent", "fulfillrequirements"], cwd=self._git.directory())

    def _cloneSources(self):
        logging.info("Cloning git repo inside chroot")
        self._mirror.replicate(config.BUILD_DIRECTORY)
        git = gitwrapper.GitWrapper.existing(self._gitURL, config.BUILD_DIRECTORY)
        git.checkout(self._hash)
        return git

    def _upsetoCheckRequirements(self):
        if not os.path.exists(os.path.join(self._git.directory(), "upseto.manifest")):
            logging.info("No upseto.manifest file, skipping verification of upseto requirements")
            return
        logging.info("Verifying upseto requirements")
        run.run(["upseto", "checkRequirements", "--show"], cwd=self._git.directory())

    def _make(self, arguments=""):
        logging.info("Running make %(arguments)s", dict(arguments=arguments))
        run.run([
            "sudo", "chroot", config.BUILD_CHROOT, "sh", "-c",
            "cd %s; make -j %d %s" % (self._gitInChroot, multiprocessing.cpu_count(), arguments)])

    def _makeForATargetThatMayNotExist(self, target, arguments=""):
        self._makefileForTargetThatMayNotExist(target)
        self._make(("-f %s %s " % (self._TEMP_MAKEFILE, target)) + arguments)

    def _rackTest(self):
        pass

    def _findBuildRootFSLabel(self):
        mani = self._mirror.dirbalakManifest(self._hash)
        try:
            label = mani.buildRootFSLabel()
            assert self._buildRootFS is None, \
                "Manifest contains build rootfs, but project marked as one without"
            return label
        except KeyError:
            try:
                buildRootFSGitBasename = mani.buildRootFSRepositoryBasename()
                assert self._buildRootFS is None, \
                    "Manifest contains build rootfs, but project marked as one without"
            except KeyError:
                if self._buildRootFS:
                    return self._buildRootFS
                raise Exception("No dirbalak.manifest file with rootfs pointer - please create one")
            label = self._mirror.run([
                'solvent', 'printlabel', '--product', 'rootfs',
                '--repositoryBasename', buildRootFSGitBasename], hash=self._hash)
            return label.strip()

    def _makefileForTargetThatMayNotExist(self, target):
        tempMakefile = os.path.join(config.BUILD_CHROOT, self._TEMP_MAKEFILE.strip("/"))
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
