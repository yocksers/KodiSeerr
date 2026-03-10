import sys
import xbmcgui
import xbmcplugin
import context
import cache
import browse
import requests_view
import actions
import api_client

context.init(sys.argv)

mode = context.args.get('mode')
page = context.args.get('page', 1)
try:
    page = int(page)
except (ValueError, TypeError):
    page = 1


def _fetch_list(cache_key, endpoint, params):
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request(endpoint, params=params)
        if data:
            cache.set_cached(cache_key, data)
    return data


if not mode:
    browse.list_main_menu()
elif mode == "test_connection":
    actions.test_connection()
elif mode == "clear_cache":
    actions.clear_cache()
elif mode == "statistics":
    requests_view.show_statistics()
elif mode == "favorites":
    actions.list_favorites()
elif mode == "add_favorite":
    actions.add_to_favorites(context.args.get('type'), context.args.get('id'))
elif mode == "remove_favorite":
    actions.remove_from_favorites(context.args.get('type'), context.args.get('id'))
elif mode == "show_details":
    actions.show_details(context.args.get('type'), context.args.get('id'))
elif mode == "report_issue":
    actions.report_issue(context.args.get('type'), context.args.get('id'))
elif mode == "cancel_request":
    requests_view.cancel_request(context.args.get('request_id'))
elif mode == "jump_to_page":
    browse.jump_to_page()
elif mode == "collections":
    browse.list_collections()
elif mode == "collection_details":
    browse.show_collection_details(context.args.get('collection_id'))
elif mode == "recently_added":
    browse.list_recently_added()
elif mode == "search":
    browse.search()
elif mode == "request":
    requests_view.do_request(context.args.get('type'), context.args.get('id'))
elif mode == "requests":
    take = 20
    skip = (page - 1) * take
    data = api_client.client.api_request("/request", params={"take": take, "skip": skip, "sort": "added", "filter": "all"})
    if data:
        requests_view.show_requests(data, mode, page)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch requests", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
elif mode == "tvshow" and context.args.get("id"):
    browse.list_seasons(context.args.get("id"))
elif mode == "season" and context.args.get("tv_id") and context.args.get("season"):
    browse.list_episodes(context.args.get("tv_id"), int(context.args.get("season")))
elif mode == "genres" and context.args.get("media_type"):
    browse.list_genres(context.args.get("media_type"))
elif mode == "genre" and context.args.get("display_type") and context.args.get("genre_id"):
    display_type = context.args.get("display_type")
    genre_id = context.args.get("genre_id")
    data = _fetch_list(
        f"genre_{display_type}_{genre_id}_{page}",
        f"/discover/{display_type}/genre/{genre_id}",
        {"page": page},
    )
    if data:
        browse.list_items(data, mode, display_type, genre_id)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch genre items", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
elif mode == "trending":
    data = _fetch_list(f"trending_{page}", "/discover/trending", {"page": page})
    if data:
        browse.list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch trending", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
elif mode == "popular_movies":
    data = _fetch_list(f"popular_movies_{page}", "/discover/movies", {"sortBy": "popularity.desc", "page": page})
    if data:
        browse.list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch popular movies", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
elif mode == "popular_tv":
    data = _fetch_list(f"popular_tv_{page}", "/discover/tv", {"sortBy": "popularity.desc", "page": page})
    if data:
        browse.list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch popular TV shows", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
elif mode == "upcoming_movies":
    data = _fetch_list(f"upcoming_movies_{page}", "/discover/movies/upcoming", {"page": page})
    if data:
        browse.list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch upcoming movies", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
elif mode == "upcoming_tv":
    data = _fetch_list(f"upcoming_tv_{page}", "/discover/tv/upcoming", {"page": page})
    if data:
        browse.list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch upcoming TV shows", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
