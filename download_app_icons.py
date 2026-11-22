"""Download app-site favicons for FIELD. Requires an internet connection when run.
Icons are fetched from the corresponding websites using Google's favicon service.
Images are cached in assets/app_icons and displayed offline afterwards.
"""
from __future__ import annotations
import urllib.request
from pathlib import Path

DOMAINS = {
    'Google.Chrome': 'google.com',
    'Mozilla.Firefox': 'mozilla.org',
    'Brave.Brave': 'brave.com',
    'Discord.Discord': 'discord.com',
    'Telegram.TelegramDesktop': 'telegram.org',
    'Valve.Steam': 'store.steampowered.com',
    'EpicGames.EpicGamesLauncher': 'epicgames.com',
    'OBSProject.OBSStudio': 'obsproject.com',
    'VideoLAN.VLC': 'videolan.org',
    '7zip.7zip': '7-zip.org',
    'Notepad++.Notepad++': 'notepad-plus-plus.org',
    'Microsoft.PowerToys': 'learn.microsoft.com',
    'Microsoft.VisualStudioCode': 'code.visualstudio.com',
    'Git.Git': 'git-scm.com',
    'Happ.Happ': 'happ.su',
    'Throneproj.Throne': 'throneproj.github.io',
}

def main():
    directory = Path(__file__).resolve().parent / 'assets' / 'app_icons'
    directory.mkdir(parents=True, exist_ok=True)
    for package, domain in DOMAINS.items():
        filename = directory / f'{package}.png'
        url = f'https://www.google.com/s2/favicons?domain={domain}&sz=128'
        try:
            request = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 FIELD-icon-downloader/1.0'})
            with urllib.request.urlopen(request, timeout=15) as response:
                data = response.read(512_000)
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('Response is not PNG')
            filename.write_bytes(data)
            print(f'[OK] {package} ({domain})')
        except Exception as exc:
            print(f'[SKIP] {package}: {exc}')
    print(f'Done. Icons folder: {directory}')

if __name__ == '__main__':
    main()
