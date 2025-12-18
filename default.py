import sys
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import urllib.parse
import json
import os
import time
import api_client

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
base_url = sys.argv[0]
args = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))

image_base = "https://image.tmdb.org/t/p/w500"
enable_ask_4k = addon.getSettingBool('enable_ask_4k')

cache = {}
cache_path = xbmcvfs.translatePath(f"special://profile/addon_data/{addon.getAddonInfo('id')}/cache.json")
favorites_path = xbmcvfs.translatePath(f"special://profile/addon_data/{addon.getAddonInfo('id')}/favorites.json")
preferences_path = xbmcvfs.translatePath(f"special://profile/addon_data/{addon.getAddonInfo('id')}/preferences.json")

def load_cache():
    global cache
    if addon.getSettingBool('enable_caching'):
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'r') as f:
                    cache = json.load(f)
        except Exception as e:
            xbmc.log(f"[KodiSeerr] Cache load error: {e}", xbmc.LOGERROR)
            cache = {}

def save_cache():
    if addon.getSettingBool('enable_caching'):
        try:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            xbmc.log(f"[KodiSeerr] Cache save error: {e}", xbmc.LOGERROR)

def get_cached(key):
    if not addon.getSettingBool('enable_caching'):
        return None
    if key in cache:
        entry = cache[key]
        cache_duration = addon.getSettingInt('cache_duration') * 60
        if time.time() - entry.get('timestamp', 0) < cache_duration:
            return entry.get('data')
    return None

def set_cached(key, data):
    if addon.getSettingBool('enable_caching'):
        cache[key] = {'data': data, 'timestamp': time.time()}
        save_cache()

def load_favorites():
    try:
        if os.path.exists(favorites_path):
            with open(favorites_path, 'r') as f:
                return set(json.load(f))
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Favorites load error: {e}", xbmc.LOGERROR)
    return set()

