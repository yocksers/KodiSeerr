import urllib.request
import urllib.error
import http.cookiejar
import ssl
import xbmcaddon
import xbmc
import json
from urllib.parse import urlencode

class JellyseerrClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = None  # Will be initialized with SSL context
        self.logged_in = False

    def init_opener(self):
        """Initializes the opener with SSL context based on addon settings."""
        addon = xbmcaddon.Addon()
        allow_self_signed = addon.getSettingBool("allow_self_signed")

        if allow_self_signed:
            ssl_context = ssl._create_unverified_context()
        else:
            ssl_context = ssl.create_default_context()

        https_handler = urllib.request.HTTPSHandler(context=ssl_context)
        cookie_handler = urllib.request.HTTPCookieProcessor(self.cookie_jar)
        self.opener = urllib.request.build_opener(https_handler, cookie_handler)

    def login(self):
        """Logs into the Jellyseerr/Overseerr instance."""
        if self.logged_in:
            return

        self.init_opener()

        login_url = f"{self.base_url}/api/v1/auth/local"
        data = json.dumps({
            "email": self.username,
            "password": self.password
        }).encode('utf-8')

        req = urllib.request.Request(login_url, data=data)
        req.add_header("Content-Type", "application/json")

        try:
            with self.opener.open(req) as resp:
                resp.read()
            self.logged_in = True
        except urllib.error.URLError as e:
            xbmc.log(f"[kodiseerr] Login failed: {e}", xbmc.LOGERROR)

    def api_request(self, endpoint, method="GET", data=None, params=None):
        """Sends an authenticated API request to the server."""
        if not self.logged_in:
            self.login()

        if not self.opener:
            self.init_opener()

        url = f"{self.base_url}/api/v1{endpoint}"
        if params:
            url += '?' + urlencode(params)

        if data is not None:
            data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        if method == "POST":
            req.add_header("Content-Type", "application/json")

        try:
            with self.opener.open(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.URLError as e:
            xbmc.log(f"[kodiseerr] API request failed: {e}", xbmc.LOGERROR)
            return None
