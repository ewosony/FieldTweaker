# FIELD 1.2.0 — Windows Control Center

Complete Python/PySide6 source tree for Windows 10 and 11. Repository: https://github.com/ewosony/FieldTweaker.

## Features

- **Home:** live CPU, memory, disk capacity and quick navigation.
- **System cleanup:** scan and selectively delete old temporary files, thumbnails, crash dumps, archived error reports, and browser caches. Preview before deletion, explicit confirmation, no cookies/passwords/history/documents/restore points.
- **App installer:** 16 winget applications, search, category filter, essentials preset, installed-app detection, upgrade selected, progress and installation log. Fully integrated into the main window.
- **Power plans:** switch among plans already present in Windows, restore the previous active plan.
- **Advanced settings:** reversible Windows Update controls, driver update preferences, Game DVR background capture, Fast Startup and wallpaper JPEG quality.
- Existing settings, built-in apps, startup items, profiles, activity history, process monitor, and file-lock inspector remain available.
- Russian/English interface, dark/light themes.

## Run

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 main.py
```

## Package

```powershell
py -3.11 -m pip install --upgrade pyinstaller
.\build_exe.bat
```

The bundled one-file executable is built at `dist\FIELD 1.2.exe`. Official app icon PNGs are not included; the app displays fallback badges and provides optional download scripts.

## Safety

Cleanup only processes explicitly selected old cache files from allowlisted locations, never browsing history/passwords/cookies/documents. Files are deleted without using the Recycle Bin. Close browsers before clearing caches. Windows Update disabling increases exposure to security vulnerabilities and may be overridden by Windows itself. Settings backups are stored under `%APPDATA%\FIELD` for restoration. Only existing Windows power plans can be selected. Administrator permission is required for some advanced settings.

## Tests

```powershell
py -3.11 -m unittest discover -s tests -v
```

Offline tests have been executed; GUI/winget/Windows features require testing on a real Windows machine before publishing. See `MANUAL_TESTS.md`.


## Updated app catalog and branded icons

The embedded app installer now lists **26 apps**, including MSI Afterburner, HWiNFO, HWMonitor, Everything, ShareX, qBittorrent, Spotify, Audacity, Bitwarden, and KeePassXC.

Eight brand-logo PNG images are included in `assets/app_icons`. Remaining logos are fetched on the user's PC from publisher websites or public icon catalogs, cached under `%LOCALAPPDATA%\FIELD\brand_icons_v2`, and reused offline. To include downloaded logos in your standalone EXE, run `python download_app_icons.py --bundle` before PyInstaller; `build_exe.bat` runs this automatically. A **Refresh icons** button is available in the installer UI. If remote assets are unavailable, the UI uses a letter-based fallback. See `assets/app_icons/ATTRIBUTION.md` for attribution. FIELD only installs MSI Afterburner; it does not change GPU settings.
