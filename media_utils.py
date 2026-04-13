import xbmc
import api_client
import cache


def make_art(item):
    import context
    art = {}
    path_map = {
        "posterPath": ("poster", "thumb"),
        "backdropPath": ("fanart",),
        "logoPath": ("clearlogo",),
        "bannerPath": ("banner",),
        "landscapePath": ("landscape",),
        "iconPath": ("icon",),
        "clearartPath": ("clearart",),
    }
    for key, targets in path_map.items():
        if item.get(key):
            for target in targets:
                art[target] = context.image_base + item[key]
    return art


def make_info(item, media_type):
    release_date = item.get('releaseDate') or item.get('firstAirDate')
    year = int(release_date.split("-")[0]) if release_date and release_date.split("-")[0].isdigit() else 0

    def join_names(obj_list):
        return ', '.join(
            g['name'] if isinstance(g, dict) and 'name' in g else str(g)
            for g in obj_list
        )

    genres = join_names(item.get('genres', []))
    studio = join_names(item.get('studios', [])) if item.get('studios') else ''
    country = join_names(item.get('productionCountries', [])) if item.get('productionCountries') else ''
    mpaa = item.get('certification', '')
    try:
        runtime = int(item.get('runtime', 0))
    except Exception:
        runtime = 0
    try:
        rating = float(item.get('voteAverage', 0))
    except Exception:
        rating = 0.0
    try:
        votes = int(item.get('voteCount', 0))
    except Exception:
        votes = 0
    director = ', '.join([c['name'] for c in item.get('crew', []) if c.get('job') == 'Director']) if item.get('crew') else ''
    cast = [p['name'] for p in item.get('cast', []) if isinstance(p, dict) and 'name' in p]
    cast_str = ', '.join(cast[:5])
    plot = item.get('overview', '')
    title = item.get('title') or item.get('name')

    type_label = {'movie': 'Movie', 'tv': 'Series', 'season': 'Series', 'episode': 'Series'}.get(media_type)

    rich_plot = f"{title} ({year})"
    if type_label: rich_plot += f"\nType: {type_label}"
    if genres: rich_plot += f"\nGenres: {genres}"
    if studio: rich_plot += f"\nStudio: {studio}"
    if country: rich_plot += f"\nCountry: {country}"
    if mpaa: rich_plot += f"\nCertification: {mpaa}"
    if runtime: rich_plot += f"\nRuntime: {runtime} min"
    if rating: rich_plot += f"\nRating: {rating} ({votes} votes)"
    if director: rich_plot += f"\nDirector: {director}"
    if cast_str: rich_plot += f"\nCast: {cast_str}"
    if plot: rich_plot += f"\n\n{plot}"

    return {
        'title': title or "",
        'plot': rich_plot or "",
        'year': year,
        'genre': genres or "",
        'rating': rating,
        'votes': votes,
        'premiered': release_date or "",
        'duration': runtime,
        'mpaa': mpaa or "",
        'cast': cast,
        'director': director or "",
        'studio': studio or "",
        'country': country or "",
        'mediatype': media_type,
    }


def set_info_tag(list_item, info):
    tag = list_item.getVideoInfoTag()
    if info.get('title'): tag.setTitle(info['title'])
    if info.get('plot'): tag.setPlot(info['plot'])
    if info.get('year'):
        try: tag.setYear(int(info['year']))
        except Exception: pass
    if info.get('genre'):
        try:
            tag.setGenres([info['genre']])
        except AttributeError:
            tag.setGenre(info['genre'])
    if info.get('rating'):
        try: tag.setRating(float(info['rating']))
        except Exception: pass
    if info.get('votes'):
        try: tag.setVotes(int(info['votes']))
        except Exception: pass
    if info.get('premiered'): tag.setPremiered(info['premiered'])
    if info.get('duration'):
        try: tag.setDuration(int(info['duration']))
        except Exception: pass
    if info.get('mpaa'): tag.setMpaa(info['mpaa'])
    if info.get('cast'): tag.setCast(info['cast'])
    if info.get('director'):
        try:
            tag.setDirectors([info['director']])
        except AttributeError:
            tag.setDirector(info['director'])
    if info.get('studio'):
        try:
            tag.setStudios([info['studio']])
        except AttributeError:
            tag.setStudio(info['studio'])
    if info.get('country'):
        try:
            tag.setCountries([info['country']])
        except AttributeError:
            tag.setCountry(info['country'])
    if info.get('mediatype'): tag.setMediaType(info['mediatype'])


def get_media_status(media_type, media_id, item=None):
    if item is not None:
        media_info = item.get('mediaInfo')
        if media_info and isinstance(media_info, dict):
            status = media_info.get('status')
            if isinstance(status, (int, float)):
                return int(status)
        return 0
    cache_key = f"status_{media_type}_{media_id}"
    cached = cache.get_cached(cache_key)
    if cached is not None:
        return cached
    try:
        data = api_client.client.api_request(f"/{media_type}/{media_id}")
        if data and data.get('mediaInfo'):
            status = data['mediaInfo'].get('status')
            if isinstance(status, (int, float)):
                status = int(status)
                cache.set_cached(cache_key, status)
                return status
        cache.set_cached(cache_key, 1)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Status check error: {e}", xbmc.LOGERROR)
    return 1


def get_status_label(status):
    import context
    if not context.addon.getSettingBool('show_request_status'):
        return ""
    status_map = {
        2: "[COLOR yellow](Pending)[/COLOR]",
        3: "[COLOR cyan](Processing)[/COLOR]",
        4: "[COLOR lime](Partially Available)[/COLOR]",
        5: "[COLOR lime](Available)[/COLOR]",
        6: "[COLOR gray](Blocklisted)[/COLOR]",
        7: "[COLOR gray](Deleted)[/COLOR]",
    }
    return status_map.get(status, "")
