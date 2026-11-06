import json
import os
import xbmc

_FAVORITES_FILE = 'favorites.json'
_PREFERENCES_FILE = 'preferences.json'


def load_favorites():
    import users
    path = users.data_path(_FAVORITES_FILE)
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {k: {} for k in data}
                if isinstance(data, dict):
                    return data
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Favorites load error: {e}", xbmc.LOGERROR)
    return {}


def save_favorites(favorites):
    import users
    path = users.data_path(_FAVORITES_FILE)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(favorites, f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Favorites save error: {e}", xbmc.LOGERROR)


def load_search_history():
    prefs = load_preferences()
    return prefs.get('search_history', [])


def save_to_search_history(query):
    prefs = load_preferences()
    history = prefs.get('search_history', [])
    if query in history:
        history.remove(query)
    history.insert(0, query)
    prefs['search_history'] = history[:20]
    save_preferences(prefs)


def clear_search_history():
    prefs = load_preferences()
    prefs['search_history'] = []
    save_preferences(prefs)


def load_preferences():
    import users
    path = users.data_path(_PREFERENCES_FILE)
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Preferences load error: {e}", xbmc.LOGERROR)
    return {}


def save_preferences(prefs):
    import users
    path = users.data_path(_PREFERENCES_FILE)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(prefs, f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Preferences save error: {e}", xbmc.LOGERROR)
