import urllib.request
import http.cookiejar
import json

class JellyseerrClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.logged_in = False

    def login(self):
        if self.logged_in:
            return
        login_url = f"{self.base_url}/api/v1/auth/local"
        data = json.dumps({"email": self.username, "password": self.password}).encode('utf-8')
        req = urllib.request.Request(login_url, data=data)
        req.add_header("Content-Type", "application/json")
        with self.opener.open(req) as resp:
            resp.read()
        self.logged_in = True

    def api_request(self, endpoint, method="GET", data=None, params=None):
        if not self.logged_in:
            self.login()
        url = f"{self.base_url}/api/v1{endpoint}"
        if params:
            from urllib.parse import urlencode
            url += '?' + urlencode(params)
        if data is not None:
            data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        if method == "POST":
            req.add_header("Content-Type", "application/json")
        with self.opener.open(req) as resp:
            return json.loads(resp.read().decode())