def save_favorites(favorites):
    try:
        os.makedirs(os.path.dirname(favorites_path), exist_ok=True)
        with open(favorites_path, 'w') as f:
            json.dump(list(favorites), f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Favorites save error: {e}", xbmc.LOGERROR)

def load_preferences():
    try:
        if os.path.exists(preferences_path):
            with open(preferences_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Preferences load error: {e}", xbmc.LOGERROR)
    return {}

def save_preferences(prefs):
    try:
        os.makedirs(os.path.dirname(preferences_path), exist_ok=True)
        with open(preferences_path, 'w') as f:
            json.dump(prefs, f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Preferences save error: {e}", xbmc.LOGERROR)

load_cache()

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

def get_media_status(media_type, media_id):
    """Get the request status for a media item"""
    cache_key = f"status_{media_type}_{media_id}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached
    
    try:
        data = api_client.client.api_request(f"/{media_type}/{media_id}")
        if data and data.get('mediaInfo'):
            status = data['mediaInfo'].get('status', 0)
            set_cached(cache_key, status)
            return status
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Status check error: {e}", xbmc.LOGERROR)
    return 0

def get_status_label(status):
    """Convert status code to label"""
    status_map = {
        1: "",
        2: "[COLOR yellow](Pending)[/COLOR]",
        3: "[COLOR cyan](Processing)[/COLOR]",
        4: "[COLOR lime](Partially Available)[/COLOR]",
        5: "[COLOR lime](Available)[/COLOR]"
    }
    return status_map.get(status, "")

def test_connection():
    """Test connection to Jellyseerr server"""
    try:
        if api_client.client.login():
            xbmcgui.Dialog().notification('KodiSeerr', 'Connection successful!', xbmcgui.NOTIFICATION_INFO, 3000)
        else:
            xbmcgui.Dialog().notification('KodiSeerr', 'Connection failed. Check settings.', xbmcgui.NOTIFICATION_ERROR, 5000)
    except Exception as e:
        xbmcgui.Dialog().notification('KodiSeerr', f'Error: {str(e)}', xbmcgui.NOTIFICATION_ERROR, 5000)
    xbmc.executebuiltin("Action(Back)")

def clear_cache():
    """Clear all cached data"""
    global cache
    try:
        if os.path.exists(cache_path):
            os.remove(cache_path)
        cache = {}
        xbmcgui.Dialog().notification('KodiSeerr', 'Cache cleared successfully', xbmcgui.NOTIFICATION_INFO, 3000)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Clear cache error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('KodiSeerr', 'Failed to clear cache', xbmcgui.NOTIFICATION_ERROR)

def list_main_menu():
    xbmcplugin.setContent(addon_handle, 'files')
    
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
        
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, is_folder)
    
    xbmcplugin.endOfDirectory(addon_handle)

def list_genres(media_type):
    xbmcplugin.setContent(addon_handle, 'genres')
    cache_key = f"genres_{media_type}"
    data = get_cached(cache_key)
    
    if not data:
        data = api_client.client.api_request(f"/genres/{media_type}", params={})
        if data:
            set_cached(cache_key, data)
    
    if data:
        for item in data:
            name = item.get('name')
            id = item.get('id')
            display_type = "movies" if media_type == "movie" else media_type
            url = build_url({'mode': 'genre', 'display_type': display_type, 'genre_id': id})
            list_item = xbmcgui.ListItem(label=name)
            list_item.setArt({'icon': 'DefaultGenre.png'})
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch genres", xbmcgui.NOTIFICATION_ERROR)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)

def list_collections():
    """List movie collections"""
    xbmcplugin.setContent(addon_handle, 'sets')
    page = args.get('page', 1)
    try:
        page = int(page)
    except:
        page = 1
    
    data = api_client.client.api_request("/discover/movies", params={"page": page, "sortBy": "popularity.desc"})
    
    if data:
        items = data.get('results', [])
        collections_seen = set()
        
        for item in items:
            if item.get('belongsToCollection'):
                coll = item['belongsToCollection']
                coll_id = coll.get('id')
                if coll_id not in collections_seen:
                    collections_seen.add(coll_id)
                    name = coll.get('name', 'Unknown Collection')
                    url = build_url({'mode': 'collection_details', 'collection_id': coll_id})
                    list_item = xbmcgui.ListItem(label=name)
                    if coll.get('posterPath'):
                        list_item.setArt({'poster': image_base + coll['posterPath'], 'thumb': image_base + coll['posterPath']})
                    xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
    
    xbmcplugin.endOfDirectory(addon_handle)

def show_collection_details(collection_id):
    """Show movies in a collection"""
    xbmcplugin.setContent(addon_handle, 'movies')
    data = api_client.client.api_request(f"/collection/{collection_id}")
    
    if data:
        parts = data.get('parts', [])
        for item in parts:
            media_type = 'movie'
            title = item.get('title') or item.get('name')
            release_date = item.get('releaseDate')
            year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
            
            label = f"{title} ({year})" if year else title
            
            if addon.getSettingBool('show_request_status'):
                status = get_media_status(media_type, item.get('id'))
                status_label = get_status_label(status)
                if status_label:
                    label += f" {status_label}"
            
            id = item.get('id')
            
            context_menu = []
            context_menu.append(('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": id})})'))
            context_menu.append(('Add to Favorites', f'RunPlugin({build_url({"mode": "add_favorite", "type": media_type, "id": id})})'))
            
            url = build_url({'mode': 'request', 'type': media_type, 'id': id})
            list_item = xbmcgui.ListItem(label=label)
            list_item.addContextMenuItems(context_menu)
            info = make_info(item, media_type)
            art = make_art(item)
            set_info_tag(list_item, info)
            list_item.setArt(art)
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)
    
    xbmcplugin.endOfDirectory(addon_handle)

def list_items(data, mode, display_type=None, genre_id=None):
    items = data.get('results', [])
    current_page = data.get('page', 1)
    total_pages = data.get('totalPages', 1)
    
    if items:
        first_media_type = items[0].get('mediaType', 'video')
        if first_media_type == 'movie':
            xbmcplugin.setContent(addon_handle, 'movies')
        elif first_media_type == 'tv':
            xbmcplugin.setContent(addon_handle, 'tvshows')
        else:
            xbmcplugin.setContent(addon_handle, 'videos')
    else:
        xbmcplugin.setContent(addon_handle, 'videos')

    page_info = xbmcgui.ListItem(label=f'[I]Page {current_page} of {total_pages}[/I]')
    page_info.setArt({'icon': 'DefaultAddonNone.png'})
    xbmcplugin.addDirectoryItem(addon_handle, '', page_info, False)

    params = {'mode': 'jump_to_page', 'original_mode': mode}
    if mode == "genre":
        params['genre_id'] = genre_id
        params['display_type'] = display_type
    jump_url = build_url(params)
    jump_item = xbmcgui.ListItem(label='[B]Jump to Page...[/B]')
    jump_item.setArt({'icon': 'DefaultAddonNone.png'})
    xbmcplugin.addDirectoryItem(addon_handle, jump_url, jump_item, True)

    if current_page > 1:
        params = {
            'mode': mode,
            'page': current_page - 1
        }
        if mode == "genre":
            params['genre_id'] = genre_id
            params['display_type'] = display_type
        prev_page_url = build_url(params)
        prev_item = xbmcgui.ListItem(label=f'[B]<< Previous Page ({current_page - 1})[/B]')
        prev_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        xbmcplugin.addDirectoryItem(addon_handle, prev_page_url, prev_item, True)

    show_status = addon.getSettingBool('show_request_status')
    
    for item in items:
        media_type = item.get('mediaType')
        title = item.get('title') or item.get('name')
        release_date = item.get('releaseDate') or item.get('firstAirDate')
        year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
        label = f"{title} ({year})" if year else title
        
        if show_status:
            status = get_media_status(media_type, item.get('id'))
            status_label = get_status_label(status)
            if status_label:
                label += f" {status_label}"
        
        id = item.get('id')
        
        context_menu = []
        context_menu.append(('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": id})})'))
        context_menu.append(('Add to Favorites', f'RunPlugin({build_url({"mode": "add_favorite", "type": media_type, "id": id})})'))
        
        url = build_url({'mode': 'request', 'type': media_type, 'id': id})
        list_item = xbmcgui.ListItem(label=label)
        list_item.addContextMenuItems(context_menu)
        info = make_info(item, media_type)
        art = make_art(item)
        set_info_tag(list_item, info)
        list_item.setArt(art)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)

    if current_page < total_pages:
        params = {
            'mode': mode,
            'page': current_page + 1
        }
        if mode == "genre":
            params['genre_id'] = genre_id
            params['display_type'] = display_type
        next_page_url = build_url(params)
        next_item = xbmcgui.ListItem(label=f'[B]Next Page ({current_page + 1}) >>[/B]')
        next_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        xbmcplugin.addDirectoryItem(addon_handle, next_page_url, next_item, True)
    
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.endOfDirectory(addon_handle)

