import xbmc
import xbmcgui
import xbmcplugin
import concurrent.futures
import api_client
import cache
import context
import media_utils
import storage
from utils import build_url


def test_connection():
    try:
        api_client.client.logged_in = False
        if api_client.client.login():
            xbmcgui.Dialog().notification('KodiSeerr', 'Connection successful!', xbmcgui.NOTIFICATION_INFO, 3000)
        else:
            xbmcgui.Dialog().notification('KodiSeerr', 'Connection failed. Check settings.', xbmcgui.NOTIFICATION_ERROR, 5000)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Test connection error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('KodiSeerr', f'Error: {str(e)}', xbmcgui.NOTIFICATION_ERROR, 5000)
    xbmc.executebuiltin("Action(Back)")


def clear_cache():
    cache.clear()
    xbmcgui.Dialog().notification('KodiSeerr', 'Cache cleared successfully', xbmcgui.NOTIFICATION_INFO, 3000)


def show_details(media_type, media_id):
    cache_key = f"details_{media_type}_{media_id}"
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request(f"/{media_type}/{media_id}")
        if data:
            cache.set_cached(cache_key, data)
    if not data:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch details", xbmcgui.NOTIFICATION_ERROR)
        return
    title = data.get('title') or data.get('name', 'Unknown')
    overview = data.get('overview', 'No description available')
    release_date = data.get('releaseDate') or data.get('firstAirDate', 'Unknown')
    rating = data.get('voteAverage', 0)
    genres = ', '.join([g['name'] for g in data.get('genres', [])])
    details = f"[B]{title}[/B]\n\nRelease Date: {release_date}\nRating: {rating}/10\n"
    if genres:
        details += f"Genres: {genres}\n"
    details += f"\n{overview}\n\n"
    if data.get('cast'):
        details += f"\n[B]Cast:[/B]\n{', '.join(c['name'] for c in data['cast'][:10])}\n"
    if data.get('recommendations'):
        details += "\n[B]Recommended:[/B]\n"
        for rec in data['recommendations'][:5]:
            details += f"• {rec.get('title') or rec.get('name')}\n"
    xbmcgui.Dialog().textviewer(title, details)


def add_to_favorites(media_type, media_id):
    favorites = storage.load_favorites()
    fav_key = f"{media_type}_{media_id}"
    if fav_key in favorites:
        xbmcgui.Dialog().notification('KodiSeerr', 'Already in favorites', xbmcgui.NOTIFICATION_INFO)
    else:
        cache_key = f"details_{media_type}_{media_id}"
        data = cache.get_cached(cache_key)
        if not data:
            data = api_client.client.api_request(f"/{media_type}/{media_id}")
            if data:
                cache.set_cached(cache_key, data)
        meta = {}
        if data:
            release = data.get('releaseDate') or data.get('firstAirDate') or ''
            meta = {
                'title': data.get('title') or data.get('name', ''),
                'poster': data.get('posterPath', ''),
                'year': release[:4],
                'mediatype': media_type,
            }
        favorites[fav_key] = meta
        storage.save_favorites(favorites)
        xbmcgui.Dialog().notification('KodiSeerr', 'Added to favorites', xbmcgui.NOTIFICATION_INFO)


def remove_from_favorites(media_type, media_id):
    favorites = storage.load_favorites()
    fav_key = f"{media_type}_{media_id}"
    if fav_key in favorites:
        del favorites[fav_key]
        storage.save_favorites(favorites)
        xbmcgui.Dialog().notification('KodiSeerr', 'Removed from favorites', xbmcgui.NOTIFICATION_INFO)
        xbmc.executebuiltin('Container.Refresh')


