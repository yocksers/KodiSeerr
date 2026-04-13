import xbmc
import xbmcgui
import xbmcplugin
import json
import api_client
import context


def play_local_file(media_type, media_id, season=None, episode=None):
    try:
        data = api_client.client.api_request(f"/{media_type}/{media_id}")
        external_ids = data.get("externalIds", {}) if data else {}
    except Exception:
        external_ids = {}

    tmdb_id = str(media_id)
    imdb_id = str(external_ids.get("imdbId") or "")
    tvdb_id = str(external_ids.get("tvdbId") or "")

    if media_type == "tv" and season is not None and episode is not None:
        path = _get_local_episode(tvdb_id, tmdb_id, imdb_id, season, episode)
    else:
        path = _get_local_movie(tmdb_id, imdb_id, tvdb_id)

    if not path:
        xbmcgui.Dialog().notification('KodiSeerr', 'File not found in local library', xbmcgui.NOTIFICATION_ERROR, 4000)
        xbmcplugin.setResolvedUrl(context.addon_handle, False, xbmcgui.ListItem())
        return

    play_item = xbmcgui.ListItem()
    play_item.setPath(path)
    play_item.setProperty('IsPlayable', 'true')
    xbmcplugin.setResolvedUrl(context.addon_handle, True, listitem=play_item)


def _get_local_episode(tvdb_id, tmdb_id, imdb_id, season, episode):
    show_query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetTVShows",
        "params": {"properties": ["uniqueid"]},
        "id": 1
    }
    response = xbmc.executeJSONRPC(json.dumps(show_query))
    data = json.loads(response)
    shows = data.get("result", {}).get("tvshows", [])
    show = None
    for s in shows:
        uids = s.get("uniqueid", {})
        if (str(uids.get("tvdb", "")) == str(tvdb_id) or
                str(uids.get("tmdb", "")) == str(tmdb_id) or
                (imdb_id and str(uids.get("imdb", "")) == str(imdb_id))):
            show = s
            break
    if show is None:
        xbmc.log(f"[KodiSeerr] Show not found in local library (tmdb={tmdb_id}, tvdb={tvdb_id})", xbmc.LOGWARNING)
        return None
    show_id = show.get("tvshowid")
    episode_query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetEpisodes",
        "params": {
            "tvshowid": show_id,
            "season": int(season),
            "properties": ["file"],
            "filter": {"field": "episode", "operator": "is", "value": str(episode)}
        },
        "id": 2
    }
    response = xbmc.executeJSONRPC(json.dumps(episode_query))
    data = json.loads(response)
    episodes = data.get("result", {}).get("episodes", [])
    if episodes:
        return episodes[0].get("file")
    return None


def _get_local_movie(tmdb_id, imdb_id, tvdb_id):
    query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetMovies",
        "params": {
            "properties": ["uniqueid", "file"]
        },
        "id": 3
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
