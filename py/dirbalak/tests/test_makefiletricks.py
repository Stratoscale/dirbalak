import unittest
from dirbalak import makefiletricks
import tempfile
import os


class Test(unittest.TestCase):
    def test_TargetMapSimpleMakefile(self):
        contents = "a: b\nb: c\\\nd\nd:e\n"
        temp = tempfile.NamedTemporaryFile()
        temp.write(contents)
        temp.flush()
        defaultTarget, map = makefiletricks._targetMap(temp.name)
        self.assertEquals(defaultTarget, 'a')
        self.assertEquals(map, dict(
            a=['b'],
            b=['c', 'd'],
            d=['e']))
        self.assertEquals(
            makefiletricks._reachable(map, 'b'),
            set(['b', 'c', 'd', 'e']))
        self.assertEquals(
            makefiletricks._reachable(map, 'a'),
            set(['a', 'b', 'c', 'd', 'e']))
        self.assertEquals(
            makefiletricks._reachable(map, 'c'),
            set(['c']))
        self.assertEquals(
            makefiletricks._reachable(map, 'd'),
            set(['d', 'e']))
        self.assertEquals(
            makefiletricks._reachable(map, 'e'),
            set(['e']))

    def test_RealMakefile(self):
        makefile = os.path.join(os.path.dirname(__file__), "samplemakefile.Makefile")
        defaultTarget, map = makefiletricks._targetMap(makefile)
        self.assertEquals(defaultTarget, 'all')
        self.assertEquals(map['submit'], [])
        self.assertEquals(
            makefiletricks._reachable(map, 'submit'),
            set(['submit']))
        self.assertTrue(makefiletricks.targetDoesNotDependOnAnything(
            os.path.dirname(__file__), "samplemakefile.Makefile", 'submit'))
        self.assertFalse(makefiletricks._containsSudoSolventSubmitWithoutMinusE(
            os.path.dirname(__file__), "samplemakefile.Makefile"))

    def test_ContainsSudoSolventSubmitWithoutMinusE(self):
        contents = "submit:\n\tsudo solvent submit build/rootfs\n"
        temp = tempfile.NamedTemporaryFile()
        temp.write(contents)
        temp.flush()
        self.assertTrue(makefiletricks._containsSudoSolventSubmitWithoutMinusE(
            os.path.dirname(temp.name), os.path.basename(temp.name)))


if __name__ == '__main__':
    unittest.main()