def jump_to_page():
    """Allow user to jump to a specific page"""
    keyboard = xbmcgui.Dialog().input('Enter Page Number', type=xbmcgui.INPUT_NUMERIC)
    if keyboard:
        try:
            page = int(keyboard)
            original_mode = args.get('original_mode')
            params = {'mode': original_mode, 'page': page}
            if args.get('genre_id'):
                params['genre_id'] = args.get('genre_id')
                params['display_type'] = args.get('display_type')
            xbmc.executebuiltin(f'Container.Update({build_url(params)})')
        except ValueError:
            xbmcgui.Dialog().notification('KodiSeerr', 'Invalid page number', xbmcgui.NOTIFICATION_ERROR)

def show_details(media_type, media_id):
    """Show detailed information about a media item"""
    data = api_client.client.api_request(f"/{media_type}/{media_id}")
    if not data:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch details", xbmcgui.NOTIFICATION_ERROR)
        return
    
    title = data.get('title') or data.get('name', 'Unknown')
    overview = data.get('overview', 'No description available')
    release_date = data.get('releaseDate') or data.get('firstAirDate', 'Unknown')
    rating = data.get('voteAverage', 0)
    genres = ', '.join([g['name'] for g in data.get('genres', [])])
    
    details = f"[B]{title}[/B]\n\n"
    details += f"Release Date: {release_date}\n"
    details += f"Rating: {rating}/10\n"
    if genres:
        details += f"Genres: {genres}\n"
    details += f"\n{overview}\n\n"
    
    if data.get('cast'):
        cast_names = [c['name'] for c in data['cast'][:10]]
        details += f"\n[B]Cast:[/B]\n{', '.join(cast_names)}\n"
    
    if data.get('recommendations'):
        details += f"\n[B]Recommended:[/B]\n"
        for rec in data['recommendations'][:5]:
            rec_title = rec.get('title') or rec.get('name')
            details += f"• {rec_title}\n"
    
    xbmcgui.Dialog().textviewer(title, details)

