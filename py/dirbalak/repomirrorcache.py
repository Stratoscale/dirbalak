from dirbalak import repomirror
import multiprocessing.pool
import logging


_cache = {}
_CONCURRENCY = 32


fetch = True


def get(gitURL):
    if gitURL not in _cache:
        mirror = repomirror.RepoMirror(gitURL)
        if fetch:
            logging.info("Fetching repo %(gitURL)s", dict(gitURL=gitURL))
            mirror.fetch()
        else:
            mirror.existing()
        _cache[gitURL] = mirror
    return _cache[gitURL]


def prepopulate(gitURLs):
    pool = multiprocessing.pool.ThreadPool(_CONCURRENCY)
    futures = []
    for url in gitURLs:
        if url in _cache:
            continue
        mirror = repomirror.RepoMirror(url)
        future = pool.apply_async(_fetchSubthread, args=(mirror,))
        futures.append(future)
    for future in futures:
        future.get()


def _fetchSubthread(mirror):
    logging.info("Fetching repo %(gitURL)s", dict(gitURL=mirror.gitURL()))
    mirror.fetch()
