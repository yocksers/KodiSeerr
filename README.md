# KodiSeerr

*A full-featured Jellyseerr and Overseerr integration for Kodi*

KodiSeerr is a comprehensive Kodi add-on that provides complete integration with Jellyseerr servers. Browse, search, and request movies and TV shows with advanced features including request tracking, favorites, collections, and smart notifications - all from within Kodi.

---

## ✨ Features

### Core Features
- 🔍 **Search** movies and TV shows with detailed results
- 🔥 Browse **Trending** and **Popular** content (Movies & TV)
- 📺 View **Recently Added** content
- ✅ **Request** movies or TV shows with confirmation dialogs
- 🎬 Browse **Collections** (e.g., Marvel Cinematic Universe)
- 📊 **Statistics Dashboard** showing request counts and server info

### Advanced Request Management
- 🟢 **Request Status Indicators** (Available, Pending, Processing, Denied)
- 🎯 **Season/Episode Selection** for TV shows
- 🎞️ **Quality Profile Selection** with preference memory
- 🔄 **Duplicate Request Detection**
- ❌ **Request Cancellation** support
- 📋 **Request Templates** with saved preferences

### User Experience
- ⭐ **Favorites/Watchlist** system (local storage)
- 📄 **Advanced Pagination** with jump-to-page functionality
- 📱 **Context Menus** (Show Details, Add to Favorites)
- 📝 **Detailed Media Information** viewer
- 🔔 **Smart Notifications** (approved, processing, available)
- 💾 **API Response Caching** for improved performance
- 🧪 **Connection Test** utility in settings

### Configuration Options
- 🔐 Username/password authentication (no API key needed)
- 🖼️ Customizable display settings (ratings, badges, year display)
- ⚙️ Adjustable items per page and cache duration
- 🔄 Settings backup and restore functionality
- 🐛 Debug logging option
- 🔒 Self-signed certificate support

---

## 📋 Requirements

- **Kodi 19+** (Matrix or newer)
- **Python 3.0.1+** (included with Kodi 19+)
- A running **Jellyseerr** server
- Network access to your Jellyseerr instance

---

## 📥 Installation

### Method 1: From ZIP (Recommended)
1. Download the latest `Kodiseerr.zip` release
2. In Kodi, navigate to **Add-ons**
3. Click the **package icon** (top left) → **Install from zip file**
4. Browse to and select the downloaded ZIP file
5. Wait for the "Add-on installed" notification

---

## ⚙️ Configuration

### Initial Setup
1. Open the KodiSeerr add-on
2. Go to **Settings** (gear icon or right-click context menu)
3. Configure the following:

**General Settings:**
- **Server URL**: Your Jellyseerr address (e.g., `http://192.168.1.100:5055`)
- **Username**: Your Jellyseerr username or email
- **Password**: Your account password
- **Allow self-signed certificates**: Enable if using HTTPS with self-signed cert

4. Click **Test Server Connection** to verify your settings
5. That's it! 🎉

### Additional Settings

**Requests:**
- Enable/disable 4K request prompts
- Configure quality profile selection
- Set default quality profiles
- Enable season selection for TV shows
- Toggle confirmation dialogs

**Notifications:**
- Enable request status notifications
- Set polling interval (default: 300 seconds)
- Choose which status changes trigger notifications

**Display:**
- Items per page (default: 20)
- Show/hide year in titles, media type badges, ratings

**Performance:**
- API caching (recommended: enabled)
- Cache duration in minutes
- Image caching options

**Advanced:**
- Debug logging for troubleshooting
- Export/import settings for backup
- Clear cache when needed

---

## 🎮 Usage

### Main Menu
- **Search** - Search for movies or TV shows
- **Trending** - Browse trending content
- **Popular** - Browse popular content
- **Recently Added** - See what's new on your server
- **Collections** - Browse movie collections
- **My Favorites** - View your local watchlist
- **My Requests** - Track your request history
- **Statistics** - View server statistics
- **Settings** - Configure the addon

### Requesting Content
1. Find a movie or TV show through search or browsing
2. Select the item
3. If it's a TV show and season selection is enabled, choose seasons
4. If quality profiles are enabled, select your preferred quality
5. For movies, choose between regular or 4K (if enabled)
6. Confirm your request
7. Receive notifications as the request status changes

### Managing Favorites
- Right-click (long-press on mobile) on any item
- Select **Add to Favorites** or **Remove from Favorites**
- Access your favorites from the main menu

---

## 🔔 Notifications

KodiSeerr includes a background service that monitors your requests and provides notifications:

- **Approved**: When an admin approves your request
- **Processing**: When content starts downloading
- **Available**: When content is ready to watch

Configure notification preferences in **Settings** → **Notifications**

---

## 💾 Backup & Restore

Export your settings before reinstalling or moving to a different Kodi instance:

1. Go to **Settings** → **Advanced**
2. Click **Export Settings** to save your configuration
3. On new installation, use **Import Settings** to restore

---

## ❤️ Support This Project

If you enjoy KodiSeerr and want to donate for a coffee or to kill some braincells with a beer:

[**Buy me a coffee ☕**](https://buymeacoffee.com/yockser)

---

## 🔗 Links

- **Jellyseerr**: https://github.com/Fallenbagel/jellyseerr
- **Kodi**: https://kodi.tv/