def add_to_favorites(media_type, media_id):
    """Add item to favorites"""
    favorites = load_favorites()
    fav_key = f"{media_type}_{media_id}"
    if fav_key in favorites:
        xbmcgui.Dialog().notification('KodiSeerr', 'Already in favorites', xbmcgui.NOTIFICATION_INFO)
    else:
        favorites.add(fav_key)
        save_favorites(favorites)
        xbmcgui.Dialog().notification('KodiSeerr', 'Added to favorites', xbmcgui.NOTIFICATION_INFO)

def remove_from_favorites(media_type, media_id):
    """Remove item from favorites"""
    favorites = load_favorites()
    fav_key = f"{media_type}_{media_id}"
    if fav_key in favorites:
        favorites.remove(fav_key)
        save_favorites(favorites)
        xbmcgui.Dialog().notification('KodiSeerr', 'Removed from favorites', xbmcgui.NOTIFICATION_INFO)
        xbmc.executebuiltin('Container.Refresh')

def list_favorites():
    """List user's favorite items"""
    xbmcplugin.setContent(addon_handle, 'videos')
    favorites = load_favorites()
    
    if not favorites:
        info_item = xbmcgui.ListItem(label='[I]No favorites yet[/I]')
        xbmcplugin.addDirectoryItem(addon_handle, '', info_item, False)
    else:
        for fav in favorites:
            parts = fav.split('_')
            if len(parts) >= 2:
                media_type = parts[0]
                media_id = parts[1]
                
                data = api_client.client.api_request(f"/{media_type}/{media_id}")
                if data:
                    title = data.get('title') or data.get('name', 'Unknown')
                    label = title
                    
                    context_menu = []
                    context_menu.append(('Remove from Favorites', f'RunPlugin({build_url({"mode": "remove_favorite", "type": media_type, "id": media_id})})'))
                    context_menu.append(('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": media_id})})'))
                    
                    url = build_url({'mode': 'request', 'type': media_type, 'id': media_id})
                    list_item = xbmcgui.ListItem(label=label)
                    list_item.addContextMenuItems(context_menu)
                    info = make_info(data, media_type)
                    art = make_art(data)
                    set_info_tag(list_item, info)
                    list_item.setArt(art)
                    xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)
    
    xbmcplugin.endOfDirectory(addon_handle)

