import xbmcaddon
import xbmcvfs

addon = None
addon_handle = None
base_url = None
args = None
image_base = "https://image.tmdb.org/t/p/w500"
enable_ask_4k = False
favorites_path = None
preferences_path = None


def init(argv):
    global addon, addon_handle, base_url, args, enable_ask_4k, favorites_path, preferences_path
    import urllib.parse
    addon = xbmcaddon.Addon()
    addon_handle = int(argv[1])
    base_url = argv[0]
    args = dict(urllib.parse.parse_qsl(argv[2][1:]))
    enable_ask_4k = addon.getSettingBool('enable_ask_4k')
    addon_id = addon.getAddonInfo('id')
    favorites_path = xbmcvfs.translatePath(f"special://profile/addon_data/{addon_id}/favorites.json")
    preferences_path = xbmcvfs.translatePath(f"special://profile/addon_data/{addon_id}/preferences.json")