def list_favorites():
    xbmcplugin.setContent(context.addon_handle, 'videos')
    favorites = storage.load_favorites()
    if not favorites:
        info_item = xbmcgui.ListItem(label='[I]No favorites yet[/I]')
        xbmcplugin.addDirectoryItem(context.addon_handle, '', info_item, False)
    else:
        for fav_key, meta in favorites.items():
            parts = fav_key.split('_', 1)
            if len(parts) < 2:
                continue
            media_type, media_id = parts
            label = meta.get('title', '')
            year = meta.get('year', '')
            art_data = None
            if not label:
                cache_key = f"details_{media_type}_{media_id}"
                data = cache.get_cached(cache_key)
                if not data:
                    data = api_client.client.api_request(f"/{media_type}/{media_id}")
                    if data:
                        cache.set_cached(cache_key, data)
                if not data:
                    continue
                label = data.get('title') or data.get('name', 'Unknown')
                release = data.get('releaseDate') or data.get('firstAirDate') or ''
                year = release[:4]
                art_data = data
            if year:
                label = f"{label} ({year})"
            ctx_menu = [
                ('Remove from Favorites', f'RunPlugin({build_url({"mode": "remove_favorite", "type": media_type, "id": media_id})})'),
                ('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": media_id})})'),
            ]
            url = build_url({'mode': 'request', 'type': media_type, 'id': media_id})
            list_item = xbmcgui.ListItem(label=label)
            list_item.addContextMenuItems(ctx_menu)
            if art_data:
                media_utils.set_info_tag(list_item, media_utils.make_info(art_data, media_type))
                list_item.setArt(media_utils.make_art(art_data))
            elif meta.get('poster'):
                list_item.setArt({
                    'poster': context.image_base + meta['poster'],
                    'thumb': context.image_base + meta['poster'],
                })
            xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(context.addon_handle)


def show_profile():
    user = api_client.client.api_request('/auth/me')
    if not user:
        xbmcgui.Dialog().notification('KodiSeerr', 'Could not load profile', xbmcgui.NOTIFICATION_ERROR)
        return

    xbmcplugin.setContent(context.addon_handle, 'files')

    display_name = user.get('displayName') or user.get('username') or user.get('email', 'Unknown')
    email = user.get('email', '')
    header_label = f"[B]{display_name}[/B]"
    if email and email != display_name:
        header_label += f"  ({email})"
    header_item = xbmcgui.ListItem(label=header_label)
    header_item.setArt({'icon': 'DefaultActor.png'})
    xbmcplugin.addDirectoryItem(context.addon_handle, '', header_item, False)

    total_requests = user.get('requestCount', 0)
    total_item = xbmcgui.ListItem(label=f'Total Requests:  {total_requests}')
    total_item.setArt({'icon': 'DefaultAddonInfoProvider.png'})
    xbmcplugin.addDirectoryItem(context.addon_handle, '', total_item, False)

    def _quota_label(quota):
        if not quota:
            return 'Unlimited'
        limit = quota.get('limit', 0)
        used = quota.get('used', 0)
        remaining = quota.get('remaining', limit)
        if not limit:
            return 'Unlimited'
        return f'{used} used / {limit} limit  ({remaining} remaining)'

    movie_quota = user.get('movieQuota')
    movie_item = xbmcgui.ListItem(label=f'Movie Requests:  {_quota_label(movie_quota)}')
    movie_item.setArt({'icon': 'DefaultMovies.png'})
    xbmcplugin.addDirectoryItem(context.addon_handle, '', movie_item, False)

    tv_quota = user.get('tvQuota')
    tv_item = xbmcgui.ListItem(label=f'Series Requests:  {_quota_label(tv_quota)}')
    tv_item.setArt({'icon': 'DefaultTVShows.png'})
    xbmcplugin.addDirectoryItem(context.addon_handle, '', tv_item, False)

    separator = xbmcgui.ListItem(label='[I]Recent Requests[/I]')
    separator.setArt({'icon': 'DefaultAddonNone.png'})
    xbmcplugin.addDirectoryItem(context.addon_handle, '', separator, False)

    user_id = user.get('id')
    if user_id:
        recent_data = api_client.client.api_request(
            '/request',
            params={'take': 10, 'skip': 0, 'sort': 'added', 'filter': 'all', 'requestedBy': user_id}
        )
    else:
        recent_data = api_client.client.api_request(
            '/request',
            params={'take': 10, 'skip': 0, 'sort': 'added', 'filter': 'all'}
        )

    if recent_data:
        _STATUS_LABELS = {2: '[COLOR yellow]Requested[/COLOR]', 3: '[COLOR cyan]Processing[/COLOR]',
                          4: '[COLOR lime]Partially Available[/COLOR]', 5: '[COLOR lime]Available[/COLOR]'}
        for req in recent_data.get('results', []):
            media = req.get('media', {})
            media_id = media.get('tmdbId')
            media_type = media.get('mediaType')
            media_status = media.get('status', 1)
            if not media_id or not media_type:
                continue
            cache_key = f"details_{media_type}_{media_id}"
            media_data = cache.get_cached(cache_key)
            if not media_data:
                media_data = api_client.client.api_request(f"/{media_type}/{media_id}")
                if media_data:
                    cache.set_cached(cache_key, media_data)
            if not media_data:
                continue
            title = media_data.get('title') or media_data.get('name') or 'Unknown'
            release = media_data.get('releaseDate') or media_data.get('firstAirDate', '')
            year = release[:4] if release else ''
            status_str = _STATUS_LABELS.get(media_status, '')
            label = f'{title}'
            if year:
                label += f' ({year})'
            if status_str:
                label += f'  {status_str}'
            list_item = xbmcgui.ListItem(label=label)
            list_item.setArt(media_utils.make_art(media_data))
            media_utils.set_info_tag(list_item, media_utils.make_info(media_data, media_type))
            if media_status == 5 and media_type == 'movie':
                url = build_url({'mode': 'play_local_file', 'type': media_type, 'id': media_id})
                list_item.setProperty('IsPlayable', 'true')
            elif media_status == 5 and media_type == 'tv':
                url = build_url({'mode': 'tvshow', 'id': media_id})
            else:
                url = build_url({'mode': 'show_details', 'type': media_type, 'id': media_id})
            xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, media_status == 5 and media_type == 'tv')

    xbmcplugin.endOfDirectory(context.addon_handle)


