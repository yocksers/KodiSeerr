import urllib.parse


def build_url(query):
    import context
    return context.base_url + '?' + urllib.parse.urlencode(query)