def show_statistics():
    """Show user statistics"""
    try:
        requests_data = api_client.client.api_request('/request', params={'take': 1000})
        if not requests_data:
            xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch statistics", xbmcgui.NOTIFICATION_ERROR)
            return
        
        items = requests_data.get('results', [])
        
        total = len(items)
        movies = sum(1 for i in items if i.get('media', {}).get('mediaType') == 'movie')
        tv = sum(1 for i in items if i.get('media', {}).get('mediaType') == 'tv')
        
        status_counts = {}
        for item in items:
            status = item.get('media', {}).get('status', 0)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        pending = status_counts.get(2, 0)
        processing = status_counts.get(3, 0)
        available = status_counts.get(5, 0)
        
        stats = f"[B]Your Request Statistics[/B]\n\n"
        stats += f"Total Requests: {total}\n"
        stats += f"Movies: {movies}\n"
        stats += f"TV Shows: {tv}\n\n"
        stats += f"[COLOR yellow]Pending:[/COLOR] {pending}\n"
        stats += f"[COLOR cyan]Processing:[/COLOR] {processing}\n"
        stats += f"[COLOR lime]Available:[/COLOR] {available}\n"
        
        xbmcgui.Dialog().textviewer("Statistics", stats)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Statistics error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch statistics", xbmcgui.NOTIFICATION_ERROR)
    xbmc.executebuiltin("Action(Back)")

def get_quality_profiles():
    """Get available quality profiles from server"""
    try:
        # This depends on Jellyseerr API - might need adjustment
        data = api_client.client.api_request('/settings/radarr')
        if data and isinstance(data, list) and len(data) > 0:
            profiles = data[0].get('profiles', [])
            return [(p['id'], p['name']) for p in profiles]
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Quality profiles error: {e}", xbmc.LOGERROR)
    return []

def do_request(media_type, id):
    """Handle media request with advanced options"""
    # Check if already requested/available
    status = get_media_status(media_type, id)
    if status >= 5:
        if not xbmcgui.Dialog().yesno('KodiSeerr', 'This content is already available. Request anyway?'):
            return
    elif status in [2, 3, 4]:
        if not xbmcgui.Dialog().yesno('KodiSeerr', 'This content is already requested. Request again?'):
            return
    
    is4k = False
    quality_profile = None
    seasons_to_request = "all"
    
    if enable_ask_4k:
        prefs = load_preferences()
        if addon.getSettingBool('remember_last_quality') and 'last_4k_choice' in prefs:
            is4k = prefs['last_4k_choice']
        else:
            if xbmcgui.Dialog().yesno('KodiSeerr', 'Request in 4K quality?'):
                is4k = True
        
        if addon.getSettingBool('remember_last_quality'):
            prefs['last_4k_choice'] = is4k
            save_preferences(prefs)
    
    if addon.getSettingBool('show_quality_profiles'):
        profiles = get_quality_profiles()
        if profiles:
            profile_names = [p[1] for p in profiles]
            selected = xbmcgui.Dialog().select('Select Quality Profile', profile_names)
            if selected >= 0:
                quality_profile = profiles[selected][0]
    
    if media_type == "tv" and addon.getSettingBool('enable_season_selection'):
        tv_data = api_client.client.api_request(f"/tv/{id}")
        if tv_data and tv_data.get('seasons'):
            seasons = tv_data['seasons']
            season_names = ['All Seasons'] + [f"Season {s.get('seasonNumber', 0)}" for s in seasons]
            selected = xbmcgui.Dialog().select('Select Seasons', season_names)
            if selected > 0:
                seasons_to_request = [seasons[selected - 1].get('seasonNumber')]
            elif selected < 0:
                return
    
    if addon.getSettingBool('confirm_before_request'):
        title_data = api_client.client.api_request(f"/{media_type}/{id}")
        title = title_data.get('title') or title_data.get('name', 'this content') if title_data else 'this content'
        msg = f"Request {title}"
        if is4k:
            msg += " in 4K"
        msg += "?"
        if not xbmcgui.Dialog().yesno('KodiSeerr', msg):
            return
    
    payload = {
        "mediaType": media_type,
        "mediaId": int(id),
        "is4k": is4k
    }
    
    if media_type == "tv":
        payload["seasons"] = seasons_to_request
    
    if quality_profile:
        payload["profileId"] = quality_profile
    
    try:
        api_client.client.api_request("/request", method="POST", data=payload)
        xbmcgui.Dialog().notification('KodiSeerr', 'Request Sent!', xbmcgui.NOTIFICATION_INFO, 3000)
        cache_key = f"status_{media_type}_{id}"
        if cache_key in cache:
            del cache[cache_key]
            save_cache()
    except Exception as e:
        xbmcgui.Dialog().notification('KodiSeerr', f'Request Failed: {str(e)}', xbmcgui.NOTIFICATION_ERROR, 4000)
    
    xbmc.executebuiltin("Action(Back)")

