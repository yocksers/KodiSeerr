import sys
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import urllib.parse
import api_client

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
base_url = sys.argv[0]
args = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))

image_base = "https://image.tmdb.org/t/p/w500"
enable_ask_4k = addon.getSettingBool('enable_ask_4k')

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def make_art(item):
    art = {}
    for k in ["posterPath", "backdropPath", "logoPath", "bannerPath", "landscapePath", "iconPath", "clearartPath"]:
        if item.get(k):
            if k == "posterPath":
                art["poster"] = image_base + item[k]
                art["thumb"] = image_base + item[k]
            elif k == "backdropPath":
                art["fanart"] = image_base + item[k]
            elif k == "logoPath":
                art["clearlogo"] = image_base + item[k]
            elif k == "bannerPath":
                art["banner"] = image_base + item[k]
            elif k == "landscapePath":
                art["landscape"] = image_base + item[k]
            elif k == "iconPath":
                art["icon"] = image_base + item[k]
            elif k == "clearartPath":
                art["clearart"] = image_base + item[k]
    return art

def make_info(item, media_type):
    release_date = item.get('releaseDate') or item.get('firstAirDate')
    year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else 0
    def join_names(obj_list):
        return ', '.join(
            g['name'] if isinstance(g, dict) and 'name' in g else str(g)
            for g in obj_list
        )
    genres = join_names(item.get('genres', []))
    studio = join_names(item.get('studios', [])) if item.get('studios') else ''
    country = join_names(item.get('productionCountries', [])) if item.get('productionCountries') else ''
    mpaa = item.get('certification', '')
    runtime = item.get('runtime', 0)
    try:
        runtime = int(runtime)
    except Exception:
        runtime = 0
    try:
        rating = float(item.get('voteAverage', 0))
    except Exception:
        rating = 0.0
    votes = item.get('voteCount', 0)
    try:
        votes = int(votes)
    except Exception:
        votes = 0
    director = ', '.join([c['name'] for c in item.get('crew', []) if c.get('job') == 'Director']) if item.get('crew') else ''
    cast = [person['name'] for person in item.get('cast', []) if isinstance(person, dict) and 'name' in person]
    cast_str = ', '.join(cast[:5])
    plot = item.get('overview', '')
    title = item.get('title') or item.get('name')
    # Rich plot for display
    rich_plot = f"{title} ({year})"
    if genres: rich_plot += f"\nGenres: {genres}"
    if studio: rich_plot += f"\nStudio: {studio}"
    if country: rich_plot += f"\nCountry: {country}"
    if mpaa: rich_plot += f"\nCertification: {mpaa}"
    if runtime: rich_plot += f"\nRuntime: {runtime} min"
    if rating: rich_plot += f"\nRating: {rating} ({votes} votes)"
    if director: rich_plot += f"\nDirector: {director}"
    if cast_str: rich_plot += f"\nCast: {cast_str}"
    if plot: rich_plot += f"\n\n{plot}"

    info = {
        'title': title or "",
        'plot': rich_plot or "",
        'year': year,
        'genre': genres or "",
        'rating': rating,
        'votes': votes,
        'premiered': release_date or "",
        'duration': runtime,
        'mpaa': mpaa or "",
        'cast': cast,
        'director': director or "",
        'studio': studio or "",
        'country': country or "",
        'mediatype': media_type
    }
    return info

def set_info_tag(list_item, info):
    info_tag = list_item.getVideoInfoTag()
    if info.get('title'): info_tag.setTitle(info['title'])
    if info.get('plot'): info_tag.setPlot(info['plot'])
    if info.get('year'):
        try:
            info_tag.setYear(int(info['year']))
        except Exception:
            pass
    if info.get('genre'): info_tag.setGenre(info['genre'])
    if info.get('rating'):
        try:
            info_tag.setRating(float(info['rating']))
        except Exception:
            pass
    if info.get('votes'):
        try:
            info_tag.setVotes(int(info['votes']))
        except Exception:
            pass
    if info.get('premiered'): info_tag.setPremiered(info['premiered'])
    if info.get('duration'):
        try:
            info_tag.setDuration(int(info['duration']))
        except Exception:
            pass
    if info.get('mpaa'): info_tag.setMpaa(info['mpaa'])
    if info.get('cast'): info_tag.setCast(info['cast'])
    if info.get('director'): info_tag.setDirector(info['director'])
    if info.get('studio'): info_tag.setStudio(info['studio'])
    if info.get('country'): info_tag.setCountry(info['country'])
    if info.get('mediatype'): info_tag.setMediaType(info['mediatype'])

