from rackattack.ssh import connection
from rackattack import api
from dirbalak import config
from dirbalak import rackrun
import dirbalak.rackrun.config
import os
import re
import logging
import subprocess
import urlparse
import socket
from upseto import gitwrapper


class OfficialBuildHost:
    _TIMEOUT = 8 * 60

    def __init__(self, client, nice=0):
        requirement = api.Requirement(imageLabel=config.OFFICIAL_BUILD_ROOTFS, imageHint="build")
        allocationInfo = api.AllocationInfo(user="dirbalak-build", purpose="officialbuild", nice=nice)
        logging.info("Construction of an official build host: Before allocation")
        self._allocation = client.allocate(
            requirements=dict(node=requirement), allocationInfo=allocationInfo)
        logging.info("Construction of an official build host: Allocation succeeded")

    def setForceReleaseCallback(self, callback):
        self._allocation.setForceReleaseCallback(callback)

    def close(self):
        if hasattr(self, '_ssh'):
            self._ssh.close()
        if not self._allocation.dead():
            self._allocation.free()

    def setUp(self, netRCFile):
        logging.info("Waiting for allocation to complete")
        self._allocation.wait(timeout=self._TIMEOUT)
        logging.info("Done waiting for allocation to complete")
        self._node = self._allocation.nodes()['node']
        self._ssh = connection.Connection(** self._node.rootSSHCredentials())
        logging.info("Waiting for ssh connection")
        self._allocation.wait()
        self._ssh.waitForTCPServer()
        self._ssh.connect()
        logging.info("Done waiting for ssh connection")
        self._configureSolvent()
        self._configurePyracktest()
        self._ssh.ftp.putFile("/root/.netrc", netRCFile)
        self._ssh.ftp.putFile(
            "/root/dirbalakbuild.egg", os.path.join(rackrun.config.DIRBALAK_EGG_DIR, "dirbalakbuild.egg"))
        self._ssh.ftp.putFile("/etc/resolv.conf", "/etc/resolv.conf")
        self._ssh.run.script("sed 's/.*requiretty.*//' -i /etc/sudoers")
        logging.info("Setup of official build host completed successfully")

    def ipAddress(self):
        return self._node.ipAddress()

    def build(self, gitURL, hash, submit, buildRootFS, logbeamBuildID):
        self._configureLogbeam(gitURL, logbeamBuildID)
        cleanBuildLine = "python -m dirbalak.main cleanbuild --gitURL '%s' --hash '%s' %s %s" % (
            gitURL, hash, "" if submit else "--nosubmit",
            "--rootfs=%s" % buildRootFS if buildRootFS is not None else "")
        self._ssh.run.script(
            "export PYTHONPATH=/root/dirbalakbuild.egg\n"
            "export SOLVENT_CONFIG='OFFICIAL_BUILD: Yes'\n"
            "export RACKATTACK_PROVIDER=%(rackattackProvider)s\n"
            "set -o pipefail\n"
            "%(commandLine)s |& tee /tmp/%(cleanBuildLogFilename)s\n"
            "result=$?\n"
            "echo >> /tmp/%(cleanBuildLogFilename)s\n"
            "echo RETURN_CODE $result >> /tmp/%(cleanBuildLogFilename)s\n"
            "logbeam upload /tmp/%(cleanBuildLogFilename)s\n"
            "exit $result\n" % dict(
                commandLine=cleanBuildLine,
                rackattackProvider=self._rackattackProvider(),
                cleanBuildLogFilename=config.CLEANBUILD_LOG_FILENAME))

    def _configureSolvent(self):
        with open("/etc/solvent.conf") as f:
            solventConf = f.read()
        modified = re.sub("LOCAL_OSMOSIS:.*", "LOCAL_OSMOSIS: 127.0.0.1:1010", solventConf)
        # todo: change 127.0.0.1 -> localhost
        self._ssh.ftp.putContents("/etc/solvent.conf", modified)

    def _configurePyracktest(self):
        conf = "USER: dirbalak-pyracktest"
        self._ssh.ftp.putContents("/etc/racktest.conf", conf)

    def _configureLogbeam(self, gitURL, logbeamBuildID):
        basename = gitwrapper.originURLBasename(gitURL)
        under = os.path.join(config.LOGBEAM_ROOT_DIR, basename, logbeamBuildID)
        conf = subprocess.check_output(["logbeam", "createConfig", "--under", under])
        self._ssh.ftp.putContents("/etc/logbeam.config", conf)

    def _rackattackProvider(self):
        ipcURL, subURL = os.environ['RACKATTACK_PROVIDER'].split('@')
        return "%s@%s" % (self._hostnameToIP(ipcURL), self._hostnameToIP(subURL))

    def _hostnameToIP(self, url):
        parsed = urlparse.urlparse(url)
        hostname, port = parsed.netloc.split(":")
        ip = socket.gethostbyname(hostname)
        result = list(parsed)
        result[1] = "%s:%s" % (ip, port)
        return urlparse.urlunparse(result)


if __name__ == "__main__":
    import sys
    from rackattack import clientfactory
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    client = clientfactory.factory()
    host = OfficialBuildHost(client)
    try:
        host.setUp(sys.argv[1])
        host.build(sys.argv[2], sys.argv[3], False)
    except:
        logging.exception("failed")
    finally:
        print host._node.rootSSHCredentials()
        os.system(
            "sshpass -p %(password)s ssh -o ServerAliveInterval=5 -o ServerAliveCountMax=1 "
            "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p %(port)d "
            "%(username)s@%(hostname)s" % host._node.rootSSHCredentials())
