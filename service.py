import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import json
import api_client
import os

addon = xbmcaddon.Addon()
monitor = xbmc.Monitor()

def get_interval():
    try:
        interval = int(addon.getSetting('polling_interval'))
        return max(60, interval)
    except Exception:
        import traceback
        traceback.print_exc()
        return 300

def main_loop():
    data_path = xbmcvfs.translatePath(f"special://profile/addon_data/{addon.getAddonInfo('id')}/")
    os.makedirs(data_path, exist_ok=True)
    notified_file = os.path.join(data_path, "notified_requests.json")
    try:
        with open(notified_file, 'r') as f:
            notified_ids = set(json.load(f))
    except Exception:
        import traceback
        traceback.print_exc()
        notified_ids = set()

    while not monitor.abortRequested():
        if addon.getSettingBool('enable_request_notifications'):
            try:
                requests_data = api_client.client.api_request('/request')
            except Exception:
                import traceback
                traceback.print_exc()
                xbmc.log("[KodiSeerr Service] Fetch requests failed", xbmc.LOGERROR)
            else:
                items = requests_data.get('results', []) if isinstance(requests_data, dict) else []
                for item in items:
                    media = item.get('media') or {}
                    media_status = media.get('status', 1)
                    title = media.get('title') or media.get('name') or "Media"
                    media_id = str(media.get('tmdbId') or media.get('id') or "")

                    if media_status == 5 and media_id and media_id not in notified_ids:
                        xbmcgui.Dialog().notification('KodiSeerr', f'{title} is now available!', xbmcgui.NOTIFICATION_INFO)
                        notified_ids.add(media_id)

                with open(notified_file, 'w') as f:
                    json.dump(list(notified_ids), f)

        if monitor.waitForAbort(get_interval()):
            break

if __name__ == '__main__':
    main_loop()
