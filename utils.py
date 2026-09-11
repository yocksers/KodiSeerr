import urllib.parse


def build_url(query):
    import context
    return context.base_url + '?' + urllib.parse.urlencode(query)


def add_next_page_button(base_params, page, total_pages):
    import xbmcplugin
    import xbmcgui
    import context
    if page < total_pages:
        params = dict(base_params)
        params['page'] = page + 1
        next_item = xbmcgui.ListItem(label=f'[B]Next Page ({page + 1}) >>[/B]')
        next_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        xbmcplugin.addDirectoryItem(context.addon_handle, build_url(params), next_item, True)
