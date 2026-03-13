import xbmcaddon
import time
from jellyseerr_api import JellyseerrClient

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
    current_settings = (
        addon.getSetting("jellyseerr_url").rstrip("/"),
        addon.getSetting("jellyseerr_username"),
        addon.getSetting("jellyseerr_password"),
        addon.getSetting("jellyseerr_api_token"),
        "api_token" if addon.getSettingBool("use_api_token") else "password",
        addon.getSettingBool("allow_self_signed")
    )
    
    if _client_instance is None or _cached_settings != current_settings:
        if _client_instance is not None:
            _client_instance.close()
        url, username, password, api_token, auth_method, _ = current_settings
        _client_instance = JellyseerrClient(url, username, password, api_token, auth_method)
        _cached_settings = current_settings

    _last_settings_check = now
    return _client_instance

class _ClientProxy:
    """Proxy object that always returns the current client"""
    def __getattr__(self, name):
        return getattr(get_client(), name)

client = _ClientProxy()
