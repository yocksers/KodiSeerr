import concurrent.futures
import threading
import xbmc
import xbmcplugin
import xbmcgui
import api_client
import cache
import context
import media_utils
from utils import build_url


def list_main_menu():
    xbmcplugin.setContent(context.addon_handle, 'files')
    items = [
        ('trending', 'Trending', 'DefaultMovies.png', True),
        ('popular_movies', 'Popular Movies', 'DefaultMovies.png', True),
        ('popular_tv', 'Popular TV Shows', 'DefaultTVShows.png', True),
        ('upcoming_movies', 'Upcoming Movies', 'DefaultMovies.png', True),
        ('upcoming_tv', 'Upcoming TV Shows', 'DefaultTVShows.png', True),
        (None, None, None, False),
        ('genres_movie', 'Movies by Genre', 'DefaultGenre.png', True),
        ('genres_tv', 'TV Shows by Genre', 'DefaultGenre.png', True),
        (None, None, None, False),
        ('recently_added', 'Recently Added', 'DefaultRecentlyAddedMovies.png', True),
        ('collections', 'Collections', 'DefaultSets.png', True),
        (None, None, None, False),
        ('favorites', 'My Favorites', 'DefaultFavourites.png', True),
        ('requests', 'Request Progress', 'DefaultInProgressShows.png', True),
        ('statistics', 'Statistics', 'DefaultAddonInfoProvider.png', False),
        (None, None, None, False),
        ('search', 'Search', 'DefaultAddonsSearch.png', True),
        ('test_connection', 'Test Connection', 'DefaultAddonService.png', False),
    ]
    for item in items:
        if item[0] is None:
            continue
        mode, label, icon, is_folder = item
        list_item = xbmcgui.ListItem(label)
        list_item.setArt({'icon': icon, 'thumb': icon})
        if mode == 'genres_movie':
            url = build_url({'mode': 'genres', 'media_type': 'movie'})
        elif mode == 'genres_tv':
            url = build_url({'mode': 'genres', 'media_type': 'tv'})
        else:
            url = build_url({'mode': mode})
        xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(context.addon_handle)


def list_genres(media_type):
    xbmcplugin.setContent(context.addon_handle, 'genres')
    cache_key = f"genres_{media_type}"
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request(f"/genres/{media_type}", params={})
        if data:
            cache.set_cached(cache_key, data)
    if data:
        for item in data:
            name = item.get('name')
            genre_id = item.get('id')
            display_type = "movies" if media_type == "movie" else media_type
            url = build_url({'mode': 'genre', 'display_type': display_type, 'genre_id': genre_id})
            list_item = xbmcgui.ListItem(label=name)
            list_item.setArt({'icon': 'DefaultGenre.png'})
            xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, True)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch genres", xbmcgui.NOTIFICATION_ERROR)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(context.addon_handle)


def list_collections():
    xbmcplugin.setContent(context.addon_handle, 'sets')
    page = context.args.get('page', 1)
    try:
        page = int(page)
    except Exception:
        page = 1
    cache_key = f"collections_{page}"
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request("/discover/movies", params={"page": page, "sortBy": "popularity.desc"})
        if data:
            cache.set_cached(cache_key, data)
    if data:
        collections_seen = set()
        for item in data.get('results', []):
            if item.get('belongsToCollection'):
                coll = item['belongsToCollection']
                coll_id = coll.get('id')
                if coll_id not in collections_seen:
                    collections_seen.add(coll_id)
                    name = coll.get('name', 'Unknown Collection')
                    url = build_url({'mode': 'collection_details', 'collection_id': coll_id})
                    list_item = xbmcgui.ListItem(label=name)
                    if coll.get('posterPath'):
                        list_item.setArt({
                            'poster': context.image_base + coll['posterPath'],
                            'thumb': context.image_base + coll['posterPath'],
                        })
                    xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(context.addon_handle)


def show_collection_details(collection_id):
    xbmcplugin.setContent(context.addon_handle, 'movies')
    cache_key = f"collection_{collection_id}"
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request(f"/collection/{collection_id}")
        if data:
            cache.set_cached(cache_key, data)
    if data:
        parts = data.get('parts', [])
        show_request_status = context.addon.getSettingBool('show_request_status')
        statuses = {}
        if show_request_status and parts:
            api_client.client.login()
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(parts))) as executor:
                future_to_id = {
                    executor.submit(media_utils.get_media_status, 'movie', item.get('id'), item): item.get('id')
                    for item in parts
                }
                for future, key_id in future_to_id.items():
                    statuses[key_id] = future.result()
        for item in parts:
            media_type = 'movie'
            title = item.get('title') or item.get('name')
            release_date = item.get('releaseDate')
            year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
            label = f"{title} ({year})" if year else title
            if show_request_status:
                status = statuses.get(item.get('id'), 0)
                status_label = media_utils.get_status_label(status)
                if status_label:
                    label += f" {status_label}"
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
    xbmcplugin.endOfDirectory(context.addon_handle)


