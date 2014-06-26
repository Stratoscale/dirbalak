from dirbalak import repomirror


_cache = {}


fetch = True


def get(gitURL):
    if gitURL not in _cache:
        mirror = repomirror.RepoMirror(gitURL)
        if fetch:
            mirror.fetch()
        else:
            mirror.existing()
        _cache[gitURL] = mirror
    return _cache[gitURL]
