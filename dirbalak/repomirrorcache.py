from dirbalak import repomirror
import logging


_cache = {}


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
