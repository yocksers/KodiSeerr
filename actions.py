import xbmc
import xbmcgui
import xbmcplugin
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
        favorites.add(fav_key)
        storage.save_favorites(favorites)
        xbmcgui.Dialog().notification('KodiSeerr', 'Added to favorites', xbmcgui.NOTIFICATION_INFO)


def remove_from_favorites(media_type, media_id):
    favorites = storage.load_favorites()
    fav_key = f"{media_type}_{media_id}"
    if fav_key in favorites:
        favorites.remove(fav_key)
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
        for fav in favorites:
            parts = fav.split('_', 1)
            if len(parts) < 2:
                continue
            media_type, media_id = parts
            cache_key = f"details_{media_type}_{media_id}"
            data = cache.get_cached(cache_key)
            if not data:
                data = api_client.client.api_request(f"/{media_type}/{media_id}")
                if data:
                    cache.set_cached(cache_key, data)
            if not data:
                continue
            label = data.get('title') or data.get('name', 'Unknown')
            ctx_menu = [
                ('Remove from Favorites', f'RunPlugin({build_url({"mode": "remove_favorite", "type": media_type, "id": media_id})})'),
                ('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": media_id})})'),
            ]
            url = build_url({'mode': 'request', 'type': media_type, 'id': media_id})
            list_item = xbmcgui.ListItem(label=label)
            list_item.addContextMenuItems(ctx_menu)
            media_utils.set_info_tag(list_item, media_utils.make_info(data, media_type))
            list_item.setArt(media_utils.make_art(data))
            xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, False)
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