def list_main_menu():
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'search'}), xbmcgui.ListItem('Search'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'trending_movies'}), xbmcgui.ListItem('Trending Movies'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'trending_tv'}), xbmcgui.ListItem('Trending TV Shows'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'popular_movies'}), xbmcgui.ListItem('Popular Movies'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'popular_tv'}), xbmcgui.ListItem('Popular TV Shows'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'upcoming_movies'}), xbmcgui.ListItem('Upcoming Movies'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'upcoming_tv'}), xbmcgui.ListItem('Upcoming TV Shows'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'tvshows'}), xbmcgui.ListItem('Browse TV Shows'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'requests'}), xbmcgui.ListItem('Request Progress'), True)
    xbmcplugin.endOfDirectory(addon_handle)

def list_items(data, media_type, mode):
    items = data.get('results', [])
    current_page = data.get('page', 1)
    total_pages = data.get('totalPages', 1)

    # Show page info
    page_info = xbmcgui.ListItem(label=f'[I]Page {current_page} of {total_pages}[/I]')
    xbmcplugin.addDirectoryItem(addon_handle, '', page_info, False)

    # Previous Page
    if current_page > 1:
        prev_page_url = build_url({'mode': mode, 'page': current_page - 1})
        prev_item = xbmcgui.ListItem(label=f'[B]<< Previous Page ({current_page - 1})[/B]')
        xbmcplugin.addDirectoryItem(addon_handle, prev_page_url, prev_item, True)

    # Media Items
    for item in items:
        title = item.get('title') or item.get('name')
        release_date = item.get('releaseDate') or item.get('firstAirDate')
        year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
        label = f"{title} ({year})" if year else title
        id = item.get('id')
        url = build_url({'mode': 'request', 'type': media_type, 'id': id})
        list_item = xbmcgui.ListItem(label=label)
        info = make_info(item, media_type)
        art = make_art(item)
        set_info_tag(list_item, info)
        list_item.setArt(art)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)

    # Next Page
    if current_page < total_pages:
        next_page_url = build_url({'mode': mode, 'page': current_page + 1})
        next_item = xbmcgui.ListItem(label=f'[B]Next Page ({current_page + 1}) >>[/B]')
        xbmcplugin.addDirectoryItem(addon_handle, next_page_url, next_item, True)

    xbmcplugin.endOfDirectory(addon_handle)


def list_tvshows(page=1):
    params = {"sortBy": "popularity.desc", "page": page}
    data = api_client.client.api_request("/discover/tv", params=params)
    results = data.get('results', []) if data else []
    current_page = data.get('page', 1)
    total_pages = data.get('total_pages', 1)

    # Show page info (non-clickable)
    page_info = xbmcgui.ListItem(label=f'[I]Page {current_page} of {total_pages}[/I]')
    xbmcplugin.addDirectoryItem(addon_handle, '', page_info, False)

    # Previous Page
    if current_page > 1:
        previous_page_url = build_url({'mode': 'list_tvshows', 'page': current_page - 1})
        previous_item = xbmcgui.ListItem(label=f'[B]<< Previous Page ({current_page - 1})[/B]')
        xbmcplugin.addDirectoryItem(addon_handle, previous_page_url, previous_item, True)

    # TV show items
    for item in results:
        title = item.get('title') or item.get('name')
        year = int(item.get('firstAirDate', '1900')[:4]) if item.get('firstAirDate') and item.get('firstAirDate').split("-")[0].isdigit() else None
        label = f"{title} ({year})" if year else title
        url = build_url({'mode': 'request', 'type': 'tv', 'id': item.get('id')})
        list_item = xbmcgui.ListItem(label=label)
        info = make_info(item, 'tv')
        art = make_art(item)
        set_info_tag(list_item, info)
        list_item.setArt(art)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)

    # Next Page
    if current_page < total_pages:
        next_page_url = build_url({'mode': 'list_tvshows', 'page': current_page + 1})
        next_item = xbmcgui.ListItem(label=f'[B]Next Page ({current_page + 1}) >>[/B]')
        xbmcplugin.addDirectoryItem(addon_handle, next_page_url, next_item, True)

    xbmcplugin.endOfDirectory(addon_handle)

