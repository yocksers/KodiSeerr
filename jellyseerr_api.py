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
        self.opener = None
        self.logged_in = False
        self.init_opener()

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
        """Logs into the Jellyseerr instance."""
        if self.logged_in:
            return True

        # Jellyseerr with Jellyfin authentication
        login_url = f"{self.base_url}/api/v1/auth/jellyfin"
        data = json.dumps({
            "username": self.username,
            "password": self.password
        }).encode('utf-8')

        req = urllib.request.Request(login_url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")

        try:
            with self.opener.open(req) as resp:
                response_data = json.loads(resp.read().decode())
                xbmc.log(f"[kodiseerr] Login successful, cookies: {len(self.cookie_jar)}", xbmc.LOGDEBUG)
            self.logged_in = True
            return True
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            xbmc.log(f"[kodiseerr] Login failed: {e.code} {e.reason} - {error_body}", xbmc.LOGERROR)
            return False
        except urllib.error.URLError as e:
            xbmc.log(f"[kodiseerr] Login failed: {e.reason}", xbmc.LOGERROR)
            return False

    def api_request(self, endpoint, method="GET", data=None, params=None):
        """Sends an authenticated API request to the server."""
        if not self.logged_in:
            if not self.login():
                xbmc.log(f"[kodiseerr] Cannot make API request - login failed", xbmc.LOGERROR)
                return None

        url = f"{self.base_url}/api/v1{endpoint}"
        if params:
            safe_params = {k: str(v) for k, v in params.items()}
            url += '?' + urlencode(safe_params)

        if data is not None:
            data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        if method == "POST":
            req.add_header("Content-Type", "application/json")

        try:
            with self.opener.open(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            # If we get 401, try to login again once
            if e.code == 401 and self.logged_in:
                xbmc.log(f"[kodiseerr] Got 401, retrying login", xbmc.LOGDEBUG)
                self.logged_in = False
                if self.login():
                    # Retry the request
                    try:
                        req = urllib.request.Request(url, data=data, method=method)
                        req.add_header("Accept", "application/json")
                        if method == "POST":
                            req.add_header("Content-Type", "application/json")
                        with self.opener.open(req) as resp:
                            return json.loads(resp.read().decode())
                    except Exception as retry_e:
                        xbmc.log(f"[kodiseerr] Retry failed: {retry_e}", xbmc.LOGERROR)
                        return None
            error_body = e.read().decode() if e.fp else ""
            xbmc.log(f"[kodiseerr] API request failed: {e.code} {e.reason} - {error_body}", xbmc.LOGERROR)
            return None
        except urllib.error.URLError as e:
            xbmc.log(f"[kodiseerr] API request failed: {e.reason}", xbmc.LOGERROR)
            return None
