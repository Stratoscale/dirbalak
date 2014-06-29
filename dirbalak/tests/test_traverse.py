import unittest
from dirbalak import traverse
from dirbalak import repomirrorcache


class Empty:
    pass


class FakeMirror:
    def __init__(self, masterHash, upsetoRequirementsByHash, solventRequirementsByHash):
        self._masterHash = masterHash
        self._upsetoRequirementsByHash = upsetoRequirementsByHash
        self._solventRequirementsByHash = solventRequirementsByHash

    def hash(self, expectedBranchName):
        assert expectedBranchName == "origin/master"
        return self._masterHash

    def upsetoManifest(self, hash):
        result = Empty()
        result.requirements = lambda: self._upsetoRequirementsByHash[hash]
        return result

    def solventManifest(self, hash):
        result = Empty()
        result.requirements = lambda: self._solventRequirementsByHash[hash]
        return result


class Test(unittest.TestCase):
    def setUp(self):
        self.mirrors = {}
        repomirrorcache.get = self.getMirror

    def getMirror(self, gitURL):
        return self.mirrors[gitURL]

    def test_NoRequirements(self):
        self.mirrors['dependencilessProject'] = FakeMirror(
            'master hash', {'origin/master': []}, {'origin/master': []})
        tested = traverse.Traverse()
        dependencies = list(tested.traverse('dependencilessProject', 'origin/master'))
        self.assertEquals(len(dependencies), 1)
        self.assertEquals(dependencies[0], traverse.Dependency(
            'dependencilessProject', 'origin/master', None, None, 'root', 'master hash'))

    def test_UpsetoRequirement_MasterToMaster(self):
        self.mirrors['upsetoDepedantProject'] = FakeMirror(
            'master hash 2',
            {'origin/master': [dict(originURL='dependencilessProject', hash='master hash')]},
            {'origin/master': []})
        self.mirrors['dependencilessProject'] = FakeMirror(
            'master hash', {'origin/master': []}, {'origin/master': []})
        tested = traverse.Traverse()
        dependencies = list(tested.traverse('upsetoDepedantProject', 'origin/master'))
        self.assertEquals(len(dependencies), 3)
        self.assertIn(traverse.Dependency(
            'dependencilessProject', 'origin/master', 'upsetoDepedantProject',
            'origin/master', 'upseto', 'master hash'), dependencies)
        self.assertIn(traverse.Dependency(
            'upsetoDepedantProject', 'origin/master', None, None, 'root', 'master hash 2'), dependencies)
        self.assertIn(traverse.Dependency(
            'dependencilessProject', 'origin/master', None, None, 'master', 'master hash'), dependencies)

    def test_UpsetoRequirement_MasterToOlder(self):
        self.mirrors['upsetoDepedantProject'] = FakeMirror(
            'master hash 2',
            {'origin/master': [dict(originURL='dependencilessProject', hash='non master hash')]},
            {'origin/master': []})
        self.mirrors['dependencilessProject'] = FakeMirror(
            'master hash', {'origin/master': [], 'non master hash': []},
            {'origin/master': [], 'non master hash': []})
        tested = traverse.Traverse()
        dependencies = list(tested.traverse('upsetoDepedantProject', 'origin/master'))
        self.assertEquals(len(dependencies), 3)
        self.assertIn(traverse.Dependency(
            'dependencilessProject', 'non master hash', 'upsetoDepedantProject',
            'origin/master', 'upseto', 'master hash'), dependencies)
        self.assertIn(traverse.Dependency(
            'upsetoDepedantProject', 'origin/master', None, None, 'root', 'master hash 2'), dependencies)
        self.assertIn(traverse.Dependency(
            'dependencilessProject', 'origin/master', None, None, 'master', 'master hash'), dependencies)

    def test_SolventRequirement_MasterToMaster(self):
        self.mirrors['solventDepedantProject'] = FakeMirror(
            'master hash 2', {'origin/master': []},
            {'origin/master': [dict(originURL='dependencilessProject', hash='master hash')]})
        self.mirrors['dependencilessProject'] = FakeMirror(
            'master hash', {'origin/master': []}, {'origin/master': []})
        tested = traverse.Traverse()
        dependencies = list(tested.traverse('solventDepedantProject', 'origin/master'))
        self.assertEquals(len(dependencies), 3)
        self.assertIn(traverse.Dependency(
            'dependencilessProject', 'origin/master', 'solventDepedantProject',
            'origin/master', 'solvent', 'master hash'), dependencies)
        self.assertIn(traverse.Dependency(
            'solventDepedantProject', 'origin/master', None, None, 'root', 'master hash 2'), dependencies)
        self.assertIn(traverse.Dependency(
            'dependencilessProject', 'origin/master', None, None, 'master', 'master hash'), dependencies)

    def test_SolventRequirement_MasterToOlder(self):
        self.mirrors['solventDepedantProject'] = FakeMirror(
            'master hash 2', {'origin/master': []},
            {'origin/master': [dict(originURL='dependencilessProject', hash='non master hash')]})
        self.mirrors['dependencilessProject'] = FakeMirror(
            'master hash', {'origin/master': [], 'non master hash': []},
            {'origin/master': [], 'non master hash': []})
        tested = traverse.Traverse()
        dependencies = list(tested.traverse('solventDepedantProject', 'origin/master'))
        self.assertEquals(len(dependencies), 3)
        self.assertIn(traverse.Dependency(
            'dependencilessProject', 'non master hash', 'solventDepedantProject',
            'origin/master', 'solvent', 'master hash'), dependencies)
        self.assertIn(traverse.Dependency(
            'solventDepedantProject', 'origin/master', None, None, 'root', 'master hash 2'), dependencies)
        self.assertIn(traverse.Dependency(
            'dependencilessProject', 'origin/master', None, None, 'master', 'master hash'), dependencies)


if __name__ == '__main__':
    unittest.main()