def list_items(data, mode, display_type=None, genre_id=None):
    items = data.get('results', [])
    current_page = data.get('page', 1)
    total_pages = data.get('totalPages', 1)
    is_widget = xbmc.getCondVisibility('Window.IsVisible(home)')
    hide_pagination = context.addon.getSettingBool('hide_pagination_in_widgets')

    if items:
        first_type = items[0].get('mediaType', 'video')
        if first_type == 'movie':
            xbmcplugin.setContent(context.addon_handle, 'movies')
        elif first_type == 'tv':
            xbmcplugin.setContent(context.addon_handle, 'tvshows')
        else:
            xbmcplugin.setContent(context.addon_handle, 'videos')
    else:
        xbmcplugin.setContent(context.addon_handle, 'videos')

    if not (is_widget and hide_pagination):
        page_info = xbmcgui.ListItem(label=f'[I]Page {current_page} of {total_pages}[/I]')
        page_info.setArt({'icon': 'DefaultAddonNone.png'})
        xbmcplugin.addDirectoryItem(context.addon_handle, '', page_info, False)

        jump_params = {'mode': 'jump_to_page', 'original_mode': mode}
        if mode == "genre":
            jump_params['genre_id'] = genre_id
            jump_params['display_type'] = display_type
        jump_item = xbmcgui.ListItem(label='[B]Jump to Page...[/B]')
        jump_item.setArt({'icon': 'DefaultAddonNone.png'})
        xbmcplugin.addDirectoryItem(context.addon_handle, build_url(jump_params), jump_item, True)

        if current_page > 1:
            prev_params = {'mode': mode, 'page': current_page - 1}
            if mode == "genre":
                prev_params['genre_id'] = genre_id
                prev_params['display_type'] = display_type
            prev_item = xbmcgui.ListItem(label=f'[B]<< Previous Page ({current_page - 1})[/B]')
            prev_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
            xbmcplugin.addDirectoryItem(context.addon_handle, build_url(prev_params), prev_item, True)

    show_status = context.addon.getSettingBool('show_request_status')
    statuses = {}
    if show_status and items:
        api_client.client.login()
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(items))) as executor:
            future_to_key = {
                executor.submit(media_utils.get_media_status, item.get('mediaType'), item.get('id'), item): (item.get('mediaType'), item.get('id'))
                for item in items
            }
            for future, key in future_to_key.items():
                statuses[key] = future.result()
    for item in items:
        media_type = item.get('mediaType')
        title = item.get('title') or item.get('name')
        release_date = item.get('releaseDate') or item.get('firstAirDate')
        year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
        label = f"{title} ({year})" if year else title
        if show_status:
            status_label = media_utils.get_status_label(statuses.get((media_type, item.get('id')), 0))
            if status_label:
                label += f" {status_label}"
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

    if not (is_widget and hide_pagination) and current_page < total_pages:
        next_params = {'mode': mode, 'page': current_page + 1}
        if mode == "genre":
            next_params['genre_id'] = genre_id
            next_params['display_type'] = display_type
        next_item = xbmcgui.ListItem(label=f'[B]Next Page ({current_page + 1}) >>[/B]')
        next_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        xbmcplugin.addDirectoryItem(context.addon_handle, build_url(next_params), next_item, True)

    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.endOfDirectory(context.addon_handle)


def jump_to_page():
    keyboard = xbmcgui.Dialog().input('Enter Page Number', type=xbmcgui.INPUT_NUMERIC)
    if keyboard:
        try:
            page = int(keyboard)
            if page < 1:
                xbmcgui.Dialog().notification('KodiSeerr', 'Page number must be at least 1', xbmcgui.NOTIFICATION_ERROR)
                return
            params = {'mode': context.args.get('original_mode'), 'page': page}
            if context.args.get('genre_id'):
                params['genre_id'] = context.args.get('genre_id')
            if context.args.get('display_type'):
                params['display_type'] = context.args.get('display_type')
            xbmc.executebuiltin(f'Container.Update({build_url(params)})')
        except ValueError:
            xbmcgui.Dialog().notification('KodiSeerr', 'Invalid page number', xbmcgui.NOTIFICATION_ERROR)