def show_person_credits(person_id):
    xbmcplugin.setContent(context.addon_handle, 'videos')
    cache_key = f"person_credits_{person_id}"
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request(f"/person/{person_id}/combined_credits")
        if data:
            cache.set_cached(cache_key, data)
    if not data:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch person credits", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
        return
    seen_ids = set()
    items = []
    for item in data.get('cast', []):
        media_type = item.get('mediaType')
        item_id = item.get('id')
        if media_type not in ('movie', 'tv') or not item_id or item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        items.append(item)
    for item in items:
        media_type = item.get('mediaType')
        title = item.get('title') or item.get('name')
        release_date = item.get('releaseDate') or item.get('firstAirDate')
        year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
        label = f"{title} ({year})" if year else title
        item_id = item.get('id')
        ctx_menu = [
            ('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": item_id})})'),
            ('Add to Favorites', f'RunPlugin({build_url({"mode": "add_favorite", "type": media_type, "id": item_id})})'),
        ]
        url = build_url({'mode': 'request', 'type': media_type, 'id': item_id})
        list_item = xbmcgui.ListItem(label=label)
        list_item.addContextMenuItems(ctx_menu)
        media_utils.set_info_tag(list_item, media_utils.make_info(item, media_type))
        list_item.setArt(media_utils.make_art(item))
        xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, False)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(context.addon_handle)


def report_issue(media_type, media_id):
    issue_types = ['Video Issue', 'Audio Issue', 'Subtitles Issue', 'Other']
    selected = xbmcgui.Dialog().select('Select Issue Type', issue_types)
    if selected < 0:
        return
    message = xbmcgui.Dialog().input('Describe the issue (optional)')
    try:
        api_client.client.api_request(
            f"/{media_type}/{media_id}/issue",
            method="POST",
            data={"issueType": selected + 1, "message": message or ""},
        )
        xbmcgui.Dialog().notification('KodiSeerr', 'Issue reported', xbmcgui.NOTIFICATION_INFO)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Issue report error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('KodiSeerr', 'Failed to report issue', xbmcgui.NOTIFICATION_ERROR)
