import os
import logging
from dirbalak import repomirrorcache
from dirbalak import makefiletricks
from upseto import run
from upseto import gitwrapper
from dirbalak import config
import re
import subprocess
import multiprocessing
import time
import solvent.commonmistakes


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
        self._manifest = self._mirror.dirbalakManifest(self._hash)
        logging.info("Using '%(filename)s' as makefile filename", dict(
            filename=self._manifest.makefileFilename()))
        buildRootFSLabel = self._findBuildRootFSLabel()
        self._unmountBinds()
        self._checkOutBuildRootFS(buildRootFSLabel)
        self._git = self._cloneSources()
        self._gitInChroot = self._git.directory()[len(config.BUILD_CHROOT):]
        self._checkOutDependencies()
        self._mountBinds()
        try:
            self._upsetoCheckRequirements()
            self._checkMakefileForErrors()
            self._makeForATargetThatMayNotExist(
                logName="02_make_prepareForCleanBuild", target="prepareForCleanBuild")
            self._make(logName="03_make")
            if self._submit:
                logging.info("Submitting")
                self._runAndBeamLog(
                    logName="04_solvent_submitbuild",
                    command=["sudo", "-E", "solvent", "submitbuild"], cwd=self._git.directory())
                with makefiletricks.makefileForATargetThatMayNotExists(
                        directory="/tmp", makefileFilename=self._manifest.makefileFilename(),
                        target="submit") as tempMakefile:
                    self._runAndBeamLog(
                        logName="05_make_submit", command=["make", "-f", tempMakefile, "submit"],
                        cwd=self._git.directory())
            else:
                logging.info("Non submitting job, skipping submission stages")
                self._beamLog(logName="04_05_skipped_submission", output="skipped", returnCode=0)
            self._makeForATargetThatMayNotExist(
                logName="06_make_racktest", target="racktest")
            if self._submit:
                self._runAndBeamLog(
                    logName="07_solvent_approve_build",
                    command=["sudo", "-E", "solvent", "approve"],
                    cwd=self._git.directory())
                with makefiletricks.makefileForATargetThatMayNotExists(
                        directory=self._git.directory(),
                        makefileFilename=self._manifest.makefileFilename(),
                        target="approve") as tempMakefile:
                    self._runAndBeamLog(
                        logName="08_make_approve", command=["make", "-f", tempMakefile, "approve"],
                        cwd=self._git.directory())
        finally:
            self._unmountBinds()
            self._beamLogsDir("buildHost_var_log", "/var/log")

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
        self._configureSolvent()
        self._configureLogbeam()
        self._configurePyracktest()

    def _configureLogbeam(self):
        conf = subprocess.check_output(["logbeam", "createConfig"])
        logging.info("logbeam config: %(config)s", dict(config=conf))
        with open(os.path.join(config.BUILD_CHROOT, "tmp", "logbeam.config"), "w") as f:
            f.write(conf)
        run.run([
            "sudo", "mv", os.path.join(config.BUILD_CHROOT, "tmp", "logbeam.config"),
            os.path.join(config.BUILD_CHROOT, "etc", "logbeam.config")])

    def _configureSolvent(self):
        with open("/etc/solvent.conf") as f:
            contents = f.read()
        modified = re.sub("LOCAL_OSMOSIS:.*", "LOCAL_OSMOSIS: 127.0.0.1:1010", contents)
        # todo: change 127.0.0.1 -> localhost
        with open(os.path.join(config.BUILD_CHROOT, "tmp", "solvent.conf"), "w") as f:
            f.write(modified)
        run.run([
            "sudo", "mv", os.path.join(config.BUILD_CHROOT, "tmp", "solvent.conf"),
            os.path.join(config.BUILD_CHROOT, "etc", "solvent.conf")])

    def _configurePyracktest(self):
        run.run([
            "sudo", "cp", "/etc/racktest.conf",
            os.path.join(config.BUILD_CHROOT, "etc", "racktest.conf")])

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
        self._runAndBeamLog(
            logName="01_upseto_checkRequirements", command=["upseto", "checkRequirements", "--show"],
            cwd=self._git.directory())

    def _checkMakefileForErrors(self):
        if makefiletricks.defaultTargetDependsOnTarget(
                self._git.directory(), self._manifest.makefileFilename(), 'submit'):
            raise Exception(
                "Default target depends on 'submit', makefile is invalid, dirbalak will not build")
        if makefiletricks.defaultTargetDependsOnTarget(
                self._git.directory(), self._manifest.makefileFilename(), 'approve'):
            raise Exception(
                "Default target depends on 'approve', makefile is invalid, dirbalak will not build")
        if not makefiletricks.targetDoesNotDependOnAnything(
                self._git.directory(), self._manifest.makefileFilename(), 'submit'):
            raise Exception("target 'submit' must not have any dependencies")
        if not makefiletricks.targetDoesNotDependOnAnything(
                self._git.directory(), self._manifest.makefileFilename(), 'approve'):
            raise Exception("target 'approve' must not have any dependencies")
        if not makefiletricks.targetDoesNotDependOnAnything(
                self._git.directory(), self._manifest.makefileFilename(), 'racktest'):
            raise Exception("target 'racktest' must not have any dependencies")

    def _make(self, logName, arguments=""):
        logging.info("Running make %(arguments)s", dict(arguments=arguments))
        self._runAndBeamLog(logName, [
            "sudo", "-E", "chroot", config.BUILD_CHROOT, "sh", "-c",
            "cd %s; make -f %s -j %d %s" % (
                self._gitInChroot, self._manifest.makefileFilename(), multiprocessing.cpu_count(),
                arguments)])

    def _runAndBeamLog(self, logName, command, cwd=None):
        try:
            output = run.run(command=command, cwd=cwd)
        except subprocess.CalledProcessError as e:
            self._beamLog(logName, e.output, e.returncode)
            raise
        else:
            self._beamLog(logName, output, returnCode=0)

    def _beamLog(self, logName, output, returnCode):
        logFilename = os.path.join(config.BUILD_CHROOT, "tmp", logName + ".log.txt")
        with open(logFilename, "w") as f:
            f.write(output)
            f.write("\nRETURN_CODE %d" % returnCode)
        run.run(["logbeam", "upload", logFilename])

    def _beamLogsDir(self, under, path):
        run.run(["logbeam", "upload", path, "--under", under])

    def _makeForATargetThatMayNotExist(self, logName, target, arguments=""):
        with makefiletricks.makefileForATargetThatMayNotExists(
                directory=self._git.directory(), makefileFilename=self._manifest.makefileFilename(),
                target=target) as tempMakefile:
            self._make(
                logName=logName,
                arguments=("-f %s %s " % (os.path.basename(tempMakefile), target)) + arguments)

    def _findBuildRootFSLabel(self):
        try:
            label = self._manifest.buildRootFSLabel()
            if self._buildRootFS is not None:
                raise Exception("Manifest contains build rootfs, but project marked as one without")
            return label
        except KeyError:
            try:
                buildRootFSGitBasename = self._manifest.buildRootFSRepositoryBasename()
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

    def _unmountBinds(self):
        for i in xrange(100):
            mounts = solvent.commonmistakes.CommonMistakes.mountedUnder(config.BUILD_CHROOT)
            if len(mounts) == 0:
                logging.info("After retries successfully unmounted all dangling mounts")
                return
            result = subprocess.call(["sudo", "umount", mounts[-1]['path']])
            if result != 0:
                logging.warning("Unable to umount '%(path)s'", dict(path=mounts[-1]['path']))
                time.sleep(0.2)
        logging.error("Unable to unmount dangling mounts even after many retries")

    def _mountBinds(self):
        for mountBind in self._MOUNT_BIND:
            run.run([
                "sudo", "mount", "-o", "bind", "/" + mountBind,
                os.path.join(config.BUILD_CHROOT, mountBind)])

    def _configureEnvironment(self):
        if 'OFFICIAL' not in os.environ.get('SOLVENT_CONFIG', ""):
            os.environ['SOLVENT_CLEAN'] = 'Yes'
        os.environ['SOLVENT_CONFIG'] = "\n".join([
            os.environ.get('SOLVENT_CONFIG', ""),
            "FORCE: yes"])
