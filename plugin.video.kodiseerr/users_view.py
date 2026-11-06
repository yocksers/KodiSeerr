import xbmc
import xbmcgui
import xbmcplugin
import api_client
import context
import users
from utils import build_url

_AUTH_TYPES = [
    ('jellyfin', 'Jellyfin / Emby account'),
    ('local', 'Local Seerr account (email)'),
]


def _avatar(user):
    return user.get('avatar') or 'DefaultUser.png'


def _user_item(user):
    item = xbmcgui.ListItem(user['name'])
    if user.get('session'):
        item.setLabel2('Remembered')
    item.setArt({'icon': _avatar(user), 'thumb': _avatar(user)})
    return item


def _reload():
    path = xbmc.getInfoLabel('Container.FolderPath')
    root = context.base_url.rstrip('/')
    if not path.startswith(root):
        return
    if path.rstrip('/') == root:
        xbmc.executebuiltin('Container.Refresh')
    else:
        xbmc.executebuiltin(f'Container.Update({context.base_url},replace)')


def _store_profile(user, profile):
    if not profile:
        return
    avatar = profile.get('avatar') or ''
    if avatar.startswith('/'):
        avatar = users.server_url() + avatar
    if avatar and avatar != user.get('avatar'):
        users.update_user(user['id'], avatar=avatar)


def _prompt_password(login, auth, name):
    dialog = xbmcgui.Dialog()
    while True:
        password = dialog.input(f'Password for {name}', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
        if not password:
            return None
        result = users.authenticate(login, auth, password)
        if result:
            return result
        if not dialog.yesno('KodiSeerr', 'Sign-in failed. Check the password and try again?'):
            return None


def _finish_sign_in(user, cookies, profile):
    remember = xbmcgui.Dialog().yesno(
        'KodiSeerr',
        f"Remember {user['name']} on this device?[CR]You won't be asked for the password after Kodi restarts.",
        nolabel='No',
        yeslabel='Remember me',
    )
    users.activate(user, cookies)
    if remember:
        users.remember(user['id'], cookies)
    _store_profile(user, profile)
    api_client.reset()


def sign_in(user):
    if user.get('session'):
        users.activate(user, user['session'])
        api_client.reset()
        profile = api_client.client.api_request('/auth/me')
        if profile:
            _store_profile(user, profile)
            return True
        users.deactivate()
        api_client.reset()
    result = _prompt_password(user['login'], user['auth'], user['name'])
    if not result:
        return False
    cookies, profile = result
    _finish_sign_in(user, cookies, profile)
    return True


def add_user():
    dialog = xbmcgui.Dialog()
    choice = dialog.select('Account type', [label for _, label in _AUTH_TYPES])
    if choice < 0:
        return False
    auth = _AUTH_TYPES[choice][0]
    login = dialog.input('Email' if auth == 'local' else 'Username', type=xbmcgui.INPUT_ALPHANUM)
    if not login:
        return False
    if users.find_user(login, auth):
        dialog.notification('KodiSeerr', f'{login} has already been added', xbmcgui.NOTIFICATION_WARNING, 3000)
        return False
    result = _prompt_password(login, auth, login)
    if not result:
        return False
    cookies, profile = result
    default_name = (profile or {}).get('displayName') or login
    name = dialog.input('Display name', defaultt=default_name, type=xbmcgui.INPUT_ALPHANUM) or default_name
    user = users.new_user(name, login, auth)
    users.add_user(user)
    _finish_sign_in(user, cookies, profile)
    return True


def ensure_signed_in():
    if users.uses_api_token() or users.active_user():
        return True
    if context.args.get('widget') == '1':
        return False
    user_list = users.load_users()
    if not user_list:
        return add_user()
    choice = xbmcgui.Dialog().select('Who is watching?', [_user_item(u) for u in user_list], useDetails=True)
    return choice >= 0 and sign_in(user_list[choice])


def list_users():
    xbmcplugin.setContent(context.addon_handle, 'files')
    for user in users.load_users():
        item = _user_item(user)
        menu = [('Rename', f"RunPlugin({build_url({'mode': 'rename_user', 'user': user['id']})})")]
        if user.get('session'):
            menu.append(('Forget saved sign-in', f"RunPlugin({build_url({'mode': 'forget_user', 'user': user['id']})})"))
        menu.append(('Remove user', f"RunPlugin({build_url({'mode': 'remove_user', 'user': user['id']})})"))
        item.addContextMenuItems(menu)
        xbmcplugin.addDirectoryItem(context.addon_handle, build_url({'mode': 'select_user', 'user': user['id']}), item, False)
    add_item = xbmcgui.ListItem('Add User')
    add_item.setArt({'icon': 'DefaultAddSource.png', 'thumb': 'DefaultAddSource.png'})
    xbmcplugin.addDirectoryItem(context.addon_handle, build_url({'mode': 'add_user'}), add_item, False)
    xbmcplugin.endOfDirectory(context.addon_handle, cacheToDisc=False)


def select_user(user_id):
    user = users.get_user(user_id)
    if user and sign_in(user):
        _reload()


def add_user_action():
    if add_user():
        _reload()


def rename_user(user_id):
    user = users.get_user(user_id)
    if not user:
        return
    name = xbmcgui.Dialog().input('Display name', defaultt=user['name'], type=xbmcgui.INPUT_ALPHANUM)
    if name and name != user['name']:
        users.update_user(user_id, name=name)
        _reload()


def forget_user(user_id):
    user = users.get_user(user_id)
    if not user:
        return
    users.forget(user_id)
    xbmcgui.Dialog().notification('KodiSeerr', f"Saved sign-in for {user['name']} removed", xbmcgui.NOTIFICATION_INFO, 3000)
    _reload()


def remove_user(user_id):
    user = users.get_user(user_id)
    if not user:
        return
    if not xbmcgui.Dialog().yesno('KodiSeerr', f"Remove {user['name']}?[CR]Their favorites and search history on this device will be deleted."):
        return
    users.remove_user(user_id)
    api_client.reset()
    _reload()


def switch_user():
    user = users.active_user()
    if user and not user.get('session'):
        users.sign_out(user)
    users.deactivate()
    api_client.reset()
    _reload()


def manage_users():
    dialog = xbmcgui.Dialog()
    while True:
        user_list = users.load_users()
        items = [_user_item(u) for u in user_list]
        add_item = xbmcgui.ListItem('Add User')
        add_item.setArt({'icon': 'DefaultAddSource.png', 'thumb': 'DefaultAddSource.png'})
        items.append(add_item)
        choice = dialog.select('Manage Users', items, useDetails=True)
        if choice < 0:
            return
        if choice == len(user_list):
            add_user_action()
            continue
        user = user_list[choice]
        options = [('rename', 'Rename')]
        if user.get('session'):
            options.append(('forget', 'Forget saved sign-in'))
        options.append(('remove', 'Remove user'))
        action = dialog.select(user['name'], [label for _, label in options])
        if action < 0:
            continue
        key = options[action][0]
        if key == 'rename':
            rename_user(user['id'])
        elif key == 'forget':
            forget_user(user['id'])
        else:
            remove_user(user['id'])
