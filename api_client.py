import xbmcaddon
from jellyseerr_api import JellyseerrClient

_client_instance = None
_cached_settings = None

def get_client():
    """Get the API client, creating a new one if settings have changed"""
    global _client_instance, _cached_settings
    
    addon = xbmcaddon.Addon()
    current_settings = (
        addon.getSetting("jellyseerr_url").rstrip("/"),
        addon.getSetting("jellyseerr_username"),
        addon.getSetting("jellyseerr_password"),
        addon.getSetting("jellyseerr_api_token"),
        addon.getSetting("auth_method") or "password",
        addon.getSettingBool("allow_self_signed")
    )
    
    if _client_instance is None or _cached_settings != current_settings:
        url, username, password, api_token, auth_method, _ = current_settings
        _client_instance = JellyseerrClient(url, username, password, api_token, auth_method)
        _cached_settings = current_settings
    
    return _client_instance

class _ClientProxy:
    """Proxy object that always returns the current client"""
    def __getattr__(self, name):
        return getattr(get_client(), name)

client = _ClientProxy()