def list_recently_added():
    xbmcplugin.setContent(context.addon_handle, 'videos')
    page = context.args.get('page', 1)
    try:
        page = int(page)
    except Exception:
        page = 1

    # Ensure login is done before spawning threads to avoid concurrent auth attempts
    api_client.client.login()

    results = [None, None]

    def _fetch(idx, cache_key, endpoint):
        data = cache.get_cached(cache_key)
        if not data:
            data = api_client.client.api_request(endpoint, params={"sortBy": "mediaAdded", "page": page})
            if data:
                cache.set_cached(cache_key, data)
        results[idx] = data

    t_movies = threading.Thread(target=_fetch, args=(0, f"recently_added_movies_{page}", "/discover/movies"))
    t_tv = threading.Thread(target=_fetch, args=(1, f"recently_added_tv_{page}", "/discover/tv"))
    t_movies.start()
    t_tv.start()
    t_movies.join()
    t_tv.join()

    recent_movies, recent_tv = results

    all_items = []
    if recent_movies:
        for item in recent_movies.get('results', []):
            item.setdefault('mediaType', 'movie')
            all_items.append(item)
    if recent_tv:
        for item in recent_tv.get('results', []):
            item.setdefault('mediaType', 'tv')
            all_items.append(item)

    def _added_at(item):
        media_info = item.get('mediaInfo') or {}
        return media_info.get('mediaAddedAt') or media_info.get('createdAt') or ""

    all_items.sort(key=_added_at, reverse=True)

    for item in all_items[:20]:
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
    xbmcplugin.endOfDirectory(context.addon_handle)


def list_seasons(tv_id):
    xbmcplugin.setContent(context.addon_handle, 'seasons')
    cache_key = f"details_tv_{tv_id}"
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request(f"/tv/{tv_id}")
        if data:
            cache.set_cached(cache_key, data)
    if not data:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch seasons", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
        return
    show_title = data.get('title') or data.get('name')
    for season in data.get('seasons', []):
        season_number = season.get('seasonNumber', 0)
        season_name = season.get('name', f"Season {season_number}")
        label = f"{show_title} - {season_name}"
        url = build_url({'mode': 'season', 'tv_id': tv_id, 'season': season_number})
        list_item = xbmcgui.ListItem(label=label)
        media_utils.set_info_tag(list_item, media_utils.make_info(season, 'season'))
        list_item.setArt(media_utils.make_art(season))
        xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, True)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(context.addon_handle)


def list_episodes(tv_id, season_number):
    xbmcplugin.setContent(context.addon_handle, 'episodes')
    cache_key = f"tv_{tv_id}_season_{season_number}"
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request(f"/tv/{tv_id}/season/{season_number}")
        if data:
            cache.set_cached(cache_key, data)
    if not data:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch episodes", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(context.addon_handle)
        return
    for ep in data.get('episodes', []):
        ep_num = ep.get('episodeNumber', 0)
        title = ep.get('name') or ep.get('title', f"Episode {ep_num}")
        label = f"S{season_number:02d}E{ep_num:02d} - {title}"
        list_item = xbmcgui.ListItem(label=label)
        media_utils.set_info_tag(list_item, media_utils.make_info(ep, 'episode'))
        list_item.setArt(media_utils.make_art(ep))
        xbmcplugin.addDirectoryItem(context.addon_handle, '', list_item, False)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.endOfDirectory(context.addon_handle)


def search():
    xbmcplugin.setContent(context.addon_handle, 'videos')
    search_string = context.args.get("query")
    if not search_string:
        search_string = xbmcgui.Dialog().input('Search for Movie or TV Show')
    if not search_string:
        xbmcplugin.endOfDirectory(context.addon_handle)
        return
    cache_key = f"search_{search_string}"
    data = cache.get_cached(cache_key)
    if not data:
        data = api_client.client.api_request('/search', params={'query': search_string})
        if data:
            cache.set_cached(cache_key, data)
    results = data.get('results', []) if data else []
    show_status = context.addon.getSettingBool('show_request_status')
    statuses = {}
    if show_status and results:
        api_client.client.login()
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(results))) as executor:
            future_to_key = {
                executor.submit(media_utils.get_media_status, item.get('mediaType', 'movie'), item.get('id'), item): (item.get('mediaType', 'movie'), item.get('id'))
                for item in results
            }
            for future, key in future_to_key.items():
                statuses[key] = future.result()
    for item in results:
        media_type = item.get('mediaType', 'movie')
        title = item.get('title') or item.get('name')
        release_date = item.get('releaseDate') or item.get('firstAirDate')
        year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
        type_label = "(Movie)" if media_type == "movie" else "(TV Show)"
        full_title = f"{title} ({year}) {type_label}" if year else f"{title} {type_label}"
        if show_status:
            status_label = media_utils.get_status_label(statuses.get((media_type, item.get('id')), 0))
            if status_label:
                full_title += f" {status_label}"
        item_id = item.get('id')
        ctx_menu = [
            ('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": item_id})})'),
            ('Add to Favorites', f'RunPlugin({build_url({"mode": "add_favorite", "type": media_type, "id": item_id})})'),
        ]
        url = build_url({'mode': 'request', 'type': media_type, 'id': item_id})
        list_item = xbmcgui.ListItem(label=full_title)
        list_item.addContextMenuItems(ctx_menu)
        media_utils.set_info_tag(list_item, media_utils.make_info(item, media_type))
        list_item.setArt(media_utils.make_art(item))
        xbmcplugin.addDirectoryItem(context.addon_handle, url, list_item, False)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(context.addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(context.addon_handle)
