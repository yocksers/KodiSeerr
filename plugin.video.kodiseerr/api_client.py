import hashlib
import json
import xbmcaddon
import xbmcvfs
import time
import cache
from seerr_api import SeerrClient

_client_instance = None
_cached_settings = None
_last_settings_check = 0.0
_SETTINGS_CHECK_INTERVAL = 5.0

def _read_settings():
    addon = xbmcaddon.Addon()
    if addon.getSettingBool("use_api_token"):
        _auth_method = "api_token"
    elif addon.getSettingBool("use_local_auth"):
        _auth_method = "local"
    else:
        _auth_method = "jellyfin"
    return (
        xbmcvfs.translatePath("special://profile"),
        addon.getSetting("seerr_url").rstrip("/"),
        addon.getSetting("seerr_username"),
        addon.getSetting("seerr_password"),
        addon.getSetting("seerr_api_token"),
        _auth_method,
        addon.getSettingBool("allow_self_signed")
    )

def _owner_of(settings):
    """Fingerprint of the Kodi profile and Seerr identity that cached data and sessions belong to"""
    profile, url, username, password, api_token, auth_method, _allow_self_signed = settings
    credentials = [api_token] if auth_method == "api_token" else [username, password]
    raw = json.dumps([profile, url, auth_method] + credentials)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def current_owner():
    return _owner_of(_read_settings())

def get_client():
    global _client_instance, _cached_settings, _last_settings_check
    
    now = time.time()
    if _client_instance is not None and (now - _last_settings_check) < _SETTINGS_CHECK_INTERVAL:
        return _client_instance

    current_settings = _read_settings()

    if _client_instance is None or _cached_settings != current_settings:
        if _client_instance is not None:
            _client_instance.close()
        _profile, url, username, password, api_token, auth_method, _allow_self_signed = current_settings
        owner = _owner_of(current_settings)
        cache.bind(owner)
        _client_instance = SeerrClient(url, username, password, api_token, auth_method, session_owner=owner)
        _cached_settings = current_settings

    _last_settings_check = now
    return _client_instance

class _ClientProxy:
    """Proxy object that always returns the current client"""
    def __getattr__(self, name):
        return getattr(get_client(), name)

client = _ClientProxy()
