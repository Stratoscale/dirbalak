import solvent.label
from upseto import run
import re


class SolventOfficialLabels:
    def __init__(self, officialObjectStore):
        self._officialObjectStore = officialObjectStore
        labelRegex = solvent.label.label(basename = "(.*)", product="build", hash="(.*)", state="official")
        regex = re.compile(labelRegex)
        labels = run.run([
            'osmosis', 'listlabels', labelRegex,
            '--objectStores', self._officialObjectStore]).strip().split("\n")
        if labels == [""]:
            labels = []
        self._labels = set()
        for label in labels:
            basename, hash = regex.match(label).groups()
            self._labels.add((basename, hash))

    def built(self, basename, hash):
        assert 'master' not in hash
        return (basename, hash) in self._labels
