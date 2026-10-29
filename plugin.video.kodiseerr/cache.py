import hashlib
import json
import time
import xbmcaddon
import xbmcgui
import xbmcvfs

_CACHE_PROPERTY = 'kodiseerr_c83c803f_cache_v2_'


def get_scope():
    addon = xbmcaddon.Addon('plugin.video.kodiseerr')
    # Include credentials so changing a login cannot reuse the previous session.
    identity = [xbmcvfs.translatePath('special://profile/'),
                addon.getSetting('seerr_url').rstrip('/'),
                addon.getSetting('use_api_token'), addon.getSetting('use_local_auth'),
                addon.getSetting('seerr_username'), addon.getSetting('seerr_password'),
                addon.getSetting('seerr_api_token')]
    return hashlib.sha256(json.dumps(identity).encode('utf-8')).hexdigest()


def _hash_key(key):
    return hashlib.sha256(str(key).encode('utf-8')).hexdigest()


def _load(scope):
    raw = xbmcgui.Window(10000).getProperty(_CACHE_PROPERTY + scope)
    try:
        data = json.loads(raw) if raw else {}
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


def _save(scope, data):
    xbmcgui.Window(10000).setProperty(_CACHE_PROPERTY + scope, json.dumps(data, separators=(',', ':')))


def load_cache():
    # Read from the scoped window property at each operation, including services.
    return _load(get_scope())


def get_cached(key, scope=None):
    if not xbmcaddon.Addon('plugin.video.kodiseerr').getSettingBool('enable_caching'):
        return None
    entry = _load(scope or get_scope()).get(_hash_key(key))
    if entry and time.time() - entry.get('timestamp', 0) < entry.get('duration', 60):
        return entry.get('data')
    return None


def set_cached(key, data, scope=None):
    addon = xbmcaddon.Addon('plugin.video.kodiseerr')
    if not addon.getSettingBool('enable_caching'):
        return
    scope = scope or get_scope()
    entries = _load(scope)
    entries[_hash_key(key)] = {'data': data, 'timestamp': time.time(),
                               'duration': addon.getSettingInt('cache_duration') * 60}
    _save(scope, entries)


def remove(key, scope=None):
    scope = scope or get_scope()
    entries = _load(scope)
    entries.pop(_hash_key(key), None)
    _save(scope, entries)


def clear():
    xbmcgui.Window(10000).setProperty(_CACHE_PROPERTY + get_scope(), '')


def clean_cache():
    scope = get_scope()
    now = time.time()
    _save(scope, {k: v for k, v in _load(scope).items()
                  if now - v.get('timestamp', 0) <= v.get('duration', 60)})
