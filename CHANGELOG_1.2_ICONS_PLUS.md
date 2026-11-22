# FIELD 1.2 — application catalog and icon update

- Fixed empty `assets/app_icons` packaging by bundling eight real brand icons, from Font Awesome Free brand vectors (attribution included).
- Added automatic background retrieval and v2 local cache for missing logos, with no UI blocking, plus a manual **Refresh icons** action.
- The existing `fix_field_icons.py` command now refreshes the new icon cache and bundles downloaded logos.
- Expanded built-in winget catalog from 16 to **26 applications**, including MSI Afterburner, HWiNFO, HWMonitor, Everything, ShareX, qBittorrent, Spotify, Audacity, Bitwarden, and KeePassXC.
- Added localized categories Monitoring and Security.
- EXE build script automatically attempts to bundle available downloaded logos. Installation and logo fetching remain separate, no software installs automatically.

**Test limitations:** GUI and winget installs must be checked on Windows; some logos require a network connection and may fail at their remote source.
