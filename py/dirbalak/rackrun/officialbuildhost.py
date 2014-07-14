from rackattack.ssh import connection
from rackattack import api
import re
import logging


class OfficialBuildHost:
    def __init__(self, client, nice=0):
        requirement = api.Requirement(
            imageLabel="solvent__rootfs-build__rootfs__b28426f0192d2d2a82f697672468320c9392a911__clean",
            imageHint="build")
        allocationInfo = api.AllocationInfo(user="dirbalak", purpose="officialbuild", nice=nice)
        self._allocation = client.allocate(
            requirements=dict(node=requirement), allocationInfo=allocationInfo)

    def setUp(self, netRCFile):
        logging.info("Waiting for allocation to complete")
        self._allocation.wait()
        logging.info("Done waiting for allocation to complete")
        self._node = self._allocation.nodes()['node']
        self._ssh = connection.Connection(** self._node.rootSSHCredentials())
        logging.info("Waiting for ssh connection")
        self._allocation.wait()
        self._ssh.waitForTCPServer()
        self._ssh.connect()
        logging.info("Done waiting for ssh connection")
        self._configureSolvent()
        self._ssh.ftp.putFile("/root/.netrc", netRCFile)
        self._ssh.ftp.putFile("/root/dirbalakbuild.egg", "build/dirbalakbuild.egg")
        self._ssh.ftp.putFile("/etc/resolv.conf", "/etc/resolv.conf")
        self._ssh.run.script("sed 's/.*requiretty.*//' -i /etc/sudoers")
        logging.info("Setup of official build host completed successfully")

    def build(self, gitURL, hash, submit):
        self._ssh.run.script(
            "PYTHONPATH=/root/dirbalakbuild.egg SOLVENT_CONFIG='OFFICIAL_BUILD: Yes' "
            "python -m dirbalak.main cleanbuild --gitURL '%s' --hash '%s' %s" % (
                gitURL, hash, "" if submit else "--nosubmit" ))

    def _configureSolvent(self):
        with open("/etc/solvent.conf") as f:
            solventConf = f.read()
        modified = re.sub("LOCAL_OSMOSIS:.*", "LOCAL_OSMOSIS: 127.0.0.1:1010", solventConf)
        self._ssh.ftp.putContents("/etc/solvent.conf", modified)


if __name__ == "__main__":
    import sys
    from rackattack import clientfactory
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    client = clientfactory.factory()
    host = OfficialBuildHost(client)
    try:
        host.setUp(sys.argv[1])
        host.build(sys.argv[2], sys.argv[3], False)
    except:
        logging.exception("failed")
    finally:
        print host._node.rootSSHCredentials()
        import os
        os.system(
            "sshpass -p %(password)s ssh -o ServerAliveInterval=5 -o ServerAliveCountMax=1 "
            "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p %(port)d "
            "%(username)s@%(hostname)s" % host._node.rootSSHCredentials())
