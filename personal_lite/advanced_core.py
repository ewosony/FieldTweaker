"""FIELD optional advanced Windows controls. No third-party executables.

Every modification is opt-in and backed up before it is attempted.
The Windows Update toggle sets the documented NoAutoUpdate policy and disables
wuauserv's startup. Windows servicing may override these settings later; this
is not an unconditional guarantee that Windows will never update.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timezone

if os.name == 'nt':
    import winreg
else:
    winreg = None

STATE_DIR = Path(os.environ.get('APPDATA') or (Path.home() / 'AppData' / 'Roaming')) / 'FIELD'
BACKUP_FILE = STATE_DIR / 'advanced_settings_backup.json'
UPDATE_KEY = r'SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU'
SERVICE_KEY = r'SYSTEM\CurrentControlSet\Services\wuauserv'

# Registry type 4 = DWORD. Only explicit allowlisted values are supported.
FEATURES = {
    'drivers': {
        'name_ru': 'Не загружать драйверы вместе с обновлениями',
        'name_en': 'Exclude drivers from Windows quality updates',
        'desc_ru': 'Запретить автоматическое получение драйверов через Windows Update.',
        'desc_en': 'Stop driver updates from being delivered through Windows Update.',
        'values': [('HKLM', r'SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate', 'ExcludeWUDriversInQualityUpdate', 1, 4)],
    },
    'gamedvr': {
        'name_ru': 'Отключить фоновую запись игр',
        'name_en': 'Disable game background capture',
        'desc_ru': 'Отключить автоматическую фоновую запись игрового процесса.',
        'desc_en': 'Disables background game capture; some Game Bar features may be unavailable.',
        'values': [
            ('HKCU', r'SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR', 'AppCaptureEnabled', 0, 4),
            ('HKCU', r'System\GameConfigStore', 'GameDVR_Enabled', 0, 4),
        ],
    },
    'faststartup': {
        'name_ru': 'Отключить быстрый запуск Windows',
        'name_en': 'Disable Windows Fast Startup',
        'desc_ru': 'Отключить быстрый запуск Windows.',
        'desc_en': 'Disable Windows Fast Startup.',
        'values': [('HKLM', r'SYSTEM\CurrentControlSet\Control\Session Manager\Power', 'HiberbootEnabled', 0, 4)],
    },
    'wallpaper': {
        'name_ru': 'Качество обоев JPEG — 100%',
        'name_en': 'JPEG wallpaper quality — 100%',
        'desc_ru': 'Установить максимальное качество JPEG-обоев.',
        'desc_en': 'Set maximum JPEG wallpaper quality.',
        'values': [('HKCU', r'Control Panel\Desktop', 'JPEGImportQuality', 100, 4)],
    },
}


def _require_windows():
    if os.name != 'nt' or winreg is None:
        raise RuntimeError('Эта операция доступна только в Windows / Windows only')


def _is_admin():
    return bool(ctypes.windll.shell32.IsUserAnAdmin()) if os.name == 'nt' else False


def _root(name):
    return winreg.HKEY_LOCAL_MACHINE if name == 'HKLM' else winreg.HKEY_CURRENT_USER


def _read(root, subkey, name):
    _require_windows()
    try:
        with winreg.OpenKey(_root(root), subkey, 0, winreg.KEY_READ) as key:
            value, kind = winreg.QueryValueEx(key, name)
            return {'exists': True, 'value': value, 'type': kind}
    except FileNotFoundError:
        return {'exists': False}


def _write(root, subkey, name, value, kind):
    _require_windows()
    with winreg.CreateKeyEx(_root(root), subkey, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, kind, value)


def _restore(root, subkey, name, original):
    _require_windows()
    if original['exists']:
        _write(root, subkey, name, original['value'], original['type'])
    else:
        try:
            with winreg.OpenKey(_root(root), subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except FileNotFoundError:
            pass


def _load_backup():
    if not BACKUP_FILE.exists():
        return {'schema': 1, 'items': {}}
    data = json.loads(BACKUP_FILE.read_text('utf-8'))
    if data.get('schema') != 1 or not isinstance(data.get('items'), dict):
        raise ValueError('Неподдерживаемый формат резервной копии FIELD')
    return data


def _save_backup(data):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix='advanced-', suffix='.tmp', dir=STATE_DIR)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(path, BACKUP_FILE)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _item_info(data, feature):
    return data['items'].get(feature)


def feature_status(feature):
    spec = FEATURES[feature]
    changes = spec['values']
    enabled = all(_read(root, path, name).get('value') == desired for root, path, name, desired, _ in changes)
    return {'applied': enabled, 'can_restore': _item_info(_load_backup(), feature) is not None}


def set_feature(feature, enable):
    _require_windows()
    if feature not in FEATURES:
        raise ValueError('Неизвестная настройка')
    spec = FEATURES[feature]
    changes = spec['values']
    if any(root == 'HKLM' for root, *_ in changes) and not _is_admin():
        raise PermissionError('Запусти FIELD от имени администратора / Run FIELD as administrator')
    data = _load_backup()
    if enable:
        if feature in data['items']:
            raise RuntimeError('Настройка уже применяется FIELD. Сначала восстанови её.')
        current = [_read(root, path, name) for root, path, name, *_ in changes]
        data['items'][feature] = {'saved_at': datetime.now(timezone.utc).isoformat(), 'original': current}
        _save_backup(data)  # Store BEFORE making any changes.
        try:
            for root, path, name, desired, kind in changes:
                _write(root, path, name, desired, kind)
        except Exception:
            # A partial application keeps its backup for explicit recovery.
            raise
        return 'Настройка применена / Setting applied'
    snapshot = data['items'].get(feature)
    if snapshot is None:
        raise RuntimeError('Нет резервной копии FIELD: нельзя восстановить прежнее значение автоматически.')
    for (root, path, name, *_), original in zip(changes, snapshot['original']):
        _restore(root, path, name, original)
    del data['items'][feature]
    _save_backup(data)
    return 'Настройка восстановлена / Setting restored'


def _service_start():
    data = _read('HKLM', SERVICE_KEY, 'Start')
    if not data['exists']:
        raise RuntimeError('Служба Windows Update (wuauserv) не найдена')
    return data['value']


def _run_sc(*args, optional=False):
    result = subprocess.run(['sc.exe', *args], capture_output=True, text=True, errors='replace', timeout=30, shell=False)
    if result.returncode and not optional:
        raise RuntimeError('sc.exe ' + ' '.join(args) + f' завершился с кодом {result.returncode}. ' + (result.stderr or result.stdout)[:400])
    return result.returncode == 0


def _set_service_start(start):
    mapping = {2: 'auto', 3: 'demand', 4: 'disabled'}
    if start not in mapping:
        raise RuntimeError(f'Неподдерживаемое состояние службы wuauserv: {start}')
    _run_sc('config', 'wuauserv', 'start=', mapping[start])


def update_status():
    _require_windows()
    policy = _read('HKLM', UPDATE_KEY, 'NoAutoUpdate')
    start = _service_start()
    return {
        'blocked': policy.get('value') == 1 and start == 4,
        'policy_disabled': policy.get('value') == 1,
        'service_disabled': start == 4,
        'can_restore': 'windows_update' in _load_backup()['items'],
    }


def set_windows_updates_disabled(disable):
    """Persistently request no automatic Windows updates; reversible, not tamper-proof."""
    _require_windows()
    if not _is_admin():
        raise PermissionError('Для управления Windows Update запусти FIELD от имени администратора.')
    data = _load_backup()
    if disable:
        if 'windows_update' not in data['items']:
            policy = _read('HKLM', UPDATE_KEY, 'NoAutoUpdate')
            start = _service_start()
            data['items']['windows_update'] = {
                'saved_at': datetime.now(timezone.utc).isoformat(),
                'policy': policy, 'service_start': start,
            }
            _save_backup(data)
        _write('HKLM', UPDATE_KEY, 'NoAutoUpdate', 1, winreg.REG_DWORD)
        _set_service_start(4)
        stopped = _run_sc('stop', 'wuauserv', optional=True)
        result = update_status()
        if not result['blocked']:
            raise RuntimeError('Не удалось подтвердить блокировку Windows Update. Резервная копия сохранена для отката.')
        return ('Автоматические обновления отключены политикой и настройкой службы wuauserv. '
                + ('Служба остановлена. ' if stopped else 'Служба могла остаться запущенной до перезагрузки. ')
                + 'Windows может впоследствии изменить эти параметры.')
    snapshot = data['items'].get('windows_update')
    if snapshot is None:
        raise RuntimeError('Нет резервной копии FIELD. Автоматическое восстановление чужих параметров заблокировано.')
    # Allow Windows servicing first, then restore exactly the previous policy.
    _set_service_start(snapshot['service_start'])
    _restore('HKLM', UPDATE_KEY, 'NoAutoUpdate', snapshot['policy'])
    del data['items']['windows_update']
    _save_backup(data)
    return 'Исходные настройки обновлений восстановлены. Изменение политик может потребовать перезагрузки.'