def do_request(media_type, id):
    is4k = False
    if enable_ask_4k:
        if xbmcgui.Dialog().yesno('KodiSeerr', 'Request in 4K quality?'):
            is4k = True
    payload = {
        "mediaType": media_type,
        "mediaId": int(id),
        "is4k": is4k
    }
    if media_type == "tv":
        payload["seasons"] = "all"
    try:
        api_client.client.api_request("/request", method="POST", data=payload)
        xbmcgui.Dialog().notification('KodiSeerr', 'Request Sent!', xbmcgui.NOTIFICATION_INFO, 3000)
    except Exception as e:
        xbmcgui.Dialog().notification('KodiSeerr', f'Request Failed: {str(e)}', xbmcgui.NOTIFICATION_ERROR, 4000)
    xbmc.executebuiltin("Action(Back)")

def show_requests(data, mode):
    items = data.get('results', [])
    current_page = data.get('page', 1)
    total_pages = data.get('totalPages', 1)

    # Show page info
    page_info = xbmcgui.ListItem(label=f'[I]Page {current_page} of {total_pages}[/I]')
    xbmcplugin.addDirectoryItem(addon_handle, '', page_info, False)

    # Previous Page
    if current_page > 1:
        prev_page_url = build_url({'mode': mode, 'page': current_page - 1})
        prev_item = xbmcgui.ListItem(label=f'[B]<< Previous Page ({current_page - 1})[/B]')
        xbmcplugin.addDirectoryItem(addon_handle, prev_page_url, prev_item, True)

    for item in items:
        media = item.get('media', {})
        id = media.get('tmdbId')
        media_type = media.get('mediaType')
        mediaData = api_client.client.api_request(f"/{media_type}/{id}", params={})
        label_text = mediaData.get('title') or mediaData.get('name') or "Untitled"

        status = media.get('status')
        info = {}
        if status == 3:
            label_text += " [COLOR blue](Requested)[/COLOR]"
        elif status == 4:
            label_text += " [COLOR lime](Partially Available)[/COLOR]"
        elif status == 5:
            label_text += " [COLOR lime](Available)[/COLOR]"

        url = ""  # build_url({'mode': 'request_view', 'type': media_type, 'id': id})
        list_item = xbmcgui.ListItem(label=label_text)
        info['title'] = label_text
        info['plot'] = f"Media ID: {id}, Type: {media_type}"
        set_info_tag(list_item, info)
        art = make_art(mediaData)
        list_item.setArt(art)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)

    # Next Page
    if current_page < total_pages:
        next_page_url = build_url({'mode': mode, 'page': current_page + 1})
        next_item = xbmcgui.ListItem(label=f'[B]Next Page ({current_page + 1}) >>[/B]')
        xbmcplugin.addDirectoryItem(addon_handle, next_page_url, next_item, True)

    xbmcplugin.endOfDirectory(addon_handle)    

