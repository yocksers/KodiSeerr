import xbmc
import xbmcaddon
import xbmcgui
import json
import api_client
import users
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


def _load_notified(notified_file):
    try:
        if os.path.exists(notified_file):
            with open(notified_file, 'r') as f:
                raw = json.load(f)
                if isinstance(raw, list):
                    return {str(i): {'status': 5} for i in raw}, [], False
                elif isinstance(raw, dict) and 'media' in raw:
                    return raw.get('media', {}), raw.get('declined', []), False
                else:
                    return raw, [], False
        return {}, [], True
    except Exception:
        import traceback
        traceback.print_exc()
        return {}, [], False


def main_loop():
    users.purge_legacy_password()
    notified_file = None
    notified_media = {}
    notified_declined = []
    silent = False

    interval = get_interval()

    while not monitor.abortRequested():
        signed_in = users.uses_api_token() or users.active_user()
        if signed_in and addon.getSettingBool('enable_request_notifications'):
            current_file = users.data_path("notified_requests.json")
            if current_file != notified_file:
                notified_file = current_file
                notified_media, notified_declined, silent = _load_notified(notified_file)
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

                    if silent:
                        if request_status == 3 and request_id and request_id not in notified_declined:
                            notified_declined.append(request_id)
                        if media_id:
                            notified_media[media_id] = {'status': media_status, 'title': title}
                        continue

                    if request_status == 3 and request_id and request_id not in notified_declined:
                        if addon.getSettingBool('notify_declined'):
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} request was declined', xbmcgui.NOTIFICATION_WARNING, 5000)
                        notified_declined.append(request_id)

                    if media_id:
                        previous_data = notified_media.get(media_id, {})
                        previous_status = previous_data.get('status', 0)

                        if media_status == 5 and previous_status != 5:
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} is now available!', xbmcgui.NOTIFICATION_INFO, 5000)
                            notified_media[media_id] = {'status': 5, 'title': title}
                        elif media_status == 3 and previous_status != 3 and addon.getSettingBool('notify_processing'):
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} is now processing', xbmcgui.NOTIFICATION_INFO, 4000)
                            notified_media[media_id] = {'status': 3, 'title': title}
                        elif media_status == 2 and previous_status != 2 and addon.getSettingBool('notify_approved'):
                            xbmcgui.Dialog().notification('KodiSeerr', f'{title} request approved', xbmcgui.NOTIFICATION_INFO, 4000)
                            notified_media[media_id] = {'status': 2, 'title': title}
                        elif media_status != previous_status and media_id not in notified_media:
                            notified_media[media_id] = {'status': media_status, 'title': title}

                silent = False
                os.makedirs(os.path.dirname(notified_file), exist_ok=True)
                with open(notified_file, 'w') as f:
                    json.dump({'media': notified_media, 'declined': notified_declined}, f)

        if monitor.waitForAbort(interval):
            break
        interval = get_interval()


if __name__ == '__main__':
    main_loop()
