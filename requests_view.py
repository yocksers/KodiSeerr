import xbmc
import xbmcplugin
import xbmcgui
import api_client
import cache
import context
import media_utils
import storage
from utils import build_url


_PERM_ADMIN = 2
_PERM_MANAGE_REQUESTS = 8


def has_manage_requests_permission():
    try:
        user = api_client.client.api_request('/auth/me')
        if not user:
            return False
        perms = user.get('permissions', 0)
        return bool(perms & _PERM_ADMIN) or bool(perms & _PERM_MANAGE_REQUESTS)
    except Exception:
        return False


def _format_free_space(bytes_val):
    if not bytes_val:
        return ''
    tb = bytes_val / (1024 ** 4)
    if tb >= 1:
        return f'{tb:.2f} TB'
    return f'{bytes_val / (1024 ** 3):.2f} GB'


def get_server_options(media_type, is4k=False):
    service = 'radarr' if media_type == 'movie' else 'sonarr'
    try:
        servers = api_client.client.api_request(f'/settings/{service}')
        if not servers or not isinstance(servers, list):
            return None
        server = None
        for s in servers:
            if s.get('is4k', False) == is4k and s.get('isDefault', False):
                server = s
                break
        if not server:
            for s in servers:
                if s.get('is4k', False) == is4k:
                    server = s
                    break
        if not server:
            server = servers[0]
        server_id = server.get('id')
        default_profile_id = server.get('activeProfileId')
        default_root_folder = server.get('activeDirectory', '')
        profiles = api_client.client.api_request(f'/settings/{service}/{server_id}/profiles') or []
        root_folders = api_client.client.api_request(f'/settings/{service}/{server_id}/rootfolders') or []
        tags = api_client.client.api_request(f'/settings/{service}/{server_id}/tags') or []
        return {
            'server_id': server_id,
            'default_profile_id': default_profile_id,
            'default_root_folder': default_root_folder,
            'profiles': profiles,
            'root_folders': root_folders,
            'tags': tags,
        }
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Failed to get server options: {e}", xbmc.LOGERROR)
        return None


def prompt_advanced_options(media_type, is4k=False):
    opts = get_server_options(media_type, is4k)
    if not opts:
        return {}
    result = {'server_id': opts['server_id']}
    profiles = opts.get('profiles', [])
    if profiles:
        default_id = opts.get('default_profile_id')
        names = []
        default_idx = 0
        for i, p in enumerate(profiles):
            name = p.get('name', str(p.get('id', i)))
            if p.get('id') == default_id:
                name += ' (Default)'
                default_idx = i
            names.append(name)
        sel = xbmcgui.Dialog().select('Quality Profile', names, preselect=default_idx)
        if sel < 0:
            return None
        result['profile_id'] = profiles[sel].get('id')
    root_folders = opts.get('root_folders', [])
    if root_folders:
        default_folder = opts.get('default_root_folder', '')
        names = []
        default_idx = 0
        for i, f in enumerate(root_folders):
            path = f.get('path', '')
            free = _format_free_space(f.get('freeSpace'))
            name = f'{path} ({free})' if free else path
            if path == default_folder:
                name += ' (Default)'
                default_idx = i
            names.append(name)
        sel = xbmcgui.Dialog().select('Root Folder', names, preselect=default_idx)
        if sel < 0:
            return None
        result['root_folder'] = root_folders[sel].get('path', '')
    tags = opts.get('tags', [])
    if tags:
        tag_labels = [t.get('label', str(t.get('id', ''))) for t in tags]
        selected_tags = xbmcgui.Dialog().multiselect('Tags', tag_labels)
        if selected_tags is None:
            return None
        if selected_tags:
            result['tags'] = [tags[i].get('id') for i in selected_tags]
    return result


def get_quality_profiles():
    try:
        data = api_client.client.api_request('/settings/radarr')
        if data and isinstance(data, list) and len(data) > 0:
            profiles = data[0].get('profiles', [])
            return [(p['id'], p['name']) for p in profiles]
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Quality profiles error: {e}", xbmc.LOGERROR)
    return []


