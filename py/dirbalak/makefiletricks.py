import contextlib
import os
import re
import logging


@contextlib.contextmanager
def makefileForATargetThatMayNotExists(directory, makefileFilename, target):
    makefile = os.path.join(directory, "fakeMakefileForTargetThatDoesNotExist")
    with open(makefile, "w") as f:
        f.write("include %s\n%s:\n" % (makefileFilename, target))
    yield makefile
    os.unlink(makefile)


def targetDoesNotDependOnAnything(directory, makefileFilename, target):
    defaultTarget, map = _targetMap(os.path.join(directory, makefileFilename))
    reachable = _reachable(map, target)
    if len(reachable) > 1:
        logging.info("target '%(target)s' depends on '%(reachable)s'", dict(
            target=target, reachable=reachable))
    return len(reachable) == 1


def defaultTargetDependsOnTarget(directory, makefileFilename, target):
    defaultTarget, map = _targetMap(os.path.join(directory, makefileFilename))
    reachable = _reachable(map, defaultTarget)
    return target in reachable


_DEPS_SEPERATOR = re.compile(r"\s+")


def _extractDeps(line):
    deps = _DEPS_SEPERATOR.split(line.strip(" \n\\"))
    return [d for d in deps if d != '']


def _targetMap(makefile):
    with open(makefile) as f:
        lines = f.readlines()
    TARGET = re.compile(r"^(\S.*):")
    result = {}
    defaultTarget = None
    for lineIndex in xrange(len(lines)):
        line = lines[lineIndex]
        match = TARGET.match(line)
        if match is not None:
            target = match.group(1)
            if defaultTarget is None:
                defaultTarget = target
            result.setdefault(target, [])
            result[target] += _extractDeps(line[len(match.group(1)) + 1:])
            prevLineIndex = lineIndex
            while lines[prevLineIndex].endswith("\\\n"):
                prevLineIndex += 1
                result[target] += _extractDeps(lines[prevLineIndex])
    return defaultTarget, result


def _reachable(map, origin):
    reachable = set([origin])
    previousSize = 0
    while previousSize != len(reachable):
        previousSize = len(reachable)
        for target in list(reachable):
            reachable |= set(map.get(target, []))
    return reachable
