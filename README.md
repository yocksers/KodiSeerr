# KodiSeerr

A Kodi add-on for Jellyseerr and Overseerr integration. Browse, search, and request movies and TV shows, track requests, manage favorites, and receive notifications - all from within Kodi.

---

## Requirements

- Kodi 19+ (Matrix or newer)
- A running Jellyseerr server
- Network access to your Jellyseerr instance

---

## Installation

1. Download the latest `Kodiseerr.zip` release
2. In Kodi, navigate to **Add-ons**
3. Click the package icon (top left) → **Install from zip file**
4. Select the downloaded ZIP file
5. Wait for the "Add-on installed" notification

---

## Configuration

1. Open the KodiSeerr add-on
2. Go to **Settings**
3. Set your **Server URL** (e.g., `http://192.168.1.100:5055`), **Username**, and **Password**
4. Enable **Allow self-signed certificates** if needed

Additional settings cover requests (4K, quality profiles, season selection), notifications (polling interval, status triggers), display (items per page, badges, ratings), and advanced options (debug logging, cache, backup/restore).

---

## Usage

### Main Menu
- **Search** - Search for movies or TV shows
- **Trending / Popular** - Browse trending or popular content
- **Recently Added** - See what's new on your server
- **Collections** - Browse movie collections
- **My Favorites** - View your local watchlist
- **My Requests** - Track your request history
- **Statistics** - View server statistics
- **Settings** - Configure the addon

### Requesting Content
1. Find a movie or TV show and select it
2. Choose seasons (TV shows, if enabled) and quality profile (if enabled)
3. For movies, choose regular or 4K (if enabled)
4. Confirm your request

### Favorites
Right-click any item and select **Add to Favorites** or **Remove from Favorites**. Access your list from the main menu.

---

## Notifications

A background service monitors your requests and notifies you when a request is approved, starts processing, or becomes available. Configure this in **Settings** → **Notifications**.

---

## Support This Project

If you enjoy KodiSeerr and want to donate for a coffee or to kill some braincells with a beer:

[Buy me a coffee](https://buymeacoffee.com/yockser)

---

## Links

- Jellyseerr: https://github.com/Fallenbagel/jellyseerr
- Kodi: https://kodi.tv/