def cancel_request(request_id):
    """Cancel a pending request"""
    if xbmcgui.Dialog().yesno('KodiSeerr', 'Cancel this request?'):
        try:
            api_client.client.api_request(f"/request/{request_id}", method="DELETE")
            xbmcgui.Dialog().notification('KodiSeerr', 'Request cancelled', xbmcgui.NOTIFICATION_INFO)
            xbmc.executebuiltin('Container.Refresh')
        except Exception as e:
            xbmcgui.Dialog().notification('KodiSeerr', f'Failed to cancel: {str(e)}', xbmcgui.NOTIFICATION_ERROR)

def show_requests(data, mode, current_page=1):
    xbmcplugin.setContent(addon_handle, 'videos')
    items = data.get('results', [])
    page_info = data.get('pageInfo', {})
    total_results = page_info.get('results', len(items))
    total_pages = page_info.get('pages', 1)

    page_info = xbmcgui.ListItem(label=f'[I]Page {current_page} of {total_pages}[/I]')
    page_info.setArt({'icon': 'DefaultAddonNone.png'})
    xbmcplugin.addDirectoryItem(addon_handle, '', page_info, False)

    if current_page > 1:
        prev_page_url = build_url({'mode': mode, 'page': current_page - 1})
        prev_item = xbmcgui.ListItem(label=f'[B]<< Previous Page ({current_page - 1})[/B]')
        prev_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        xbmcplugin.addDirectoryItem(addon_handle, prev_page_url, prev_item, True)

    for item in items:
        media = item.get('media', {})
        id = media.get('tmdbId')
        media_type = media.get('mediaType')
        request_id = item.get('id')
        
        mediaData = api_client.client.api_request(f"/{media_type}/{id}", params={})
        if not mediaData:
            continue
        label_text = mediaData.get('title') or mediaData.get('name') or "Untitled"

        status = media.get('status')
        if status == 2:
            label_text += " [COLOR yellow](Pending)[/COLOR]"
        elif status == 3:
            label_text += " [COLOR cyan](Processing)[/COLOR]"
        elif status == 4:
            label_text += " [COLOR lime](Partially Available)[/COLOR]"
        elif status == 5:
            label_text += " [COLOR lime](Available)[/COLOR]"

        context_menu = []
        if status in [2, 3]:
            context_menu.append(('Cancel Request', f'RunPlugin({build_url({"mode": "cancel_request", "request_id": request_id})})'))
        context_menu.append(('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": id})})'))

        url = build_url({'mode': 'request', 'type': media_type, 'id': id})
        list_item = xbmcgui.ListItem(label=label_text)
        list_item.addContextMenuItems(context_menu)
        info = {'title': label_text, 'plot': f"Media ID: {id}, Type: {media_type}"}
        set_info_tag(list_item, info)
        art = make_art(mediaData)
        list_item.setArt(art)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)

    if current_page < total_pages:
        next_page_url = build_url({'mode': mode, 'page': current_page + 1})
        next_item = xbmcgui.ListItem(label=f'[B]Next Page ({current_page + 1}) >>[/B]')
        next_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        xbmcplugin.addDirectoryItem(addon_handle, next_page_url, next_item, True)
    
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)    

