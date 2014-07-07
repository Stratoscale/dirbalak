from realtimewebui import callbacks


class Callbacks:
    def __init__(self, multiverse):
        self._multiverse = multiverse
        callbacks.callbacks['userRequestsFetch'] = self._requestFetch
        callbacks.callbacks['userRequestsFetchAll'] = self._requestFetchAll

    def _requestFetch(self, project):
        project = self._multiverse.projects[project]
        project.needsFetch('User request to fetch project')

    def _requestFetchAll(self):
        self._multiverse.needsFetch('User request to fetch all')
