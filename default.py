
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

image_base = "https://image.tmdb.org/t/p/w500"

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def login():
    login_url = f"{jellyseerr_url}/api/v1/auth/local"
    payload = json.dumps({"email": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(login_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        xbmcgui.Dialog().notification("KodiSeerr", f"Login error: {e}", xbmcgui.NOTIFICATION_ERROR, 3000)
        return False

def get_api(endpoint, params=None):
    if not any(cookie.name == "connect.sid" for cookie in cookie_jar):
        if not login():
            return {}
    url = f"{jellyseerr_url}/api/v1{endpoint}"
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    try:
        with opener.open(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        xbmcgui.Dialog().notification("KodiSeerr", f"API error: {e}", xbmcgui.NOTIFICATION_ERROR, 3000)
        return {}

def list_main_menu():
    for label, mode in [
        ("Trending Movies", "trending_movies"),
        ("Trending TV Shows", "trending_tv"),
        ("Popular Movies", "popular_movies"),
        ("Popular TV Shows", "popular_tv"),
        ("Search", "search"),
        ("📋 Request Progress", "requests")
    ]:
        url = build_url({"mode": mode})
        xbmcplugin.addDirectoryItem(addon_handle, url, xbmcgui.ListItem(label), True)
    xbmcplugin.endOfDirectory(addon_handle)

def list_items(items, media_type):
    for item in items:
        title = item.get("title") or item.get("name")
        plot = item.get("overview") or ""
        poster = item.get("posterPath")
        id = item.get("id")
        url = build_url({"mode": "details", "type": media_type, "id": id})
        list_item = xbmcgui.ListItem(label=title)
        list_item.setInfo("video", {"title": title, "plot": plot})
        if poster:
            art_url = image_base + poster
            list_item.setArt({"thumb": art_url, "poster": art_url, "fanart": art_url})
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(addon_handle)

def list_requests():
    data = get_api("/request")
    results = data.get("results", [])
    results.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

    for item in results:
        media_info = item.get("media") or {}
        title = media_info.get("title") or media_info.get("name")
        poster = media_info.get("posterPath")
        status = item.get("status", 0)
        media_type = media_info.get("mediaType")
        tmdb_id = media_info.get("tmdbId")

        # Fetch fallback title if missing
        if not title and media_type and tmdb_id:
            fetched = get_api(f"/{media_type}/{tmdb_id}")
            title = fetched.get("title") or fetched.get("name")

        title = title or "Unknown Title"

        status_icon = {
            1: "🕐 Pending",
            2: "✅ Approved",
            3: "⏳ Processing",
            4: "🎉 Available",
            5: "🎉 Available"
        }.get(status, "❓ Unknown")

        label = f"{status_icon} {title}"
        list_item = xbmcgui.ListItem(label=label)
        list_item.setInfo("video", {"title": title})
        if poster:
            full_poster = image_base + poster
            list_item.setArt({"thumb": full_poster, "poster": full_poster, "fanart": full_poster})
        xbmcplugin.addDirectoryItem(addon_handle, "", list_item, False)

    xbmcplugin.endOfDirectory(addon_handle)



def show_request_filters():
    for label, filter_value in [
        ("📋 All Requests", "all"),
        ("🕐 Pending", "pending"),
        ("✅ Approved", "approved"),
        ("🎉 Available", "available")
    ]:
        url = build_url({"mode": "requests_list", "filter": filter_value})
        xbmcplugin.addDirectoryItem(addon_handle, url, xbmcgui.ListItem(label), True)
    xbmcplugin.endOfDirectory(addon_handle)

def list_requests(filter_status=None):
    data = get_api("/request")
    results = data.get("results", [])
    results.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

    for item in results:
        media_info = item.get("media") or {}
        title = media_info.get("title") or media_info.get("name")
        poster = media_info.get("posterPath")
        status = item.get("status", 0)
        media_type = media_info.get("mediaType")
        tmdb_id = media_info.get("tmdbId")

        # Fetch fallback title if missing
        if not title and media_type and tmdb_id:
            fetched = get_api(f"/{media_type}/{tmdb_id}")
            title = fetched.get("title") or fetched.get("name")

        title = title or "Unknown Title"

        if filter_status:
            if filter_status == "pending" and status != 1:
                continue
            if filter_status == "approved" and status != 2:
                continue
            if filter_status == "available" and status not in [4,5]:
                continue

        status_icon = {
            1: "🕐 Pending",
            2: "✅ Approved",
            3: "⏳ Processing",
            4: "🎉 Available",
            5: "🎉 Available"
        }.get(status, "❓ Unknown")

        label = f"{status_icon} {title}"
        list_item = xbmcgui.ListItem(label=label)
        list_item.setInfo("video", {"title": title})
        if poster:
            full_poster = image_base + poster
            list_item.setArt({"thumb": full_poster, "poster": full_poster, "fanart": full_poster})
        xbmcplugin.addDirectoryItem(addon_handle, "", list_item, False)

    xbmcplugin.endOfDirectory(addon_handle)


def show_details(media_type, id):
    data = get_api(f"/{media_type}/{id}")
    title = data.get("title") or data.get("name")
    overview = data.get("overview") or ""
    poster = data.get("posterPath")
    status = data.get("mediaInfo", {}).get("status", 1)
    requests = data.get("mediaInfo", {}).get("requests", [])
    available = (status == 5)
    requested = any(r["status"] in [1, 2] for r in requests)
    li = xbmcgui.ListItem(label=title)
    li.setInfo("video", {"title": title, "plot": overview})
    if poster:
        art_url = image_base + poster
        li.setArt({"thumb": art_url, "poster": art_url, "fanart": art_url})
    if available:
        xbmcgui.Dialog().ok("KodiSeerr", "Already Available!")
    elif requested:
        xbmcgui.Dialog().ok("KodiSeerr", "Already Requested!")
    else:
        if xbmcgui.Dialog().yesno("KodiSeerr", f'Request "{title}"?'):
            request_item(media_type, id)

def request_item(media_type, id):
    payload = {"mediaType": media_type, "mediaId": int(id), "is4k": False}
    if media_type == "tv":
        payload["seasons"] = "all"
    req = urllib.request.Request(
        f"{jellyseerr_url}/api/v1/request",
        data=json.dumps(payload).encode("utf-8"),
        method="POST"
    )
    req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req, timeout=10):
            xbmcgui.Dialog().notification("KodiSeerr", "Request Sent!", xbmcgui.NOTIFICATION_INFO, 3000)
    except Exception as e:
        xbmcgui.Dialog().notification("KodiSeerr", f"Request failed: {e}", xbmcgui.NOTIFICATION_ERROR, 4000)

def search():
    query = xbmcgui.Dialog().input("Search for Movie or TV Show")
    if query:
        data = get_api("/search", params={"query": query})
        list_items(data.get("results", []), media_type="movie")

mode = args.get("mode")
if not mode:
    list_main_menu()
elif mode == "trending_movies":
    data = get_api("/discover/trending")
    list_items([i for i in data.get("results", []) if i.get("mediaType") == "movie"], "movie")
elif mode == "trending_tv":
    data = get_api("/discover/trending")
    list_items([i for i in data.get("results", []) if i.get("mediaType") == "tv"], "tv")
elif mode == "popular_movies":
    data = get_api("/discover/movies?sortBy=popularity.desc")
    list_items(data.get("results", []), "movie")
elif mode == "popular_tv":
    data = get_api("/discover/tv?sortBy=popularity.desc")
    list_items(data.get("results", []), "tv")
elif mode == "search":
    search()
elif mode == "details":
    show_details(args.get("type"), args.get("id"))

elif mode == "requests":
    show_request_filters()
elif mode == "requests_list":
    list_requests(args.get('filter'))

