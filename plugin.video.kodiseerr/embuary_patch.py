"""User-initiated patch: add a KodiSeerr Request action to Embuary
Info's movie/TV info dialog.

Invoked from KodiSeerr's Advanced settings. Not automatic — the user
must re-run it after an Embuary Info upgrade wipes the change.

The patch has two parts:
  1. Inject an <item> block into
     script.embuary.info/resources/skins/default/1080i/script-embuary-video.xml
  2. Copy request.png into
     script.embuary.info/resources/skins/default/media/icons/

Idempotent: if `plugin.video.kodiseerr` already appears in the XML, the
patch is treated as present. Embuary's WindowXMLDialog is re-read from
disk every time it opens, so no reload is needed — the next info-page
open shows the Request button.
"""

import os
import re
import shutil

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

_ADDON = xbmcaddon.Addon()
_ADDON_PATH = xbmcvfs.translatePath(_ADDON.getAddonInfo('path'))

EMBUARY_ID = 'script.embuary.info'
EMBUARY_VIDEO_XML_REL = 'resources/skins/default/1080i/script-embuary-video.xml'
EMBUARY_ICON_DIR_REL = 'resources/skins/default/media/icons'
ICON_NAME = 'request.png'

_ICON_SOURCE = os.path.join(_ADDON_PATH, 'resources', 'media', ICON_NAME)

_PATCH_MARKER = 'plugin.video.kodiseerr'

# Anchor on the plot <item> so insertion tolerates whitespace drift.
_PLOT_ITEM_RE = re.compile(
    r'(?P<indent>[ \t]*)<item>\s*'
    r'<visible>[^<]*Container\(10051\)\.ListItem\.Plot[^<]*</visible>\s*'
    r'<property\s+name="icon">plot</property>.*?'
    r'</item>',
    re.DOTALL,
)

_REQUEST_ITEM_TEMPLATE = (
    '{i}<item>\n'
    '{i}\t<visible>System.AddonIsEnabled(plugin.video.kodiseerr) + String.IsEmpty(Container(10051).ListItem.DBID)</visible>\n'
    '{i}\t<property name="icon">request</property>\n'
    '{i}\t<label>Request</label>\n'
    '{i}\t<onclick condition="String.IsEqual(Container(10051).ListItem.Property(call),movie)">RunPlugin(plugin://plugin.video.kodiseerr/?mode=request&amp;type=movie&amp;id=$INFO[Container(10051).ListItem.Property(id)])</onclick>\n'
    '{i}\t<onclick condition="String.IsEqual(Container(10051).ListItem.Property(call),tv)">RunPlugin(plugin://plugin.video.kodiseerr/?mode=request&amp;type=tv&amp;id=$INFO[Container(10051).ListItem.Property(id)])</onclick>\n'
    '{i}</item>'
)


def _log(msg, level=xbmc.LOGINFO):
    xbmc.log('[KodiSeerr][embuary_patch] ' + msg, level)


def _embuary_path(rel):
    return xbmcvfs.translatePath(f'special://home/addons/{EMBUARY_ID}/{rel}')


def _embuary_installed():
    return os.path.isfile(_embuary_path(EMBUARY_VIDEO_XML_REL))


def _ensure_icon():
    icon_dir = _embuary_path(EMBUARY_ICON_DIR_REL)
    dest = os.path.join(icon_dir, ICON_NAME)
    if os.path.isfile(dest):
        return True
    if not os.path.isfile(_ICON_SOURCE):
        _log(f'icon source missing: {_ICON_SOURCE}', xbmc.LOGWARNING)
        return False
    try:
        os.makedirs(icon_dir, exist_ok=True)
        shutil.copyfile(_ICON_SOURCE, dest)
        _log(f'installed icon -> {dest}')
        return True
    except OSError as exc:
        _log(f'icon copy failed: {exc}', xbmc.LOGERROR)
        return False


def _apply():
    """Returns (status, message) where status is one of:
      'installed'     — patch already present; icon ensured
      'applied'       — patch newly applied
      'missing'       — embuary not installed
      'anchor_lost'   — XML layout drifted; cannot patch safely
      'read_error'    — could not read XML
      'write_error'   — could not write XML
      'icon_error'    — XML patched but icon copy failed
    """
    if not _embuary_installed():
        return ('missing', 'Embuary Info is not installed.')

    xml_path = _embuary_path(EMBUARY_VIDEO_XML_REL)
    try:
        with open(xml_path, 'r', encoding='utf-8') as fh:
            xml = fh.read()
    except OSError as exc:
        _log(f'read failed: {exc}', xbmc.LOGERROR)
        return ('read_error', f'Could not read Embuary XML: {exc}')

    if _PATCH_MARKER in xml:
        icon_ok = _ensure_icon()
        if not icon_ok:
            return ('icon_error',
                    'Patch already present but icon could not be copied.')
        return ('installed', 'Request button already present.')

    match = _PLOT_ITEM_RE.search(xml)
    if not match:
        return ('anchor_lost',
                'Embuary XML layout has changed; anchor not found.')

    indent = match.group('indent') or '\t\t\t\t\t\t\t'
    insertion = '\n' + _REQUEST_ITEM_TEMPLATE.format(i=indent)
    new_xml = xml[:match.end()] + insertion + xml[match.end():]

    try:
        with open(xml_path, 'w', encoding='utf-8') as fh:
            fh.write(new_xml)
    except OSError as exc:
        _log(f'write failed: {exc}', xbmc.LOGERROR)
        return ('write_error', f'Could not write Embuary XML: {exc}')

    if not _ensure_icon():
        return ('icon_error',
                'XML updated but request icon could not be copied.')

    _log('patch applied')
    return ('applied', 'Request button added to Embuary Info.')


def run_interactive():
    """Entry point wired to the Advanced-settings button."""
    status, msg = _apply()
    dialog = xbmcgui.Dialog()
    if status in ('applied', 'installed'):
        note = ('' if status == 'installed'
                else '\n\nOpen a movie or TV info page to see the '
                'Request button.')
        dialog.ok('KodiSeerr', msg + note)
    else:
        dialog.ok('KodiSeerr', msg)
