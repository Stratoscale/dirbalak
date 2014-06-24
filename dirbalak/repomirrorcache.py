from dirbalak import repomirror


_cache = {}


def get(gitURL):
    if gitURL not in _cache:
        mirror = repomirror.RepoMirror(gitURL)
        mirror.fetch()
        _cache[gitURL] = mirror
    return _cache[gitURL]