def list_recently_added():
    """Show recently added content to the server"""
    xbmcplugin.setContent(addon_handle, 'videos')
    page = args.get('page', 1)
    try:
        page = int(page)
    except:
        page = 1
    
    recent_movies = api_client.client.api_request("/discover/movies", params={"sortBy": "mediaAdded", "page": page})
    recent_tv = api_client.client.api_request("/discover/tv", params={"sortBy": "mediaAdded", "page": page})
    
    all_items = []
    if recent_movies:
        all_items.extend(recent_movies.get('results', []))
    if recent_tv:
        all_items.extend(recent_tv.get('results', []))
    
    for item in all_items[:20]:
        media_type = item.get('mediaType')
        title = item.get('title') or item.get('name')
        release_date = item.get('releaseDate') or item.get('firstAirDate')
        year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
        label = f"{title} ({year})" if year else title
        
        id = item.get('id')
        
        context_menu = []
        context_menu.append(('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": id})})'))
        context_menu.append(('Add to Favorites', f'RunPlugin({build_url({"mode": "add_favorite", "type": media_type, "id": id})})'))
        
        url = build_url({'mode': 'request', 'type': media_type, 'id': id})
        list_item = xbmcgui.ListItem(label=label)
        list_item.addContextMenuItems(context_menu)
        info = make_info(item, media_type)
        art = make_art(item)
        set_info_tag(list_item, info)
        list_item.setArt(art)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)
    
    xbmcplugin.endOfDirectory(addon_handle)

def report_issue(media_type, media_id):
    """Report an issue with media"""
    issue_types = ['Video Issue', 'Audio Issue', 'Subtitles Issue', 'Other']
    selected = xbmcgui.Dialog().select('Select Issue Type', issue_types)
    if selected < 0:
        return
    
    message = xbmcgui.Dialog().input('Describe the issue (optional)')
    
    try:
        payload = {
            "issueType": selected + 1,
            "message": message or ""
        }
        api_client.client.api_request(f"/{media_type}/{media_id}/issue", method="POST", data=payload)
        xbmcgui.Dialog().notification('KodiSeerr', 'Issue reported', xbmcgui.NOTIFICATION_INFO)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Issue report error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('KodiSeerr', 'Failed to report issue', xbmcgui.NOTIFICATION_ERROR)

def list_seasons(tv_id):
    xbmcplugin.setContent(addon_handle, 'seasons')
    data = api_client.client.api_request(f"/tv/{tv_id}")
    if not data:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch seasons", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)
        return
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
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)

def list_episodes(tv_id, season_number):
    xbmcplugin.setContent(addon_handle, 'episodes')
    data = api_client.client.api_request(f"/tv/{tv_id}/season/{season_number}")
    if not data:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch episodes", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)
        return
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
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.endOfDirectory(addon_handle)

def search():
    xbmcplugin.setContent(addon_handle, 'videos')
    keyboard = xbmcgui.Dialog().input('Search for Movie or TV Show')
    if keyboard:
        cache_key = f"search_{keyboard}"
        data = get_cached(cache_key)
        
        if not data:
            data = api_client.client.api_request('/search', params={'query': keyboard})
            if data:
                set_cached(cache_key, data)
        
        results = data.get('results', []) if data else []
        show_status = addon.getSettingBool('show_request_status')
        
        for item in results:
            media_type = item.get('mediaType', 'movie')
            title = item.get('title') or item.get('name')
            release_date = item.get('releaseDate') or item.get('firstAirDate')
            year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else None
            type_label = "(Movie)" if media_type == "movie" else "(TV Show)"
            full_title = f"{title} ({year}) {type_label}" if year else f"{title} {type_label}"
            
            if show_status:
                status = get_media_status(media_type, item.get('id'))
                status_label = get_status_label(status)
                if status_label:
                    full_title += f" {status_label}"
            
            context_menu = []
            context_menu.append(('Show Details', f'RunPlugin({build_url({"mode": "show_details", "type": media_type, "id": item.get("id")})})'))
            context_menu.append(('Add to Favorites', f'RunPlugin({build_url({"mode": "add_favorite", "type": media_type, "id": item.get("id")})})'))
            
            url = build_url({'mode': 'request', 'type': media_type, 'id': item.get('id')})
            list_item = xbmcgui.ListItem(label=full_title)
            list_item.addContextMenuItems(context_menu)
            info = make_info(item, media_type)
            art = make_art(item)
            set_info_tag(list_item, info)
            list_item.setArt(art)
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(addon_handle)

