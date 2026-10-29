"""Run with python -m unittest discover -s tests; no Kodi or network required."""
import importlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ADDON = Path(__file__).resolve().parents[1] / 'plugin.video.kodiseerr'


class ProfileIsolationTests(unittest.TestCase):
    def setUp(self):
        self.settings = dict(seerr_url='http://example.test', seerr_username='alice',
                             seerr_password='secret', seerr_api_token='',
                             use_api_token='false', use_local_auth='false',
                             allow_self_signed='false', enable_caching='true', cache_duration='30')
        self.profile = '/profiles/alice/'
        self.properties = {}
        owner = self

        class Addon:
            def getSetting(self, key): return owner.settings.get(key, '')
            def getSettingBool(self, key): return self.getSetting(key) == 'true'
            def getSettingInt(self, key): return int(self.getSetting(key) or 0)

        class Window:
            def __init__(self, *args): pass
            def getProperty(self, key): return owner.properties.get(key, '')
            def setProperty(self, key, value): owner.properties[key] = value

        class Session:
            def __init__(self): self.headers, self.cookies = {}, {}
            def close(self): pass

        stubs = {
            'xbmcaddon': types.SimpleNamespace(Addon=lambda *args: Addon()),
            'xbmcvfs': types.SimpleNamespace(translatePath=lambda _: owner.profile),
            'xbmcgui': types.SimpleNamespace(Window=Window),
            'xbmc': types.SimpleNamespace(log=lambda *args: None, LOGERROR=4, LOGDEBUG=0),
            'requests': types.SimpleNamespace(Session=Session, utils=types.SimpleNamespace(
                cookiejar_from_dict=dict, dict_from_cookiejar=dict)),
        }
        self.modules = patch.dict(sys.modules, stubs)
        self.modules.start()
        self.addCleanup(self.modules.stop)
        sys.path.insert(0, str(ADDON))
        self.addCleanup(lambda: sys.path.remove(str(ADDON)))
        for name in ('cache', 'api_client', 'seerr_api'): sys.modules.pop(name, None)
        self.cache = importlib.import_module('cache')
        self.api = importlib.import_module('api_client')

    def switch(self):
        self.profile = '/profiles/bob/'
        self.settings['seerr_username'] = 'bob'

    def test_profile_data_and_cookie_isolation(self):
        self.cache.set_cached('requests', ['alice'])
        self.cache.set_cached('seerr_session_cookies', 'alice-cookie')
        self.switch()
        self.assertIsNone(self.cache.get_cached('requests'))
        self.assertIsNone(self.cache.get_cached('seerr_session_cookies'))
        self.cache.set_cached('requests', ['bob'])
        self.profile = '/profiles/alice/'
        self.settings['seerr_username'] = 'alice'
        self.assertEqual(self.cache.get_cached('requests'), ['alice'])
        self.cache.clear()
        self.switch()
        self.assertEqual(self.cache.get_cached('requests'), ['bob'])

    def test_account_changes_invalidate_cache(self):
        for field, value in [('seerr_url', 'http://other.test'), ('seerr_username', 'bob'),
                             ('seerr_password', 'new'), ('seerr_api_token', 'new-token'),
                             ('use_api_token', 'true'), ('use_local_auth', 'true')]:
            with self.subTest(field=field):
                previous = self.settings[field]
                self.cache.set_cached('requests', ['old'])
                self.settings[field] = value
                self.assertIsNone(self.cache.get_cached('requests'))
                self.settings[field] = previous

    def test_client_switches_immediately_and_cookies_stay_bound(self):
        alice = self.api.get_client()
        alice.session.cookies['session'] = 'alice'
        alice._save_cookies()
        self.switch()
        bob = self.api.get_client()
        self.assertIsNot(alice, bob)
        self.assertFalse(bob.logged_in)
        self.assertEqual(bob.session.cookies, {})
        # A response from an old client must not save into the new account's scope.
        alice._save_cookies()
        self.assertIsNone(self.cache.get_cached('seerr_session_cookies'))
        self.profile = '/profiles/alice/'
        self.settings['seerr_username'] = 'alice'
        again = self.api.get_client()
        self.assertTrue(again.logged_in)
        self.assertEqual(again.session.cookies['session'], 'alice')

    def test_profile_change_with_same_credentials_replaces_client(self):
        first = self.api.get_client()
        self.profile = '/profiles/other/'
        self.assertIsNot(first, self.api.get_client())

    def test_expiry_disabled_and_corrupt_cache(self):
        self.cache.set_cached('entry', 'value')
        with patch.object(self.cache.time, 'time', return_value=10**12):
            self.assertIsNone(self.cache.get_cached('entry'))
            self.cache.clean_cache()
        self.assertIsNone(self.cache.get_cached('entry'))
        self.settings['enable_caching'] = 'false'
        self.cache.set_cached('entry', 'value')
        self.assertIsNone(self.cache.get_cached('entry'))
        self.settings['enable_caching'] = 'true'
        self.properties[self.cache._CACHE_PROPERTY + self.cache.get_scope()] = 'invalid json'
        self.assertIsNone(self.cache.get_cached('entry'))


if __name__ == '__main__':
    unittest.main()
