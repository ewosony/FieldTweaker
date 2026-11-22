"""Conservative, opt-in cleanup of *cache* files in allowlisted user folders.

Never clears documents, browser history, passwords, cookies, Windows update caches,
or restore points. No traversal through symlinks/reparse points. Scans have a cap.
"""
from __future__ import annotations

import os
import stat
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

CATEGORY_NAMES = {
    'temp': ('Временные файлы', 'Temporary files'),
    'thumbnails': ('Кэш миниатюр', 'Thumbnail cache'),
    'crash': ('Дампы сбоев', 'Crash dumps'),
    'reports': ('Архив отчётов Windows', 'Windows error reports'),
    'browser': ('Кэш браузеров', 'Browser cache'),
}
AGE_DAYS = {'temp': 2, 'thumbnails': 7, 'crash': 7, 'reports': 7, 'browser': 1}
MAX_FILES = 70000


@dataclass(frozen=True)
class Candidate:
    category: str
    path: Path
    size: int
    mtime_ns: int
    root: Path


@dataclass
class ScanResult:
    files: dict[str, list[Candidate]] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)

    def size(self, category: str) -> int:
        return sum(entry.size for entry in self.files.get(category, []))

    def count(self, category: str) -> int:
        return len(self.files.get(category, []))


def _local_data() -> Path:
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local')))


def _browser_running() -> bool:
    try:
        import psutil
        for process in psutil.process_iter(['name']):
            name = (process.info.get('name') or '').lower()
            if name in {'chrome.exe', 'firefox.exe', 'brave.exe'}:
                return True
    except Exception:
        # On errors, err on the side of caution and don't clear browser files.
        return True
    return False


def candidate_roots(category: str) -> list[Path]:
    local = _local_data()
    if category == 'temp':
        return [Path(tempfile.gettempdir())]
    if category == 'thumbnails':
        return [local / 'Microsoft' / 'Windows' / 'Explorer']
    if category == 'crash':
        return [local / 'CrashDumps']
    if category == 'reports':
        return [local / 'Microsoft' / 'Windows' / 'WER' / 'ReportArchive']
    if category == 'browser':
        paths = []
        for company, name in [('Google', 'Chrome'), ('BraveSoftware', 'Brave-Browser')]:
            user_data = local / company / name / 'User Data'
            if user_data.is_dir():
                for profile in user_data.iterdir():
                    if profile.is_dir() and (profile.name == 'Default' or profile.name.startswith('Profile ')):
                        paths.extend([profile / 'Cache' / 'Cache_Data', profile / 'Cache'])
        ff = local / 'Mozilla' / 'Firefox' / 'Profiles'
        if ff.is_dir():
            paths.extend(profile / 'cache2' / 'entries' for profile in ff.iterdir() if profile.is_dir())
        return paths
    raise ValueError('Unknown cleanup category: ' + category)


def _reparse(path: Path) -> bool:
    try:
        data = path.lstat()
        return stat.S_ISLNK(data.st_mode) or bool(getattr(data, 'st_file_attributes', 0) & 0x400)
    except OSError:
        return True


def _eligible_name(category: str, path: Path) -> bool:
    if category == 'thumbnails':
        return path.name.casefold().startswith(('thumbcache_', 'iconcache_')) and path.suffix.lower() == '.db'
    if category == 'crash':
        return path.suffix.lower() in {'.dmp', '.mdmp', '.hdmp'}
    return True


def scan(categories=None, *, now=None) -> ScanResult:
    """Read-only scan. Checkboxes in the UI choose which categories to delete."""
    if categories is None:
        categories = CATEGORY_NAMES
    now = time.time() if now is None else now
    result = ScanResult()
    count = 0
    for category in categories:
        if category not in CATEGORY_NAMES:
            raise ValueError(category)
        result.files[category] = []
        if category == 'browser' and _browser_running():
            result.skipped[category] = 'Close Chrome, Firefox and Brave before scanning browser caches.'
            continue
        threshold = now - AGE_DAYS[category] * 86400
        for root in candidate_roots(category):
            if not root.is_dir() or _reparse(root):
                continue
            root = root.resolve()
            for base, dirs, files in os.walk(root, followlinks=False):
                # Never follow links, junctions, or other reparse points.
                dirs[:] = [d for d in dirs if not _reparse(Path(base) / d)]
                for name in files:
                    if count >= MAX_FILES:
                        result.skipped[category] = 'Scan limit reached; some files were not counted.'
                        break
                    count += 1
                    item = Path(base) / name
                    if not _eligible_name(category, item) or _reparse(item):
                        continue
                    try:
                        st = item.stat()
                        if not stat.S_ISREG(st.st_mode) or st.st_mtime > threshold:
                            continue
                        if not item.resolve().is_relative_to(root):
                            continue
                        result.files[category].append(Candidate(category, item, st.st_size, st.st_mtime_ns, root))
                    except (OSError, ValueError):
                        continue
                if count >= MAX_FILES:
                    break
            if count >= MAX_FILES:
                break
        if count >= MAX_FILES:
            break
    return result


def clean(result: ScanResult, categories) -> dict:
    """Delete only files found in the scan and unchanged since it. Never folders."""
    deleted = errors = freed = 0
    for category in categories:
        if category not in CATEGORY_NAMES:
            raise ValueError(category)
        if category == 'browser' and _browser_running():
            errors += len(result.files.get(category, []))
            continue
        for entry in result.files.get(category, []):
            try:
                if entry.category != category or _reparse(entry.path) or _reparse(entry.root):
                    continue
                if not entry.path.resolve().is_relative_to(entry.root.resolve()):
                    continue
                if not _eligible_name(category, entry.path):
                    continue
                data = entry.path.stat()
                if (not stat.S_ISREG(data.st_mode) or data.st_mtime_ns != entry.mtime_ns
                        or data.st_size != entry.size):
                    continue
                entry.path.unlink()
                deleted += 1
                freed += entry.size
            except OSError:
                errors += 1
    return {'deleted': deleted, 'bytes': freed, 'errors': errors}


def human_size(n):
    for unit in ('Б', 'КБ', 'МБ', 'ГБ', 'ТБ'):
        if n < 1024:
            return f'{n:.1f} {unit}' if unit != 'Б' else f'{int(n)} {unit}'
        n /= 1024
    return f'{n:.1f} ПБ'
