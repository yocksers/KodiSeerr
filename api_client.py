import xbmcaddon
from jellyseerr_api import JellyseerrClient

addon = xbmcaddon.Addon()
url = addon.getSetting("jellyseerr_url").rstrip("/")
username = addon.getSetting("jellyseerr_username")
password = addon.getSetting("jellyseerr_password")
api_token = addon.getSetting("jellyseerr_api_token")
auth_method = addon.getSetting("auth_method")

if not auth_method:
    auth_method = "password"

client = JellyseerrClient(url, username, password, api_token, auth_method)
