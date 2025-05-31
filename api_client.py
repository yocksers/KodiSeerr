import xbmcaddon
from jellyseerr_api import JellyseerrClient
from overseerr_api import OverseerrClient  # (Assumes you want to add Overseerr support later)

addon = xbmcaddon.Addon()
service = addon.getSetting("api_service")
url = addon.getSetting("jellyseerr_url").rstrip("/")
username = addon.getSetting("jellyseerr_username")
password = addon.getSetting("jellyseerr_password")

if service == "1":
    client = OverseerrClient(url, username, password)
else:
    client = JellyseerrClient(url, username, password)