mode = args.get('mode')
page = args.get('page')
if not page:
    page = 1
else:
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

if not mode:
    list_main_menu()
elif mode == "test_connection":
    test_connection()
elif mode == "clear_cache":
    clear_cache()
elif mode == "statistics":
    show_statistics()
elif mode == "favorites":
    list_favorites()
elif mode == "add_favorite":
    add_to_favorites(args.get('type'), args.get('id'))
elif mode == "remove_favorite":
    remove_from_favorites(args.get('type'), args.get('id'))
elif mode == "show_details":
    show_details(args.get('type'), args.get('id'))
elif mode == "report_issue":
    report_issue(args.get('type'), args.get('id'))
elif mode == "cancel_request":
    cancel_request(args.get('request_id'))
elif mode == "jump_to_page":
    jump_to_page()
elif mode == "collections":
    list_collections()
elif mode == "collection_details":
    show_collection_details(args.get('collection_id'))
elif mode == "recently_added":
    list_recently_added()
elif mode == "trending":
    cache_key = f"trending_{page}"
    data = get_cached(cache_key)
    if not data:
        data = api_client.client.api_request("/discover/trending", params={"page": page})
        if data:
            set_cached(cache_key, data)
    if data:
        list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch trending", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)
elif mode == "popular_movies":
    cache_key = f"popular_movies_{page}"
    data = get_cached(cache_key)
    if not data:
        data = api_client.client.api_request("/discover/movies", params={"sortBy": "popularity.desc", "page": page})
        if data:
            set_cached(cache_key, data)
    if data:
        list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch popular movies", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)
elif mode == "popular_tv":
    cache_key = f"popular_tv_{page}"
    data = get_cached(cache_key)
    if not data:
        data = api_client.client.api_request("/discover/tv", params={"sortBy": "popularity.desc", "page": page})
        if data:
            set_cached(cache_key, data)
    if data:
        list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch popular TV shows", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)
elif mode == "upcoming_movies":
    cache_key = f"upcoming_movies_{page}"
    data = get_cached(cache_key)
    if not data:
        data = api_client.client.api_request("/discover/movies/upcoming", params={"page": page})
        if data:
            set_cached(cache_key, data)
    if data:
        list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch upcoming movies", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)
elif mode == "upcoming_tv":
    cache_key = f"upcoming_tv_{page}"
    data = get_cached(cache_key)
    if not data:
        data = api_client.client.api_request("/discover/tv/upcoming", params={"page": page})
        if data:
            set_cached(cache_key, data)
    if data:
        list_items(data, mode)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch upcoming TV shows", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)
elif mode == "search":
    search()
elif mode == "request":
    do_request(args.get('type'), args.get('id'))
elif mode == "requests":
    take = 20
    skip = (page - 1) * take
    data = api_client.client.api_request("/request", params={"take": take, "skip": skip, "sort": "added", "filter": "all"})
    if data:
        show_requests(data, mode, page)
    else:
        xbmcgui.Dialog().notification("Kodiseerr", "Failed to fetch requests", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)
elif mode == "tvshow" and args.get("id"):
    list_seasons(args.get("id"))
elif mode == "season" and args.get("tv_id") and args.get("season"):
    list_episodes(args.get("tv_id"), int(args.get("season")))
elif mode == "genres" and args.get("media_type"):
    list_genres(args.get("media_type"))
elif mode == "genre" and args.get("display_type") and args.get("genre_id"):
    display_type = args.get("display_type")
    genre_id = args.get("genre_id")
    cache_key = f"genre_{display_type}_{genre_id}_{page}"
    data = get_cached(cache_key)
    if not data:
        data = api_client.client.api_request(f"/discover/{display_type}/genre/{genre_id}", params={"page": page})
        if data:
            set_cached(cache_key, data)
    if data:
        list_items(data, mode, display_type, genre_id)
    else:
        xbmcgui.Dialog().notification("KodiSeerr", "Failed to fetch genre items", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(addon_handle)
