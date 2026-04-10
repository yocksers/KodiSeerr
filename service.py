import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import json
import api_client
import os

addon = xbmcaddon.Addon()
monitor = xbmc.Monitor()

_IMAGE_BASE = "https://image.tmdb.org/t/p/w92"


def get_interval():
    try:
        interval = int(addon.getSetting('polling_interval'))
        return max(60, interval)
    except Exception:
        return 300


def _get_poster(media):
    path = media.get('posterPath')
    if path:
        return _IMAGE_BASE + path
    return xbmcgui.NOTIFICATION_INFO


def main_loop():
    data_path = xbmcvfs.translatePath(f"special://profile/addon_data/{addon.getAddonInfo('id')}/")
    os.makedirs(data_path, exist_ok=True)
    notified_file = os.path.join(data_path, "notified_requests.json")
    try:
        if os.path.exists(notified_file):
            with open(notified_file, 'r') as f:
                raw = json.load(f)
                if isinstance(raw, list):
                    notified_media = {str(i): {'status': 5} for i in raw}
                    notified_declined = []
                elif isinstance(raw, dict) and 'media' in raw:
                    notified_media = raw.get('media', {})
                    notified_declined = raw.get('declined', [])
                else:
                    notified_media = raw
                    notified_declined = []
        else:
            notified_media = {}
            notified_declined = []
    except Exception:
        import traceback
        traceback.print_exc()
        notified_media = {}
        notified_declined = []

    interval = get_interval()

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
                    request_status = item.get('status', 1)
                    title = media.get('title') or media.get('name') or "Media"
                    media_id = str(media.get('tmdbId') or media.get('id') or "")
                    request_id = str(item.get('id') or "")
                    poster = _get_poster(media)

                    if request_status == 3 and request_id and request_id not in notified_declined:
                        if addon.getSettingBool('notify_declined'):
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} request was declined', xbmcgui.NOTIFICATION_WARNING, 5000, poster)
                        notified_declined.append(request_id)

                    if media_id:
                        previous_data = notified_media.get(media_id, {})
                        previous_status = previous_data.get('status', 0)

                        if media_status == 5 and previous_status != 5:
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} is now available!', xbmcgui.NOTIFICATION_INFO, 5000, poster)
                            notified_media[media_id] = {'status': 5, 'title': title}
                        elif media_status == 3 and previous_status != 3 and addon.getSettingBool('notify_processing'):
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} is now processing', xbmcgui.NOTIFICATION_INFO, 4000, poster)
                            notified_media[media_id] = {'status': 3, 'title': title}
                        elif media_status == 2 and previous_status != 2 and addon.getSettingBool('notify_approved'):
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} request approved', xbmcgui.NOTIFICATION_INFO, 4000, poster)
                            notified_media[media_id] = {'status': 2, 'title': title}
                        elif media_status != previous_status and media_id not in notified_media:
                            notified_media[media_id] = {'status': media_status, 'title': title}

                with open(notified_file, 'w') as f:
                    json.dump({'media': notified_media, 'declined': notified_declined}, f)

        if monitor.waitForAbort(interval):
            break
        interval = get_interval()


if __name__ == '__main__':
    main_loop()