def list_seasons(tv_id):
    data = api_client.client.api_request(f"/tv/{tv_id}")
    seasons = data.get('seasons', [])
    show_title = data.get('title') or data.get('name')
    for season in seasons:
        season_number = season.get('seasonNumber', 0)
        season_name = season.get('name', f"Season {season_number}")
        label = f"{show_title} - {season_name}"
        url = build_url({'mode': 'season', 'tv_id': tv_id, 'season': season_number})
        list_item = xbmcgui.ListItem(label=label)
        info = make_info(season, 'season')
        art = make_art(season)
        set_info_tag(list_item, info)
        list_item.setArt(art)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(addon_handle)

def list_episodes(tv_id, season_number):
    data = api_client.client.api_request(f"/tv/{tv_id}/season/{season_number}")
    episodes = data.get('episodes', [])
    show_title = data.get('show', {}).get('name') or data.get('show', {}).get('title', '')
    for ep in episodes:
        ep_num = ep.get('episodeNumber', 0)
        title = ep.get('name') or ep.get('title', f"Episode {ep_num}")
        label = f"S{season_number:02d}E{ep_num:02d} - {title}"
        list_item = xbmcgui.ListItem(label=label)
        info = make_info(ep, 'episode')
        art = make_art(ep)
        set_info_tag(list_item, info)
        list_item.setArt(art)
        xbmcplugin.addDirectoryItem(addon_handle, '', list_item, False)
    xbmcplugin.endOfDirectory(addon_handle)

def search():
    keyboard = xbmcgui.Dialog().input('Search for Movie or TV Show')
    if keyboard:
        data = api_client.client.api_request('/search', params={'query': keyboard})
        results = data.get('results', []) if data else []
        for item in results:
            media_type = item.get('mediaType', 'movie')
            title = item.get('title') or item.get('name')
            release_date = item.get('releaseDate') or item.get('firstAirDate')
            year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
            type_label = "(Movie)" if media_type == "movie" else "(TV Show)"
            full_title = f"{title} ({year}) {type_label}" if year else f"{title} {type_label}"
            url = build_url({'mode': 'request', 'type': media_type, 'id': item.get('id')})
            list_item = xbmcgui.ListItem(label=full_title)
            info = make_info(item, media_type)
            art = make_art(item)
            set_info_tag(list_item, info)
            list_item.setArt(art)
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(addon_handle)

mode = args.get('mode')
page = args.get('page')
if not page:
    page = 1
if not mode:
    list_main_menu()
elif mode == "trending_movies": # functionality is somewhat broken
    data = api_client.client.api_request("/discover/trending", params={"page": page})
    list_items(data, "movie", mode)
elif mode == "trending_tv": # functionality is somewhat broken
    data = api_client.client.api_request("/discover/trending", params={"page": page})
    list_items(data, "tv", mode)
elif mode == "popular_movies":
    data = api_client.client.api_request("/discover/movies", params={"sortBy": "popularity.desc", "page": page})
    list_items(data, "movie", mode)
elif mode == "popular_tv":
    data = api_client.client.api_request("/discover/tv", params={"sortBy": "popularity.desc", "page": page})
    list_items(data, "tv", mode)
elif mode == "upcoming_movies":
    data = api_client.client.api_request("/discover/movies/upcoming", params={"page": page})
    list_items(data, "movie", mode)
elif mode == "upcoming_tv":
    data = api_client.client.api_request("/discover/tv/upcoming", params={"page": page})
    list_items(data, "tv", mode)
elif mode == "search": # functionality is completely broken
    search()
elif mode == "request":
    do_request(args.get('type'), args.get('id'))
elif mode == "requests":
    data = api_client.client.api_request("/request", params={"sort": "added", "filter": "all", "sortDirection": "desc"})
    if data:
        show_requests(data, mode)
    else:
        xbmcgui.Dialog().notification("Kodiseerr", "Failed to fetch requests", xbmcgui.NOTIFICATION_ERROR)

elif mode == "tvshows":
    list_tvshows()
elif mode == "tvshow" and args.get("id"):
    list_seasons(args.get("id"))
elif mode == "season" and args.get("tv_id") and args.get("season"):
    list_episodes(args.get("tv_id"), int(args.get("season")))
