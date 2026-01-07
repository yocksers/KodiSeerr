import urllib.request
import urllib.error
import http.cookiejar
import ssl
import json
import xbmcaddon
import xbmc

class OverseerrClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = None  # Will be initialized with SSL context

        self.init_opener()

    def init_opener(self):
        """Initializes the opener with SSL context based on addon settings."""
        addon = xbmcaddon.Addon('plugin.video.kodiseerr')
        allow_self_signed = addon.getSettingBool("allow_self_signed")

        if allow_self_signed:
            ssl_context = ssl._create_unverified_context()
        else:
            ssl_context = ssl.create_default_context()

        https_handler = urllib.request.HTTPSHandler(context=ssl_context)
        cookie_handler = urllib.request.HTTPCookieProcessor(self.cookie_jar)
        self.opener = urllib.request.build_opener(https_handler, cookie_handler)

    def login(self):
        """Logs into the Overseerr server using local auth."""
        if not self.username or not self.password:
            return

        login_url = self.base_url + "/auth/local"
        data = json.dumps({
            "email": self.username,
            "password": self.password
        }).encode()

        req = urllib.request.Request(login_url, data=data, headers={
            "Content-Type": "application/json"
        })

        try:
            self.opener.open(req)
        except urllib.error.URLError as e:
            xbmc.log(f"[kodiseerr] Overseerr login failed: {e}", xbmc.LOGERROR)

    def get(self, path):
        """Performs a GET request to the Overseerr API."""
        try:
            req = urllib.request.Request(self.base_url + path)
            with self.opener.open(req) as response:
                return json.load(response)
        except urllib.error.URLError as e:
            xbmc.log(f"[kodiseerr] Overseerr GET request failed: {e}", xbmc.LOGERROR)
            return None
