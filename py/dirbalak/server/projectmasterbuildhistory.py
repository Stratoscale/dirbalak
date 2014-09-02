import os
import logging
from dirbalak import config
import logbeam.compressedftpfilesystemabstraction


class ProjectMasterBuildHistory:
    def __init__(self, basename):
        self._basename = basename
        self._master = None
        self._builds = {}

    def history(self):
        result = []
        for build in sorted(self._builds.keys())[-10: ]:
            result.append(self._builds[build])
        return result

    def setMaster(self, hash):
        if hash == self._master:
            return
        self._builds = {}
        self._master = hash
        self.refresh()

    def refresh(self):
        if self._master is None:
            return
        dirname = os.path.join(config.LOGBEAM_ROOT_DIR, self._basename)
        logsFilesystem = logbeam.compressedftpfilesystemabstraction.CompressedFTPFilesystemAbstraction()
        with logsFilesystem.filesystem() as fs:
            for build in fs.listdir(dirname):
                if not build.endswith(self._master):
                    continue
                if build in self._builds:
                    continue
                self._parseBuild(build, fs)

    def _parseBuild(self, build, fs):
        dirname = os.path.join(config.LOGBEAM_ROOT_DIR, self._basename, build)
        try:
            with fs.open(os.path.join(dirname, config.CLEANBUILD_LOG_FILENAME)) as f:
                lines = f.readlines()
        except Exception as e:
            logging.exception(
                "Can't parse '%(basename)s/%(build)s/%(cleanBuildLogFilename)s'. "
                "Maybe not done? (%(exception)s)",
                dict(
                    basename=self._basename, build=build, exception=str(e),
                    cleanBuildLogFilename=config.CLEANBUILD_LOG_FILENAME))
            return
        logging.info(
            "Parsed '%(basename)s/%(build)s/%(cleanBuildLogFilename)s': %(returnCode)s",
            dict(
                basename=self._basename, build=build, returnCode=lines[-2],
                cleanBuildLogFilename=config.CLEANBUILD_LOG_FILENAME))
        if lines[-1] == 'RETURN_CODE 0\n':
            result = dict(successfull=True)
        else:
            result = dict(successfull=False)
        self._builds[build] = result
