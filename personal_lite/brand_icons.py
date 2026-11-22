"""Branded icon retrieval for FIELD.

Bundled logo images are usable immediately and offline. Missing logos are
retrieved from publisher-controlled HTTPS URLs or public icon libraries, cached
under LOCALAPPDATA/ FIELD and never downloaded into the temporary PyInstaller
extraction directory. All network traffic stays off the Qt GUI thread.
"""
from __future__ import annotations

import os
import re
import sys
import threading
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# User-selected apps only. No network URL is ever built from package names.
# Earlier sources are preferable; website favicons are last-resort fallbacks.
ICON_SOURCES: dict[str, tuple[str, ...]] = {
    'Google.Chrome': (
        'https://cdn.simpleicons.org/googlechrome/4285F4',
        'https://www.google.com/s2/favicons?domain=google.com&sz=128',
    ),
    'Mozilla.Firefox': (
        'https://raw.githubusercontent.com/mozilla-firefox/firefox/main/browser/branding/official/content/about-logo.svg',
        'https://cdn.simpleicons.org/firefoxbrowser/FF7139',
    ),
    'Brave.Brave': ('https://cdn.simpleicons.org/brave/FB542B',),
    'Discord.Discord': ('https://cdn.simpleicons.org/discord/5865F2',),
    'Telegram.TelegramDesktop': ('https://cdn.simpleicons.org/telegram/26A5E4',),
    'Valve.Steam': ('https://cdn.simpleicons.org/steam/245A81',),
    'EpicGames.EpicGamesLauncher': (
        'https://cdn.simpleicons.org/epicgames/FFFFFF',
        'https://www.google.com/s2/favicons?domain=epicgames.com&sz=128',
    ),
    'OBSProject.OBSStudio': (
        'https://cdn.simpleicons.org/obsstudio/635A82',
        'https://www.google.com/s2/favicons?domain=obsproject.com&sz=128',
    ),
    'VideoLAN.VLC': (
        'https://cdn.simpleicons.org/vlcmediaplayer/FF8800',
        'https://www.google.com/s2/favicons?domain=videolan.org&sz=128',
    ),
    '7zip.7zip': (
        'https://cdn.simpleicons.org/7zip/333333',
        'https://www.google.com/s2/favicons?domain=7-zip.org&sz=128',
    ),
    'Notepad++.Notepad++': (
        'https://cdn.simpleicons.org/notepadplusplus/68B04D',
        'https://www.google.com/s2/favicons?domain=notepad-plus-plus.org&sz=128',
    ),
    'Microsoft.PowerToys': (
        'https://cdn.simpleicons.org/powertoys/357EC7',
        'https://www.google.com/s2/favicons?domain=learn.microsoft.com&sz=128',
    ),
    'Microsoft.VisualStudioCode': (
        'https://cdn.simpleicons.org/visualstudiocode/007ACC',
        'https://www.google.com/s2/favicons?domain=code.visualstudio.com&sz=128',
    ),
    'Git.Git': ('https://cdn.simpleicons.org/git/F05032',),
    'Happ.Happ': (
        'https://www.google.com/s2/favicons?domain=happ.su&sz=128',
    ),
    'Throneproj.Throne': (
        'https://github.com/throneproj.png?size=256',
        'https://www.google.com/s2/favicons?domain=throneproj.github.io&sz=128',
    ),
    'Guru3D.Afterburner': (
        'https://asset.msi.com/global/picture/app/afterburner.png',
        'https://www.google.com/s2/favicons?domain=msi.com&sz=128',
    ),
    'REALiX.HWiNFO': (
        'https://www.google.com/s2/favicons?domain=hwinfo.com&sz=128',
    ),
    'CPUID.HWMonitor': (
        'https://www.google.com/s2/favicons?domain=cpuid.com&sz=128',
    ),
    'voidtools.Everything': (
        'https://www.google.com/s2/favicons?domain=voidtools.com&sz=128',
    ),
    'ShareX.ShareX': (
        'https://cdn.simpleicons.org/sharex/2075B9',
        'https://www.google.com/s2/favicons?domain=getsharex.com&sz=128',
    ),
    'qBittorrent.qBittorrent': (
        'https://cdn.simpleicons.org/qbittorrent/2F67BA',
        'https://www.google.com/s2/favicons?domain=qbittorrent.org&sz=128',
    ),
    'Spotify.Spotify': ('https://cdn.simpleicons.org/spotify/1DB954',),
    'Audacity.Audacity': (
        'https://cdn.simpleicons.org/audacity/0000CC',
        'https://www.google.com/s2/favicons?domain=audacityteam.org&sz=128',
    ),
    'Bitwarden.Bitwarden': ('https://cdn.simpleicons.org/bitwarden/175DDC',),
    'KeePassXCTeam.KeePassXC': (
        'https://cdn.simpleicons.org/keepassxc/6CAC4D',
        'https://www.google.com/s2/favicons?domain=keepassxc.org&sz=128',
    ),
}

