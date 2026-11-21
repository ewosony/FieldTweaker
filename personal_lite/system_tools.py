"""Read-only process and file-lock inspection; optional graceful stop of own non-system processes.
The file-lock scanner uses Microsoft's documented Restart Manager API. It does not close
foreign handles, change permissions, or bypass protected Windows processes.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import getpass
import os
from pathlib import Path
import sys

try:
    import psutil
except ImportError:
    psutil = None

PROTECTED_NAMES = {
    'system', 'registry', 'smss.exe', 'csrss.exe', 'wininit.exe', 'winlogon.exe',
    'services.exe', 'lsass.exe', 'svchost.exe', 'securityhealthservice.exe',
    'msmpeng.exe', 'explorer.exe', 'dwm.exe', 'fontdrvhost.exe',
    'startmenuexperiencehost.exe', 'sihost.exe', 'taskhostw.exe',
    'searchhost.exe', 'shellexperiencehost.exe', 'spoolsv.exe',
}


def list_processes():
    if psutil is None:
        raise RuntimeError('Не установлен psutil. Выполни: python -m pip install -r requirements.txt')
    records = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'status', 'exe']):
        try:
            row = proc.info
            memory = row.get('memory_info')
            records.append({
                'pid': row['pid'], 'name': row.get('name') or '—',
                'user': row.get('username') or '—',
                'memory_mb': round(memory.rss / 1024**2, 1) if memory else 0,
                'status': row.get('status') or '—',
                'exe': row.get('exe') or '',
            })
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
    return sorted(records, key=lambda p: p['memory_mb'], reverse=True)


def is_safe_target(pid: int):
    if psutil is None:
        return False, 'Отсутствует psutil.'
    if pid <= 4 or pid in (os.getpid(), os.getppid()):
        return False, 'Системный или собственный процесс FIELD.'
    try:
        proc = psutil.Process(pid)
        if proc.name().lower() in PROTECTED_NAMES:
            return False, 'Защищённый системный компонент Windows.'
        owner = proc.username()
        # Windows username includes optional DOMAIN\username prefix.
        if owner.rsplit('\\', 1)[-1].casefold() != getpass.getuser().casefold():
            return False, 'Процесс принадлежит другому пользователю или системе.'
        return True, ''
    except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
        return False, str(exc)


def close_user_process(pid: int):
    """Terminate the current user's non-system process after explicit confirmation."""
    ok, reason = is_safe_target(pid)
    if not ok:
        raise PermissionError(reason)
    proc = psutil.Process(pid)
    stamp = proc.create_time()
    ok, reason = is_safe_target(pid)
    if not ok or psutil.Process(pid).create_time() != stamp:
        raise RuntimeError(reason or 'Процесс изменился — обнови список.')
    proc.terminate()  # On Windows psutil uses TerminateProcess: forceful, not a graceful WM_CLOSE.
    try:
        proc.wait(timeout=3)
        return f'Процесс {pid} завершён. Несохранённые данные могли быть потеряны.'
    except psutil.TimeoutExpired:
        return f'Запрос завершения процесса {pid} отправлен, но процесс пока работает.'


# Windows Restart Manager -- locate processes using a selected file; no unlock/handle closure.
CCH_RM_SESSION_KEY = 32
CCH_RM_MAX_APP_NAME = 255
CCH_RM_MAX_SVC_NAME = 63
ERROR_MORE_DATA = 234

class RM_UNIQUE_PROCESS(ctypes.Structure):
    _fields_ = [('dwProcessId', wintypes.DWORD), ('ProcessStartTime', wintypes.FILETIME)]

class RM_PROCESS_INFO(ctypes.Structure):
    _fields_ = [
        ('Process', RM_UNIQUE_PROCESS),
        ('strAppName', wintypes.WCHAR * (CCH_RM_MAX_APP_NAME + 1)),
        ('strServiceShortName', wintypes.WCHAR * (CCH_RM_MAX_SVC_NAME + 1)),
        ('ApplicationType', wintypes.DWORD), ('AppStatus', wintypes.ULONG),
        ('TSSessionId', wintypes.DWORD), ('bRestartable', wintypes.BOOL),
    ]


def find_file_lockers(path: str):
    if sys.platform != 'win32':
        raise OSError('Поиск блокировок работает только в Windows.')
    file = Path(path).expanduser().resolve()
    if not file.exists() or not file.is_file():
        raise ValueError('Выбери существующий файл. Поиск папок пока не поддерживается.')
    rm = ctypes.WinDLL('rstrtmgr', use_last_error=True)
    rm.RmStartSession.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, wintypes.LPWSTR]
    rm.RmStartSession.restype = wintypes.DWORD
    rm.RmRegisterResources.argtypes = [wintypes.DWORD, wintypes.UINT, ctypes.POINTER(wintypes.LPCWSTR), wintypes.UINT, ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p]
    rm.RmRegisterResources.restype = wintypes.DWORD
    rm.RmGetList.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.UINT), ctypes.POINTER(wintypes.UINT), ctypes.POINTER(RM_PROCESS_INFO), ctypes.POINTER(wintypes.DWORD)]
    rm.RmGetList.restype = wintypes.DWORD
    rm.RmEndSession.argtypes = [wintypes.DWORD]
    rm.RmEndSession.restype = wintypes.DWORD
    h = wintypes.DWORD(0)
    key = ctypes.create_unicode_buffer(CCH_RM_SESSION_KEY + 1)
    rc = rm.RmStartSession(ctypes.byref(h), 0, key)
    if rc:
        raise OSError(f'Не удалось начать поиск блокировки. Код Windows: {rc}')
    try:
        paths = (wintypes.LPCWSTR * 1)(str(file))
        rc = rm.RmRegisterResources(h, 1, paths, 0, None, 0, None)
        if rc:
            raise OSError(f'Не удалось проверить файл. Код Windows: {rc}')
        needed, count, reasons = wintypes.UINT(0), wintypes.UINT(0), wintypes.DWORD(0)
        rc = rm.RmGetList(h, ctypes.byref(needed), ctypes.byref(count), None, ctypes.byref(reasons))
        if rc == 0:
            return []
        if rc != ERROR_MORE_DATA:
            raise OSError(f'Ошибка запроса процессов. Код Windows: {rc}')
        for _ in range(3):
            capacity = max(needed.value, 1)
            items = (RM_PROCESS_INFO * capacity)()
            count = wintypes.UINT(capacity)
            rc = rm.RmGetList(h, ctypes.byref(needed), ctypes.byref(count), items, ctypes.byref(reasons))
            if rc == 0:
                return [
                    {'pid': items[i].Process.dwProcessId,
                     'name': items[i].strAppName or items[i].strServiceShortName or 'Неизвестно',
                     'restartable': bool(items[i].bRestartable)}
                    for i in range(count.value)
                ]
            if rc != ERROR_MORE_DATA:
                raise OSError(f'Ошибка получения списка. Код Windows: {rc}')
        raise RuntimeError('Список изменяется слишком быстро, повтори проверку.')
    finally:
        rm.RmEndSession(h)
