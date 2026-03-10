import json
import os
import xbmc


def load_favorites():
    import context
    try:
        if os.path.exists(context.favorites_path):
            with open(context.favorites_path, 'r') as f:
                return set(json.load(f))
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Favorites load error: {e}", xbmc.LOGERROR)
    return set()


def save_favorites(favorites):
    import context
    try:
        os.makedirs(os.path.dirname(context.favorites_path), exist_ok=True)
        with open(context.favorites_path, 'w') as f:
            json.dump(list(favorites), f)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Favorites save error: {e}", xbmc.LOGERROR)


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