_active_lock = threading.RLock()
_downloads_active = False


def icon_cache_dir() -> Path:
    """V2 cache avoids old favicons from previous FIELD installations."""
    base = os.environ.get('LOCALAPPDATA') or str(Path.home() / '.cache')
    return Path(base) / 'FIELD' / 'brand_icons_v2'


def _existing(directory: Path, package_id: str) -> bool:
    return any((directory / f'{package_id}.{ext}').is_file()
               for ext in ('png', 'svg', 'ico', 'jpg'))


def _validate_icon(url: str, payload: bytes) -> str:
    if not payload or len(payload) > 600_000:
        raise ValueError('Unexpected image size')
    if payload.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if payload.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    if payload[:4] == b'\x00\x00\x01\x00':
        return '.ico'
    if payload.lstrip().startswith((b'<svg', b'<?xml')):
        root = ET.fromstring(payload)
        if not root.tag.endswith('svg'):
            raise ValueError('Not an SVG')
        # Reject remote resources, references, scripting and embedded HTML.
        for node in root.iter():
            name = node.tag.lower()
            if name.endswith(('script', 'foreignobject', 'image')):
                raise ValueError('Unsupported SVG content')
            if any('href' in key.lower() for key in node.attrib):
                raise ValueError('SVG references are not allowed')
        return '.svg'
    raise ValueError('Image type not recognized')


def _fetch_one(package_id: str, target_dir: Path, refresh: bool, bundled_dir: Path | None):
    if not refresh and (_existing(target_dir, package_id) or
                        (bundled_dir is not None and _existing(bundled_dir, package_id))):
        return
    for url in ICON_SOURCES.get(package_id, ()):
        try:
            request = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (FIELD Windows installer; app icon retrieval)',
                'Accept': 'image/svg+xml,image/png,image/*;q=0.9,*/*;q=0.1',
            })
            with urllib.request.urlopen(request, timeout=7) as response:
                data = response.read(600_001)
            suffix = _validate_icon(url, data)
            dest = target_dir / f'{package_id}{suffix}'
            target_dir.mkdir(parents=True, exist_ok=True)
            tmp = target_dir / f'.{package_id}{suffix}.tmp'
            tmp.write_bytes(data)
            tmp.replace(dest)
            # Do not prioritize a stale PNG over a new SVG (or vice versa).
            for ext in ('.svg', '.png', '.ico', '.jpg'):
                if ext != suffix:
                    (target_dir / f'{package_id}{ext}').unlink(missing_ok=True)
            return
        except (OSError, ValueError, ET.ParseError):
            continue


def download_icons(package_ids: list[str], *, refresh: bool = False,
                   bundled_dir: Path | None = None, workers: int = 4):
    """Blocking function for standalone icon preparation scripts."""
    from queue import Queue, Empty
    items = list(dict.fromkeys(package_ids))
    queue = Queue()
    for pid in items:
        queue.put(pid)
    dest = icon_cache_dir()
    def worker():
        while True:
            try:
                pid = queue.get_nowait()
            except Empty:
                return
            try:
                _fetch_one(pid, dest, refresh, bundled_dir)
            finally:
                queue.task_done()
    threads = [threading.Thread(target=worker, daemon=True,
                                name=f'FIELD-icon-{i}') for i in range(min(workers, len(items)))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return sum(_existing(dest, pid) or (bundled_dir and _existing(bundled_dir, pid))
               for pid in items), len(items)


def downloads_active() -> bool:
    with _active_lock:
        return _downloads_active


def start_icon_downloads(package_ids: list[str], *, refresh: bool = False,
                         bundled_dir: Path | None = None) -> bool:
    """Start icon download in daemon thread; never touches Qt objects."""
    global _downloads_active
    with _active_lock:
        if _downloads_active:
            return False
        _downloads_active = True
    def run():
        global _downloads_active
        try:
            download_icons(package_ids, refresh=refresh, bundled_dir=bundled_dir)
        finally:
            with _active_lock:
                _downloads_active = False
    threading.Thread(target=run, name='FIELD-brand-icon-loader', daemon=True).start()
    return True


def load_svg_pixmap(path: Path, size: int):
    """Render Qt SVG on the GUI thread (no SVG image plugin dependency)."""
    from PySide6.QtCore import QByteArray, Qt
    from PySide6.QtGui import QColor, QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer
    try:
        renderer = QSvgRenderer(str(path))
        if not renderer.isValid():
            return QPixmap()
        pix = QPixmap(size * 3, size * 3)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        return pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
    except Exception:
        return QPixmap()
