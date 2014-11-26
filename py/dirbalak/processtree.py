import os
import time
import logging
from dirbalak import run


def parentMap():
    result = {}
    for filename in os.listdir("/proc"):
        try:
            pid = int(filename)
        except:
            continue
        with open(os.path.join("/proc", filename, 'stat')) as f:
            parentPid = int(f.read().split(' ')[3])
        result[pid] = parentPid
    return result


def childrenMap():
    result = {}
    for pid, parent in parentMap().iteritems():
        result.setdefault(parent, []).append(pid)
    return result


def children(pid):
    map = childrenMap()
    children = set(map.get(pid, []))
    before = 0
    while before != len(children):
        before = len(children)
        for child in list(children):
            children |= set(map.get(child, []))
    return children


def pidLive(pid):
    if not os.path.exists(os.path.join("/proc", str(pid))):
        return False
    with open(os.path.join("/proc", str(pid), "status")) as f:
        return 'State:\tZ' not in f.read()


def devourMyChildren():
    pids = children(os.getpid())
    INTERVAL = 0.2
    NORMAL_KILLS = 15
    BRUTE_KILLS = 3
    if len(pids) > 0:
        logging.warning("Children tree not dead. ps -Af:\n%(output)s", dict(
            output=run.run(["ps", "-Af", "--forest"])))
    for i in xrange(NORMAL_KILLS):
        if len(pids) > 0:
            logging.warning("Children tree not dead, killing SIGTERM these processes: %(procs)s", dict(
                procs=pids))
            for pid in pids:
                try:
                    run.run(['sudo', 'kill', '-TERM', str(pid)])
                except:
                    pass
            time.sleep(INTERVAL)
            pids = [p for p in pids if pidLive(p)]
    for i in xrange(BRUTE_KILLS):
        if len(pids) > 0:
            logging.warning("Children tree not dead, killing SIGKILL these processes: %(procs)s", dict(
                procs=pids))
            for pid in pids:
                try:
                    run.run(['sudo', 'kill', '-KILL', str(pid)])
                except:
                    pass
            time.sleep(INTERVAL)
            pids = [p for p in pids if pidLive(p)]
    logging.warning("Children left behind: %(procs)s", dict(procs=pids))


if __name__ == "__main__":
    import sys
    print children(int(sys.argv[1]))
