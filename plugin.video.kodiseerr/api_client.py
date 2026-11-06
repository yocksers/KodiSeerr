import xbmcaddon
import time
import cache
import users
from seerr_api import SeerrClient

_client_instance = None
_cached_settings = None
_last_settings_check = 0.0
_SETTINGS_CHECK_INTERVAL = 5.0

def _read_settings():
    addon = xbmcaddon.Addon()
    if addon.getSettingBool("use_api_token"):
        identity = ("api_token", addon.getSetting("seerr_api_token"))
    else:
        user = users.active_user()
        identity = (user["auth"], user["login"], user["id"]) if user else ()
    return (
        users.owner_for(*identity),
        users.server_url(),
        identity,
        addon.getSettingBool("allow_self_signed")
    )

def current_owner():
    return _read_settings()[0]

def _build_client(owner, url, identity):
    if not identity:
        return SeerrClient(url, None, None)
    if identity[0] == "api_token":
        return SeerrClient(url, None, None, identity[1], "api_token")
    auth_method, login, user_id = identity
    return SeerrClient(url, login, None, auth_method=auth_method, session_store=users.SessionStore(owner, user_id))

def get_client():
    global _client_instance, _cached_settings, _last_settings_check

    now = time.time()
    if _client_instance is not None and (now - _last_settings_check) < _SETTINGS_CHECK_INTERVAL:
        return _client_instance

    current_settings = _read_settings()

    if _client_instance is None or _cached_settings != current_settings:
        if _client_instance is not None:
            _client_instance.close()
        owner, url, identity, _allow_self_signed = current_settings
        cache.bind(owner)
        _client_instance = _build_client(owner, url, identity)
        _cached_settings = current_settings

    _last_settings_check = now
    return _client_instance

def reset():
    global _client_instance, _cached_settings
    if _client_instance is not None:
        _client_instance.close()
    _client_instance = None
    _cached_settings = None
    cache.bind(current_owner())

class _ClientProxy:
    """Proxy object that always returns the current client"""
    def __getattr__(self, name):
        return getattr(get_client(), name)

client = _ClientProxy()
