import hashlib
import json
import time

import xbmcgui

_CACHE_PROPERTY = "kodiseerr_c83c803f_cache"
_SESSION_PROPERTY = "kodiseerr_c83c803f_session"
_cache = {}
# Fingerprint of the Kodi profile + Seerr identity the cache belongs to. The Home
# window is shared by all profiles, so data written under another owner is ignored.
_owner = None


def _hash_key(key):
    return hashlib.sha256(str(key).encode("utf-8")).hexdigest()


def load_cache():
    import api_client
    bind(api_client.current_owner())


def bind(owner):
    global _cache, _owner
    if owner == _owner:
        return
    _owner = owner
    _cache = {}
    window = xbmcgui.Window(10000)
    raw = window.getProperty(_CACHE_PROPERTY)
    if raw:
        try:
            stored = json.loads(raw)
            if stored.get('owner') == owner:
                _cache = stored.get('entries', {})
        except Exception:
            _cache = {}


def save_cache():
    window = xbmcgui.Window(10000)
    window.setProperty(_CACHE_PROPERTY, json.dumps({'owner': _owner, 'entries': _cache}, separators=(',', ':')))


def get_cached(key):
    import context
    if not context.addon.getSettingBool('enable_caching'):
        return None
    if _owner is None:
        load_cache()
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
    if _owner is None:
        load_cache()
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
    clear_session()


def get_session(owner):
    window = xbmcgui.Window(10000)
    raw = window.getProperty(_SESSION_PROPERTY)
    if not raw:
        return None
    try:
        stored = json.loads(raw)
    except Exception:
        return None
    if stored.get('owner') != owner:
        return None
    return stored.get('cookies')


def set_session(owner, cookies):
    window = xbmcgui.Window(10000)
    window.setProperty(_SESSION_PROPERTY, json.dumps({'owner': owner, 'cookies': cookies}, separators=(',', ':')))


def clear_session():
    window = xbmcgui.Window(10000)
    window.clearProperty(_SESSION_PROPERTY)


def clean_cache():
    global _cache
    current_time = time.time()
    expired = [k for k, v in _cache.items() if current_time - v.get('timestamp', 0) > v.get('duration', 60)]
    for k in expired:
        _cache.pop(k, None)
    if expired:
        save_cache()
