import xbmc
import xbmcgui
import xbmcplugin
import json
import api_client
import context


def play_local_file(media_type, media_id):
    try:
        data = api_client.client.api_request(f"/{media_type}/{media_id}")
        external_ids = data.get("externalIds", {}) if data else {}
    except Exception:
        external_ids = {}

    tmdb_id = str(media_id)
    imdb_id = str(external_ids.get("imdbId") or "")
    tvdb_id = str(external_ids.get("tvdbId") or "")

    path = _get_local_movie(tmdb_id, imdb_id, tvdb_id)
    if not path:
        xbmcgui.Dialog().notification('KodiSeerr', 'File not found in local library', xbmcgui.NOTIFICATION_ERROR, 4000)
        xbmcplugin.setResolvedUrl(context.addon_handle, False, xbmcgui.ListItem())
        return

    play_item = xbmcgui.ListItem()
    play_item.setPath(path)
    play_item.setProperty('IsPlayable', 'true')
    xbmcplugin.setResolvedUrl(context.addon_handle, True, listitem=play_item)


def _get_local_movie(tmdb_id, imdb_id, tvdb_id):
    query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetMovies",
        "params": {
            "properties": ["uniqueid", "file"]
        },
        "id": 1
    }
    response = xbmc.executeJSONRPC(json.dumps(query))
    data = json.loads(response)
    movies = data.get("result", {}).get("movies", [])
    for m in movies:
        uids = m.get("uniqueid", {})
        if (str(uids.get("tmdb", "")) == tmdb_id or
                (imdb_id and str(uids.get("imdb", "")) == imdb_id) or
                (tvdb_id and str(uids.get("tvdb", "")) == tvdb_id)):
            return m.get("file")
    return None