def do_request(media_type, media_id):
    status = media_utils.get_media_status(media_type, media_id)
    if status >= 5:
        if not xbmcgui.Dialog().yesno('KodiSeerr', 'This content is already available. Request anyway?'):
            return
    elif status in [2, 3, 4]:
        if not xbmcgui.Dialog().yesno('KodiSeerr', 'This content is already requested. Request again?'):
            return

    seasons_to_request = []
    if media_type == "tv":
        tv_cache_key = f"details_tv_{media_id}"
        tv_data = cache.get_cached(tv_cache_key)
        if not tv_data:
            tv_data = api_client.client.api_request(f"/tv/{media_id}")
            if tv_data:
                cache.set_cached(tv_cache_key, tv_data)
        current_season = context.args.get("season")
        seasons = tv_data.get('seasons', []) if tv_data else []
        season_options = ["Request all seasons"]
        if current_season:
            season_options.insert(0, f"Request Season {current_season}")
        for s in seasons:
            snum = s.get('seasonNumber')
            if snum is not None and str(snum) != str(current_season):
                season_options.append(f"Season {snum}")
        selected_idx = xbmcgui.Dialog().select("Seerr Request", season_options)
        if selected_idx < 0:
            return
        chosen = season_options[selected_idx]
        if chosen == "Request all seasons":
            seasons_to_request = "all"
        elif chosen.startswith("Request Season "):
            seasons_to_request = [int(current_season)]
        else:
            seasons_to_request = [int(chosen.replace("Season ", ""))]

    is4k = False
    quality_profile = None

    if context.enable_ask_4k:
        prefs = storage.load_preferences()
        if context.addon.getSettingBool('remember_last_quality') and 'last_4k_choice' in prefs:
            is4k = prefs['last_4k_choice']
        else:
            is4k = xbmcgui.Dialog().yesno('KodiSeerr', 'Request in 4K quality?')
        if context.addon.getSettingBool('remember_last_quality'):
            prefs['last_4k_choice'] = is4k
            storage.save_preferences(prefs)

    server_id = None
    root_folder = None
    tags = None

    if has_manage_requests_permission():
        advanced = prompt_advanced_options(media_type, is4k)
        if advanced is None:
            return
        server_id = advanced.get('server_id')
        quality_profile = advanced.get('profile_id')
        root_folder = advanced.get('root_folder')
        tags = advanced.get('tags')
    elif context.addon.getSettingBool('show_quality_profiles'):
        profiles = get_quality_profiles()
        if profiles:
            profile_names = [p[1] for p in profiles]
            selected = xbmcgui.Dialog().select('Select Quality Profile', profile_names)
            if selected >= 0:
                quality_profile = profiles[selected][0]

    if context.addon.getSettingBool('confirm_before_request'):
        title_data_key = f"details_{media_type}_{media_id}"
        title_data = cache.get_cached(title_data_key)
        if not title_data:
            title_data = api_client.client.api_request(f"/{media_type}/{media_id}")
            if title_data:
                cache.set_cached(title_data_key, title_data)
        title = title_data.get('title') or title_data.get('name', 'this content') if title_data else 'this content'
        msg = f"Request {title}" + (" in 4K" if is4k else "") + "?"
        if not xbmcgui.Dialog().yesno('KodiSeerr', msg):
            return

    payload = {"mediaType": media_type, "mediaId": int(media_id), "is4k": is4k}
    if media_type == "tv":
        payload["seasons"] = seasons_to_request
    if server_id is not None:
        payload["serverId"] = server_id
    if quality_profile:
        payload["profileId"] = quality_profile
    if root_folder:
        payload["rootFolder"] = root_folder
    if tags:
        payload["tags"] = tags

    try:
        api_client.client.api_request("/request", method="POST", data=payload)
        xbmcgui.Dialog().notification('KodiSeerr', 'Request Sent!', xbmcgui.NOTIFICATION_INFO, 3000)
        cache.remove(f"status_{media_type}_{media_id}")
    except Exception as e:
        xbmcgui.Dialog().notification('KodiSeerr', f'Request Failed: {str(e)}', xbmcgui.NOTIFICATION_ERROR, 4000)
    xbmc.executebuiltin("Action(Back)")


def cancel_request(request_id):
    if xbmcgui.Dialog().yesno('KodiSeerr', 'Cancel this request?'):
        try:
            api_client.client.api_request(f"/request/{request_id}", method="DELETE")
            xbmcgui.Dialog().notification('KodiSeerr', 'Request cancelled', xbmcgui.NOTIFICATION_INFO)
            xbmc.executebuiltin('Container.Refresh')
        except Exception as e:
            xbmcgui.Dialog().notification('KodiSeerr', f'Failed to cancel: {str(e)}', xbmcgui.NOTIFICATION_ERROR)


