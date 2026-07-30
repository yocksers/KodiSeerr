import json
import xbmc
import xbmcgui
import xbmcaddon

_MEDIA_ADDONS = [
    ('plugin.video.jellycon',        'Jellycon'),
    ('plugin.video.emby',            'Emby for Kodi'),
    ('plugin.video.plexkodiconnect', 'Plex for Kodi'),
]
_addon_check_cache = {}


def _addon_installed(addon_id):
    if addon_id not in _addon_check_cache:
        try:
            xbmcaddon.Addon(addon_id)
            _addon_check_cache[addon_id] = True
        except Exception:
            _addon_check_cache[addon_id] = False
    return _addon_check_cache[addon_id]


def get_installed_media_addons():
    return [(aid, name) for aid, name in _MEDIA_ADDONS if _addon_installed(aid)]


def _find_movie(tmdb_id, imdb_id=''):
    resp = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovies',
        'params': {'properties': ['uniqueid']}, 'id': 1,
    })))
    for m in resp.get('result', {}).get('movies', []):
        u = m.get('uniqueid', {})
        if (str(u.get('tmdb', '')) == str(tmdb_id)
                or (imdb_id and str(u.get('imdb', '')) == str(imdb_id))):
            return m.get('movieid')
    return None


def _find_tvshow(tmdb_id, imdb_id='', tvdb_id=''):
    resp = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'method': 'VideoLibrary.GetTVShows',
        'params': {'properties': ['uniqueid']}, 'id': 1,
    })))
    for s in resp.get('result', {}).get('tvshows', []):
        u = s.get('uniqueid', {})
        if (str(u.get('tmdb', '')) == str(tmdb_id)
                or (tvdb_id and str(u.get('tvdb', '')) == str(tvdb_id))
                or (imdb_id and str(u.get('imdb', '')) == str(imdb_id))):
            return s.get('tvshowid')
    return None


def jump_to_library(media_type, media_id):
    import api_client
    import cache
    cache_key = f"details_{media_type}_{media_id}"
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request(f"/{media_type}/{media_id}")
        if data:
            cache.set_cached(cache_key, data)
    ext = (data or {}).get('externalIds', {})
    tmdb_id = str(media_id)
    imdb_id = str(ext.get('imdbId') or '')
    tvdb_id = str(ext.get('tvdbId') or '')
    if media_type == 'movie':
        db_id = _find_movie(tmdb_id, imdb_id)
        if db_id:
            xbmc.executebuiltin(
                f'ActivateWindow(VideoLibrary,videodb://movies/titles/{db_id}/,return)'
            )
        else:
            xbmcgui.Dialog().notification(
                'KodiSeerr', 'Not found in local library',
                xbmcgui.NOTIFICATION_WARNING, 3000
            )
    else:
        db_id = _find_tvshow(tmdb_id, imdb_id, tvdb_id)
        if db_id:
            xbmc.executebuiltin(
                f'ActivateWindow(VideoLibrary,videodb://tvshows/titles/{db_id}/,return)'
            )
        else:
            xbmcgui.Dialog().notification(
                'KodiSeerr', 'Not found in local library',
                xbmcgui.NOTIFICATION_WARNING, 3000
            )


def get_library_context_items(media_type, media_id, status):
    from utils import build_url
    if status not in (4, 5):
        return []
    items = [(
        'View in Local Library',
        f'RunPlugin({build_url({"mode": "jump_to_library", "type": media_type, "id": media_id})})'
    )]
    for addon_id, addon_name in get_installed_media_addons():
        items.append((
            f'Browse in {addon_name}',
            f'ActivateWindow(Videos,plugin://{addon_id}/,return)'
        ))
    return items
