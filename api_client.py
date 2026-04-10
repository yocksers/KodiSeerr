import xbmcaddon
import time
from seerr_api import SeerrClient

_client_instance = None
_cached_settings = None
_last_settings_check = 0.0
_SETTINGS_CHECK_INTERVAL = 5.0

def get_client():
    global _client_instance, _cached_settings, _last_settings_check
    
    now = time.time()
    if _client_instance is not None and (now - _last_settings_check) < _SETTINGS_CHECK_INTERVAL:
        return _client_instance

    addon = xbmcaddon.Addon()
    if addon.getSettingBool("use_api_token"):
        _auth_method = "api_token"
    elif addon.getSettingBool("use_local_auth"):
        _auth_method = "local"
    else:
        _auth_method = "jellyfin"
    current_settings = (
        addon.getSetting("seerr_url").rstrip("/"),
        addon.getSetting("seerr_username"),
        addon.getSetting("seerr_password"),
        addon.getSetting("seerr_api_token"),
        _auth_method,
        addon.getSettingBool("allow_self_signed")
    )
    
    if _client_instance is None or _cached_settings != current_settings:
        if _client_instance is not None:
            _client_instance.close()
        url, username, password, api_token, auth_method, _allow_self_signed = current_settings
        _client_instance = SeerrClient(url, username, password, api_token, auth_method)
        _cached_settings = current_settings

    _last_settings_check = now
    return _client_instance

class _ClientProxy:
    """Proxy object that always returns the current client"""
    def __getattr__(self, name):
        return getattr(get_client(), name)

client = _ClientProxy()
