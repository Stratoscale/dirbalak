import logging


class BuildState:
    def __init__(self):
        self._jobs = dict()

    def get(self, gitURL, hash):
        assert hash != 'origin/master'
        result = self._jobs.get((gitURL, hash), None)
        if result is None:
            return dict(successes=0, failures=0, inProgress=False)
        return result

    def inProgress(self, gitURL, hash):
        assert hash != 'origin/master'
        value = dict(self.get(gitURL, hash))
        value['inProgress'] = True
        self._jobs[(gitURL, hash)] = value
        logging.info("Job %(gitURL)s/%(hash)s now in progress", dict(gitURL=gitURL, hash=hash))

    def done(self, gitURL, hash, success):
        assert hash != 'origin/master'
        value = dict(self.get(gitURL, hash))
        value['inProgress'] = False
        if success:
            value['successes'] += 1
        else:
            value['failures'] += 1
        self._jobs[(gitURL, hash)] = value
        logging.info("Job %(gitURL)s/%(hash)s no longer in progress", dict(gitURL=gitURL, hash=hash))
