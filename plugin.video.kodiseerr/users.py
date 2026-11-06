import hashlib
import json
import os
import shutil
import uuid

import requests
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import cache
from seerr_api import SeerrClient

_ACTIVE_PROPERTY = "kodiseerr_c83c803f_user"
_LEGACY_FILES = ("favorites.json", "preferences.json", "notified_requests.json")
_PUBLIC_FIELDS = ("id", "name", "login", "auth", "avatar")


def _addon_data_dir():
    addon_id = xbmcaddon.Addon().getAddonInfo('id')
    return xbmcvfs.translatePath(f"special://profile/addon_data/{addon_id}/")


def _profile_path():
    return xbmcvfs.translatePath("special://profile")


def _users_file():
    return os.path.join(_addon_data_dir(), "users.json")


def uses_api_token():
    return xbmcaddon.Addon().getSettingBool('use_api_token')


def server_url():
    return xbmcaddon.Addon().getSetting('seerr_url').rstrip('/')


def owner_for(*identity):
    raw = json.dumps([_profile_path(), server_url()] + list(identity))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def owner_of(user):
    return owner_for(user['auth'], user['login'], user['id'])


def new_user(name, login, auth):
    return {'id': uuid.uuid4().hex, 'name': name, 'login': login, 'auth': auth, 'avatar': ''}


def user_data_dir(user_id):
    return os.path.join(_addon_data_dir(), "users", user_id)


def data_path(filename):
    user = None if uses_api_token() else active_user()
    base = user_data_dir(user['id']) if user else _addon_data_dir()
    return os.path.join(base, filename)


def load_users():
    path = _users_file()
    if not os.path.exists(path):
        return _migrate_legacy_user()
    try:
        with open(path, 'r') as f:
            return json.load(f).get('users', [])
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Users load error: {e}", xbmc.LOGERROR)
        return []


def save_users(user_list):
    path = _users_file()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({'users': user_list}, f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Users save error: {e}", xbmc.LOGERROR)


def _migrate_legacy_user():
    addon = xbmcaddon.Addon()
    login = addon.getSetting('seerr_username')
    user_list = []
    if login:
        user = new_user(login, login, 'local' if addon.getSettingBool('use_local_auth') else 'jellyfin')
        target = user_data_dir(user['id'])
        try:
            os.makedirs(target, exist_ok=True)
            for filename in _LEGACY_FILES:
                source = os.path.join(_addon_data_dir(), filename)
                if os.path.exists(source):
                    shutil.copy2(source, os.path.join(target, filename))
        except Exception as e:
            xbmc.log(f"[KodiSeerr] User data migration error: {e}", xbmc.LOGERROR)
        user_list.append(user)
    save_users(user_list)
    return user_list


def purge_legacy_password():
    addon = xbmcaddon.Addon()
    if not addon.getSetting('seerr_password'):
        return
    load_users()
    addon.setSetting('seerr_password', '')


def get_user(user_id):
    return next((u for u in load_users() if u.get('id') == user_id), None)


def find_user(login, auth):
    return next((u for u in load_users() if u.get('login') == login and u.get('auth') == auth), None)


def add_user(user):
    user_list = load_users()
    user_list.append(user)
    save_users(user_list)


def update_user(user_id, **fields):
    user_list = load_users()
    for user in user_list:
        if user.get('id') == user_id:
            for key, value in fields.items():
                if value is None:
                    user.pop(key, None)
                else:
                    user[key] = value
    save_users(user_list)


def remove_user(user_id):
    if _active_id() == user_id:
        deactivate()
    save_users([u for u in load_users() if u.get('id') != user_id])
    shutil.rmtree(user_data_dir(user_id), ignore_errors=True)


def merge_users(imported):
    user_list = load_users()
    known_ids = {u.get('id') for u in user_list}
    known_logins = {(u.get('login'), u.get('auth')) for u in user_list}
    for entry in imported or []:
        if not isinstance(entry, dict) or not entry.get('id') or not entry.get('login'):
            continue
        if entry['id'] in known_ids or (entry.get('login'), entry.get('auth')) in known_logins:
            continue
        user_list.append({k: entry.get(k, '') for k in _PUBLIC_FIELDS})
    save_users(user_list)


def public_users():
    return [{k: u.get(k, '') for k in _PUBLIC_FIELDS} for u in load_users()]


def remember(user_id, cookies):
    update_user(user_id, session=cookies)


def forget(user_id):
    update_user(user_id, session=None)


def _active_id():
    raw = xbmcgui.Window(10000).getProperty(_ACTIVE_PROPERTY)
    if not raw:
        return None
    try:
        active = json.loads(raw)
    except Exception:
        return None
    if active.get('profile') != _profile_path():
        return None
    return active.get('id') or ""


def _set_active(user_id):
    xbmcgui.Window(10000).setProperty(_ACTIVE_PROPERTY, json.dumps({'profile': _profile_path(), 'id': user_id}))


def active_user():
    active_id = _active_id()
    if active_id is None:
        user_list = load_users()
        if len(user_list) == 1 and user_list[0].get('session'):
            activate(user_list[0], user_list[0]['session'])
            return user_list[0]
        return None
    user = get_user(active_id) if active_id else None
    if user and cache.get_session(owner_of(user)) is None:
        if not user.get('session'):
            return None
        cache.set_session(owner_of(user), user['session'])
    return user


def activate(user, cookies):
    _set_active(user['id'])
    cache.set_session(owner_of(user), cookies)


def deactivate():
    _set_active(None)
    cache.clear_session()


def authenticate(login, auth, password):
    client = SeerrClient(server_url(), login, password, auth_method=auth)
    try:
        if not client.login():
            return None
        profile = client.api_request('/auth/me')
        return requests.utils.dict_from_cookiejar(client.session.cookies), profile
    finally:
        client.close()


def sign_out(user):
    client = SeerrClient(server_url(), user['login'], None, auth_method=user['auth'], session_store=SessionStore(owner_of(user), user['id']))
    try:
        client.logout()
    finally:
        client.close()


class SessionStore:
    def __init__(self, owner, user_id):
        self.owner = owner
        self.user_id = user_id

    def load(self):
        return cache.get_session(self.owner)

    def expire(self):
        user = get_user(self.user_id)
        forget(self.user_id)
        if _active_id() == self.user_id:
            deactivate()
        name = user.get('name') if user else 'this user'
        xbmcgui.Dialog().notification('KodiSeerr', f'Session for {name} expired. Please sign in again.', xbmcgui.NOTIFICATION_WARNING, 5000)
