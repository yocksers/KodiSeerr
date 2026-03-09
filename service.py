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
        if os.path.exists(notified_file):
            with open(notified_file, 'r') as f:
                notified_data = json.load(f)
                # Upgrade old format if needed
                if isinstance(notified_data, list):
                    notified_ids = {str(id): {'status': 5} for id in notified_data}
                else:
                    notified_ids = notified_data
        else:
            notified_ids = {}
    except Exception:
        import traceback
        traceback.print_exc()
        notified_ids = {}

    while not monitor.abortRequested():
        if addon.getSettingBool('enable_request_notifications'):
            try:
                requests_data = api_client.client.api_request('/request')
            except Exception:
                import traceback
                traceback.print_exc()
                xbmc.log("[KodiSeerr Service] Fetch requests failed", xbmc.LOGERROR)
                requests_data = None
            
            if requests_data:
                items = requests_data.get('results', []) if isinstance(requests_data, dict) else []
                for item in items:
                    media = item.get('media') or {}
                    media_status = media.get('status', 1)
                    title = media.get('title') or media.get('name') or "Media"
                    media_id = str(media.get('tmdbId') or media.get('id') or "")

                    if media_id:
                        # Get previous status
                        previous_data = notified_ids.get(media_id, {})
                        previous_status = previous_data.get('status', 0)
                        
                        # Notify on status changes
                        if media_status == 5 and previous_status != 5:
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} is now available!', xbmcgui.NOTIFICATION_INFO, 5000)
                            notified_ids[media_id] = {'status': 5, 'title': title}
                        elif media_status == 3 and previous_status != 3 and addon.getSettingBool('notify_processing'):
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} is now processing', xbmcgui.NOTIFICATION_INFO, 4000)
                            notified_ids[media_id] = {'status': 3, 'title': title}
                        elif media_status == 2 and previous_status != 2 and addon.getSettingBool('notify_approved'):
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} request approved', xbmcgui.NOTIFICATION_INFO, 4000)
                            notified_ids[media_id] = {'status': 2, 'title': title}
                        elif media_status != previous_status and media_id not in notified_ids:
                            notified_ids[media_id] = {'status': media_status, 'title': title}

                    with open(notified_file, 'w') as f:
                        json.dump(notified_ids, f)

        if monitor.waitForAbort(get_interval()):
            break

if __name__ == '__main__':
    main_loop()
