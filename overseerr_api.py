
import urllib.request, json, http.cookiejar

class OverseerrClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))

    def get(self, path):
        try:
            req = urllib.request.Request(self.base_url + path)
            with self.opener.open(req) as response:
                return json.load(response)
        except:
            return None

    def login(self):
        if not self.username or not self.password:
            return
        try:
            data = json.dumps({"email": self.username, "password": self.password}).encode()
            req = urllib.request.Request(self.base_url + "/auth/local", data=data,
                                         headers={"Content-Type": "application/json"})
            self.opener.open(req)
        except:
            pass