def show_requests(data, mode, current_page):
    xbmcplugin.setContent(context.addon_handle, 'videos')
    items = data.get('results', [])
    page_info = data.get('pageInfo', {})
    total_pages = page_info.get('pages', 1)

    page_info_item = xbmcgui.ListItem(label=f'[I]Page {current_page} of {total_pages}[/I]')
    page_info_item.setArt({'icon': 'DefaultAddonNone.png'})
    xbmcplugin.addDirectoryItem(context.addon_handle, '', page_info_item, False)

    jump_item = xbmcgui.ListItem(label='[B]Jump to Page...[/B]')
    jump_item.setArt({'icon': 'DefaultAddonNone.png'})
    xbmcplugin.addDirectoryItem(context.addon_handle, build_url({'mode': 'jump_to_page', 'original_mode': mode}), jump_item, True)

    if current_page > 1:
        prev_item = xbmcgui.ListItem(label=f'[B]<< Previous Page ({current_page - 1})[/B]')
        prev_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        xbmcplugin.addDirectoryItem(context.addon_handle, build_url({'mode': mode, 'page': current_page - 1}), prev_item, True)

    for item in items:
        media = item.get('media', {})
        media_id = media.get('tmdbId')
        media_type = media.get('mediaType')
        request_id = item.get('id')
        cache_key = f"details_{media_type}_{media_id}"
        media_data = cache.get_cached(cache_key)
        if not media_data:
            media_data = api_client.client.api_request(f"/{media_type}/{media_id}", params={})
            if media_data:
                cache.set_cached(cache_key, media_data)
        if not media_data:
            continue
        label_text = media_data.get('title') or media_data.get('name') or "Untitled"
        media_status = media.get('status')
        if media_status == 2:
            label_text += " [COLOR yellow](Pending)[/COLOR]"
        elif media_status == 3:
            label_text += " [COLOR cyan](Processing)[/COLOR]"
        elif media_status == 4:
            label_text += " [COLOR lime](Partially Available)[/COLOR]"
        elif media_status == 5:
            label_text += " [COLOR lime](Available)[/COLOR]"
        ctx_menu = []
        if media_status in [2, 3]:
            ctx_menu.append(('Cancel Request', f'RunPlugin({build_url({"mode": "cancel_request", "request_id": request_id})})'))
        ctx_menu.append(('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": media_id})})'))
        if media_status == 5 and media_type == "movie":
            url = build_url({'mode': 'play_local_file', 'type': media_type, 'id': media_id})
            is_folder = False
        elif media_status == 5 and media_type == "tv":
            url = build_url({'mode': 'tvshow', 'id': media_id})
            is_folder = True
        else:
            url = build_url({'mode': 'request', 'type': media_type, 'id': media_id})
            is_folder = False
        list_item = xbmcgui.ListItem(label=label_text)
        if media_status == 5 and media_type == "movie":
            list_item.setProperty('IsPlayable', 'true')
        list_item.addContextMenuItems(ctx_menu)
        media_utils.set_info_tag(list_item, {'title': label_text, 'plot': f"Media ID: {media_id}, Type: {media_type}"})
        list_item.setArt(media_utils.make_art(media_data))
        xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, is_folder)

    if current_page < total_pages:
        next_item = xbmcgui.ListItem(label=f'[B]Next Page ({current_page + 1}) >>[/B]')
        next_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        xbmcplugin.addDirectoryItem(context.addon_handle, build_url({'mode': mode, 'page': current_page + 1}), next_item, True)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(context.addon_handle)


def show_statistics():
    try:
        requests_data = api_client.client.api_request('/request', params={'take': 1000})
        if not requests_data:
            xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch statistics", xbmcgui.NOTIFICATION_ERROR)
            return
        items = requests_data.get('results', [])
        total = len(items)
        movies = sum(1 for i in items if i.get('media', {}).get('mediaType') == 'movie')
        tv = total - movies
        status_counts = {}
        for item in items:
            s = item.get('media', {}).get('status', 0)
            status_counts[s] = status_counts.get(s, 0) + 1
        stats = (
            f"[B]Your Request Statistics[/B]\n\n"
            f"Total Requests: {total}\n"
            f"Movies: {movies}\n"
            f"TV Shows: {tv}\n\n"
            f"[COLOR yellow]Pending:[/COLOR] {status_counts.get(2, 0)}\n"
            f"[COLOR cyan]Processing:[/COLOR] {status_counts.get(3, 0)}\n"
            f"[COLOR lime]Available:[/COLOR] {status_counts.get(5, 0)}\n"
        )
        xbmcgui.Dialog().textviewer("Statistics", stats)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Statistics error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch statistics", xbmcgui.NOTIFICATION_ERROR)
    xbmc.executebuiltin("Action(Back)")
