import requests
import xbmcaddon
import xbmc

class SeerrClient:
    def __init__(self, base_url, username, password, api_token=None, auth_method="password"):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.api_token = api_token
        self.auth_method = auth_method
        self.logged_in = False
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self._init_session()

    def _init_session(self):
        addon = xbmcaddon.Addon()
        if addon.getSettingBool("allow_self_signed"):
            self.session.verify = False
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            except Exception:
                pass
        else:
            self.session.verify = True

    def close(self):
        self.session.close()

    def login(self):
        if self.logged_in:
            return True

        if self.auth_method == "api_token":
            if not self.api_token:
                xbmc.log(f"[kodiseerr] API token authentication selected but no token provided", xbmc.LOGERROR)
                return False
            self.session.headers.update({"X-Api-Key": self.api_token})
            self.logged_in = True
            return True

        login_url = f"{self.base_url}/api/v1/auth/jellyfin"
        try:
            resp = self.session.post(
                login_url,
                json={"username": self.username, "password": self.password},
                timeout=15
            )
            resp.raise_for_status()
            xbmc.log(f"[kodiseerr] Login successful", xbmc.LOGDEBUG)
            self.logged_in = True
            return True
        except requests.HTTPError as e:
            xbmc.log(f"[kodiseerr] Login failed: {e.response.status_code} {e.response.reason}", xbmc.LOGERROR)
            return False
        except requests.RequestException as e:
            xbmc.log(f"[kodiseerr] Login failed: {e}", xbmc.LOGERROR)
            return False

    def api_request(self, endpoint, method="GET", data=None, params=None):
        if not self.logged_in:
            if not self.login():
                xbmc.log(f"[kodiseerr] Cannot make API request - login failed", xbmc.LOGERROR)
                return None

        url = f"{self.base_url}/api/v1{endpoint}"
        try:
            resp = self.session.request(method, url, json=data, params=params, timeout=15)
            if resp.status_code == 401 and self.logged_in:
                xbmc.log(f"[kodiseerr] Got 401, retrying login", xbmc.LOGDEBUG)
                self.logged_in = False
                self.session.headers.pop("X-Api-Key", None)
                if self.login():
                    resp = self.session.request(method, url, json=data, params=params, timeout=15)
                else:
                    return None
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            xbmc.log(f"[kodiseerr] API request failed: {e.response.status_code} {e.response.reason}", xbmc.LOGERROR)
            return None
        except requests.RequestException as e:
            xbmc.log(f"[kodiseerr] API request failed: {e}", xbmc.LOGERROR)
            return None
