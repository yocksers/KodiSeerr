import sys
import xbmcgui
import context
import cache
import api_client
import requests_view

context.init(["plugin://plugin.video.kodiseerr/", "-1", "?"])
cache.load_cache()


def _year_of(result):
    date = result.get('releaseDate') or result.get('firstAirDate') or ""
    return date.split("-")[0] if date else ""


def main():
    if not context.addon.getSettingBool('enable_context_menu_request'):
        return

    listitem = getattr(sys, 'listitem', None)
    if listitem is None:
        xbmcgui.Dialog().notification('KodiSeerr', 'No item selected', xbmcgui.NOTIFICATION_ERROR, 3000)
        return

    tag = listitem.getVideoInfoTag()
    dbtype = tag.getMediaType()
    media_type = 'tv' if dbtype in ('tvshow', 'season', 'episode') else 'movie'
    title = tag.getTVShowTitle() if dbtype == 'episode' else tag.getTitle()
    title = title or listitem.getLabel()
    year = tag.getYear()
    if not title:
        xbmcgui.Dialog().notification('KodiSeerr', 'No title found for this item', xbmcgui.NOTIFICATION_ERROR, 3000)
        return

    from urllib.parse import urlencode, quote
    qs = urlencode({'query': title, 'page': 1}, quote_via=quote)
    data = api_client.client.api_request(f'/search?{qs}', params=None)
    results = [r for r in (data.get('results', []) if data else []) if r.get('mediaType') == media_type]
    if not results:
        xbmcgui.Dialog().notification('KodiSeerr', f"No Seerr match found for '{title}'", xbmcgui.NOTIFICATION_WARNING, 4000)
        return

    match = None
    if year:
        match = next((r for r in results if _year_of(r) == str(year)), None)
    if not match:
        match = results[0]

    media_id = match.get('id')
    if not media_id:
        xbmcgui.Dialog().notification('KodiSeerr', f"No Seerr match found for '{title}'", xbmcgui.NOTIFICATION_WARNING, 4000)
        return

    requests_view.do_request(media_type, media_id)


if __name__ == '__main__':
    main()
