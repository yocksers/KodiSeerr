import time

_cache = {}


def get_cached(key):
    import context
    if not context.addon.getSettingBool('enable_caching'):
        return None
    entry = _cache.get(key)
    if entry:
        cache_duration = context.addon.getSettingInt('cache_duration') * 60
        if time.time() - entry.get('timestamp', 0) < cache_duration:
            return entry.get('data')
    return None


def set_cached(key, data):
    import context
    if context.addon.getSettingBool('enable_caching'):
        _cache[key] = {'data': data, 'timestamp': time.time()}


def remove(key):
    _cache.pop(key, None)


def clear():
    global _cache
    _cache = {}
