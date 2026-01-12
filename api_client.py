import xbmcaddon
from jellyseerr_api import JellyseerrClient

addon = xbmcaddon.Addon()
url = addon.getSetting("jellyseerr_url").rstrip("/")
username = addon.getSetting("jellyseerr_username")
password = addon.getSetting("jellyseerr_password")

client = JellyseerrClient(url, username, password)
