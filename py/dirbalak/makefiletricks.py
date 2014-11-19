import contextlib
import os
import re
from upseto import run


@contextlib.contextmanager
def makefileForATargetThatMayNotExists(directory, makefileFilename, target):
    makefile = os.path.join(directory, "fakeMakefileForTargetThatDoesNotExist")
    with open(makefile, "w") as f:
        f.write("include %s\n%s:\n" % (makefileFilename, target))
    yield makefile
    os.unlink(makefile)


def targetDoesNotDependOnAnything(directory, makefileFilename, target):
    with makefileForATargetThatMayNotExists(directory, makefileFilename, target) as tempMakefile:
        output = run.run(["make", "-f", tempMakefile, target, "--just-print", "-d"], directory)
    relevantLines = _linesUnderTargetConsideration(output, target)
    return 'Considering' not in "\n".join(relevantLines)


def defaultTargetDependsOnTarget(directory, makefileFilename, target):
    output = run.run(["make", "-f", makefileFilename, "--just-print", "-d"], directory)
    return re.search(r"Considering .*\`%s\'" % target, output) is not None


def _linesUnderTargetConsideration(output, target):
    lines = output.strip().split("\n")
    considerLine = re.compile(r"Considering .*\`%s\'" % target)
    considerLineIndex = None
    for i in xrange(len(lines)):
        if considerLine.match(lines[i]):
            considerLineIndex = i
            break
    if considerLineIndex is None:
        raise Exception("Did not find target '%s' in make -d output:\n%s" % (target, output))
    for i in xrange(considerLineIndex + 1, len(lines)):
        if lines[i][0] != ' ':
            return lines[considerLineIndex + 1: i]
    raise Exception("Did not find termination of consideration")
