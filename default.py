import sys
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import urllib.parse
import urllib.request
import json
import http.cookiejar

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
base_url = sys.argv[0]
args = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))

jellyseerr_url = addon.getSetting('jellyseerr_url').rstrip('/')
username = addon.getSetting('jellyseerr_username')
password = addon.getSetting('jellyseerr_password')
enable_ask_4k = addon.getSettingBool('enable_ask_4k')

image_base = "https://image.tmdb.org/t/p/w500"

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def login():
    if not jellyseerr_url or not username or not password:
        xbmcgui.Dialog().notification('KodiSeerr', 'Please set URL, Username, and Password in Settings.', xbmcgui.NOTIFICATION_ERROR, 5000)
        return False
    login_url = f"{jellyseerr_url}/api/v1/auth/local"
    payload = json.dumps({"email": username, "password": password}).encode('utf-8')
    req = urllib.request.Request(login_url, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with opener.open(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        xbmcgui.Dialog().notification('KodiSeerr', f'Login Error: {str(e)}', xbmcgui.NOTIFICATION_ERROR, 3000)
        return False

def get_api(endpoint, params=None):
    if not any(cookie.name == "connect.sid" for cookie in cookie_jar):
        if not login():
            return {}
    url = f"{jellyseerr_url}/api/v1{endpoint}"
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/json')
    try:
        with opener.open(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        xbmcgui.Dialog().notification('KodiSeerr', f'API Error: {str(e)}', xbmcgui.NOTIFICATION_ERROR, 3000)
        return {}

def list_main_menu():
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'search'}), xbmcgui.ListItem('Search'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'trending_movies'}), xbmcgui.ListItem('Trending Movies'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'trending_tv'}), xbmcgui.ListItem('Trending TV Shows'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'popular_movies'}), xbmcgui.ListItem('Popular Movies'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'popular_tv'}), xbmcgui.ListItem('Popular TV Shows'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'upcoming_movies'}), xbmcgui.ListItem('Upcoming Movies'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'upcoming_tv'}), xbmcgui.ListItem('Upcoming TV Shows'), True)
    xbmcplugin.addDirectoryItem(addon_handle, build_url({'mode': 'requests'}), xbmcgui.ListItem('Request Progress'), True)
    xbmcplugin.endOfDirectory(addon_handle)

def list_items(items, media_type):
    for item in items:
        title = item.get('title') or item.get('name')
        release_date = item.get('releaseDate') or item.get('firstAirDate')
        if release_date:
            year = release_date.split("-")[0]
            title = f"{title} ({year})"
        plot = item.get('overview') or ""
        poster = item.get('posterPath')
        id = item.get('id')

        url = build_url({'mode': 'details', 'type': media_type, 'id': id})

        list_item = xbmcgui.ListItem(label=title)
        info = list_item.getVideoInfoTag()
        info.setTitle(title)
        info.setPlot(plot)

        if poster:
            art_url = image_base + poster
            list_item.setArt({'thumb': art_url, 'poster': art_url, 'fanart': art_url})

        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(addon_handle)

def show_details(media_type, id):
    data = get_api(f"/{media_type}/{id}")
    title = data.get('title') or data.get('name')
    overview = data.get('overview') or ""
    poster_path = data.get('posterPath')
    status = data.get('mediaInfo', {}).get('status', 1)
    requests = data.get('mediaInfo', {}).get('requests', [])

    if media_type == "tv":
        available = (status == 5 or status == 4)
    else:
        available = (status == 5)

    requested = any(r['status'] in [1, 2] for r in requests)

    if available:
        xbmcgui.Dialog().ok('KodiSeerr', f'"{title}" is already available!')
        return

    if requested:
        xbmcgui.Dialog().ok('KodiSeerr', f'"{title}" is already requested!')
        return

    if xbmcgui.Dialog().yesno('KodiSeerr', f'Request "{title}"?'):
        request_item(media_type, id)

def request_item(media_type, id):
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
    req = urllib.request.Request(
        f"{jellyseerr_url}/api/v1/request",
        data=json.dumps(payload).encode('utf-8'),
        method="POST"
    )
    req.add_header('Content-Type', 'application/json')
    try:
        with opener.open(req, timeout=10):
            xbmcgui.Dialog().notification('KodiSeerr', 'Request Sent!', xbmcgui.NOTIFICATION_INFO, 3000)
    except Exception as e:
        xbmcgui.Dialog().notification('KodiSeerr', f'Request Failed: {str(e)}', xbmcgui.NOTIFICATION_ERROR, 4000)


def search():
    keyboard = xbmcgui.Dialog().input('Search for Movie or TV Show')
    if keyboard:
        data = get_api('/search', params={'query': keyboard})
        results = data.get('results', [])
        for item in results:
            media_type = item.get('mediaType', 'movie')
            title = item.get('title') or item.get('name')
            release_date = item.get('releaseDate') or item.get('firstAirDate')
            if release_date:
                year = release_date.split("-")[0]
                title = f"{title} ({year})"
            plot = item.get('overview') or ""
            poster = item.get('posterPath')
            id = item.get('id')

            url = build_url({'mode': 'details', 'type': media_type, 'id': id})

            list_item = xbmcgui.ListItem(label=title)
            info = list_item.getVideoInfoTag()
            info.setTitle(title)
            info.setPlot(plot)

            if poster:
                art_url = image_base + poster
                list_item.setArt({'thumb': art_url, 'poster': art_url, 'fanart': art_url})

            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)

        xbmcplugin.endOfDirectory(addon_handle)


# Routing
mode = args.get('mode')
if not mode:
    list_main_menu()
elif mode == "trending_movies":
    data = get_api("/discover/trending")
    list_items([i for i in data.get('results', []) if i.get('mediaType') == 'movie'], "movie")
elif mode == "trending_tv":
    data = get_api("/discover/trending")
    list_items([i for i in data.get('results', []) if i.get('mediaType') == 'tv'], "tv")
elif mode == "popular_movies":
    data = get_api("/discover/movies?sortBy=popularity.desc")
    list_items(data.get('results', []), "movie")
elif mode == "popular_tv":
    data = get_api("/discover/tv?sortBy=popularity.desc")
    list_items(data.get('results', []), "tv")
elif mode == "upcoming_movies":
    data = get_api("/discover/movies?sortBy=releaseDate.desc")
    list_items(data.get('results', []), "movie")
elif mode == "upcoming_tv":
    data = get_api("/discover/tv?sortBy=firstAirDate.desc")
    list_items(data.get('results', []), "tv")
elif mode == "search":
    search()
elif mode == "details":
    show_details(args.get('type'), args.get('id'))
