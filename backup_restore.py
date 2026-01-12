import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import json
import os
from datetime import datetime

addon = xbmcaddon.Addon()

def export_settings():
    """Export addon settings to a JSON file"""
    try:
        # Get all settings
        settings = {
            'jellyseerr_url': addon.getSetting('jellyseerr_url'),
            'jellyseerr_username': addon.getSetting('jellyseerr_username'),
            'allow_self_signed': addon.getSettingBool('allow_self_signed'),
            'enable_ask_4k': addon.getSettingBool('enable_ask_4k'),
            'show_quality_profiles': addon.getSettingBool('show_quality_profiles'),
            'default_quality_profile': addon.getSetting('default_quality_profile'),
            'remember_last_quality': addon.getSettingBool('remember_last_quality'),
            'enable_season_selection': addon.getSettingBool('enable_season_selection'),
            'confirm_before_request': addon.getSettingBool('confirm_before_request'),
            'show_request_status': addon.getSettingBool('show_request_status'),
            'enable_request_notifications': addon.getSettingBool('enable_request_notifications'),
            'polling_interval': addon.getSettingInt('polling_interval'),
            'notify_processing': addon.getSettingBool('notify_processing'),
            'notify_approved': addon.getSettingBool('notify_approved'),
            'items_per_page': addon.getSettingInt('items_per_page'),
            'show_year_in_title': addon.getSettingBool('show_year_in_title'),
            'show_media_type_badge': addon.getSettingBool('show_media_type_badge'),
            'show_ratings': addon.getSettingBool('show_ratings'),
            'enable_caching': addon.getSettingBool('enable_caching'),
            'cache_duration': addon.getSettingInt('cache_duration'),
            'cache_images': addon.getSettingBool('cache_images'),
            'debug_logging': addon.getSettingBool('debug_logging'),
            'export_date': datetime.now().isoformat()
        }
        
        # Get export path
        export_path = xbmcgui.Dialog().browse(3, 'Select Export Location', 'files', '', False, False, '')
        if not export_path:
            return
        
        filename = f"kodiseerr_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(export_path, filename)
        
        with open(filepath, 'w') as f:
            json.dump(settings, f, indent=2)
        
        xbmcgui.Dialog().notification('KodiSeerr', f'Settings exported to {filename}', xbmcgui.NOTIFICATION_INFO, 3000)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Export error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('KodiSeerr', 'Export failed', xbmcgui.NOTIFICATION_ERROR)

def import_settings():
    """Import addon settings from a JSON file"""
    try:
        # Get import file
        import_file = xbmcgui.Dialog().browse(1, 'Select Settings File to Import', 'files', '.json', False, False, '')
        if not import_file:
            return
        
        with open(import_file, 'r') as f:
            settings = json.load(f)
        
        # Confirm import
        if not xbmcgui.Dialog().yesno('KodiSeerr', 'This will overwrite current settings. Continue?'):
            return
        
        # Apply settings (skip password for security)
        for key, value in settings.items():
            if key in ['export_date', 'jellyseerr_password']:
                continue
            try:
                if isinstance(value, bool):
                    addon.setSettingBool(key, value)
                elif isinstance(value, int):
                    addon.setSettingInt(key, value)
                else:
                    addon.setSetting(key, str(value))
            except Exception as e:
                xbmc.log(f"[KodiSeerr] Failed to import setting {key}: {e}", xbmc.LOGWARNING)
        
        xbmcgui.Dialog().notification('KodiSeerr', 'Settings imported successfully', xbmcgui.NOTIFICATION_INFO, 3000)
    except Exception as e:
        xbmc.log(f"[KodiSeerr] Import error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('KodiSeerr', 'Import failed', xbmcgui.NOTIFICATION_ERROR)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == 'export':
            export_settings()
        elif action == 'import':
            import_settings()
