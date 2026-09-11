import hashlib
import json
import time

import xbmcgui

_CACHE_PROPERTY = "kodiseerr_c83c803f_cache"
_cache = {}


def _hash_key(key):
    return hashlib.sha256(str(key).encode("utf-8")).hexdigest()


def load_cache():
    global _cache
    window = xbmcgui.Window(10000)
    raw = window.getProperty(_CACHE_PROPERTY)
    if raw:
        try:
            _cache = json.loads(raw)
        except Exception:
            _cache = {}


def save_cache():
    window = xbmcgui.Window(10000)
    window.setProperty(_CACHE_PROPERTY, json.dumps(_cache, separators=(',', ':')))


def get_cached(key):
    import context
    if not context.addon.getSettingBool('enable_caching'):
        return None
    hashed = _hash_key(key)
    entry = _cache.get(hashed)
    if entry:
        if time.time() - entry.get('timestamp', 0) < entry.get('duration', 60):
            return entry.get('data')
    return None


def set_cached(key, data):
    import context
    if not context.addon.getSettingBool('enable_caching'):
        return
    duration = context.addon.getSettingInt('cache_duration') * 60
    hashed = _hash_key(key)
    _cache[hashed] = {'data': data, 'timestamp': time.time(), 'duration': duration}
    save_cache()


def remove(key):
    hashed = _hash_key(key)
    if _cache.pop(hashed, None) is not None:
        save_cache()


def clear():
    global _cache
    _cache = {}
    window = xbmcgui.Window(10000)
    window.setProperty(_CACHE_PROPERTY, "")


def clean_cache():
    global _cache
    current_time = time.time()
    expired = [k for k, v in _cache.items() if current_time - v.get('timestamp', 0) > v.get('duration', 60)]
    for k in expired:
        _cache.pop(k, None)
    if expired:
        save_cache()
