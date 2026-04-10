import json
import os
import xbmc


def load_favorites():
    import context
    try:
        if os.path.exists(context.favorites_path):
            with open(context.favorites_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {k: {} for k in data}
                if isinstance(data, dict):
                    return data
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Favorites load error: {e}", xbmc.LOGERROR)
    return {}


def save_favorites(favorites):
    import context
    try:
        os.makedirs(os.path.dirname(context.favorites_path), exist_ok=True)
        with open(context.favorites_path, 'w') as f:
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
    import context
    try:
        if os.path.exists(context.preferences_path):
            with open(context.preferences_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Preferences load error: {e}", xbmc.LOGERROR)
    return {}


def save_preferences(prefs):
    import context
    try:
        os.makedirs(os.path.dirname(context.preferences_path), exist_ok=True)
        with open(context.preferences_path, 'w') as f:
            json.dump(prefs, f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Preferences save error: {e}", xbmc.LOGERROR)
