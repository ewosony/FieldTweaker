"""Windows only, allowlisted operations; no background services or elevated execution."""
from __future__ import annotations
import json, os, platform, subprocess, datetime, pathlib, threading
from .catalog import TWEAKS, APPS, PRESETS

IS_WINDOWS = os.name == 'nt'
DATA = pathlib.Path(os.getenv('LOCALAPPDATA', str(pathlib.Path.home()))) / 'PersonalLiteStudio'
STATE = DATA / 'state.json'
LOG = DATA / 'history.jsonl'
LOCK = threading.RLock()

def load_state():
    try:
        return json.loads(STATE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'registry': {}, 'startup': {}}

def save_state(data):
    DATA.mkdir(parents=True, exist_ok=True)
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(STATE)

def log(action, result, info=''):
    DATA.mkdir(parents=True, exist_ok=True)
    with LOG.open('a',encoding='utf-8') as f:
        f.write(json.dumps({'time':datetime.datetime.now().isoformat(timespec='seconds'),'action':action,'result':result,'detail':str(info)},ensure_ascii=False)+'\n')

def history():
    try:
        return [json.loads(x) for x in LOG.read_text(encoding='utf-8').splitlines()[-150:] if x.strip()][::-1]
    except (OSError, ValueError):
        return []

def require_windows():
    if not IS_WINDOWS:
        raise RuntimeError('Применение доступно только на Windows.')

def reg_get(key, name):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as h:
            value,typ = winreg.QueryValueEx(h,name)
            return {'exists':True,'value':value,'type':typ}
    except FileNotFoundError:
        return {'exists':False}

def windows_compatibility():
    """OS release/build as reported by Windows NT CurrentVersion, read-only."""
    if not IS_WINDOWS:
        return {'family': 'other', 'build': 0, 'release': '—', 'supported': False,
                'reason': 'FIELD supports Windows 10 22H2 and Windows 11 24H2/25H2.'}
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SOFTWARE\Microsoft\Windows NT\CurrentVersion') as key:
            build = int(winreg.QueryValueEx(key,'CurrentBuildNumber')[0])
            try: release = str(winreg.QueryValueEx(key,'DisplayVersion')[0])
            except OSError: release='—'
    except (OSError, ValueError):
        return {'family':'unknown','build':0,'release':'—','supported':False,
                'reason':'Unable to determine Windows build.'}
    family = '11' if build >= 22000 else '10'
    supported = (family=='10' and build>=19045) or (family=='11' and build>=26100)
    return {'family':family,'build':build,'release':release,
            'supported':supported,
            'reason':('Supported configuration' if supported else
                      'This build has not been validated; changes are blocked.')}


def tweak_compatibility(t, os_info=None):
    """Explicit conservative compatibility rules: allowlisted per version."""
    os_info = os_info or windows_compatibility()
    if not os_info['supported']:
        return False, os_info['reason']
    build = os_info['build']
    if t['id']=='seconds' and build<22621:
        return False, 'Seconds require Windows 11 build 22621 or newer.'
    if t['id']=='widgets' and build<22000:
        return False, 'The Widgets taskbar switch targets Windows 11 only.'
    if t['id']=='recentapps' and build>=22000:
        return False, 'This legacy setting is not reliable on Windows 11.'
    return True, 'Supported'

def tweak_status(t):
    ok,reason=tweak_compatibility(t)
    if not ok:return 'Не поддерживается'
    raw=reg_get(t['key'],t['name'])
    if not raw['exists']: return 'По умолчанию'
    return 'Применён' if str(raw['value']) == str(t['value']) else 'Другое значение'

def apply_tweaks(ids):
    require_windows()
    import winreg
    mapping={t['id']:t for t in TWEAKS}
    if any(i not in mapping for i in ids): raise ValueError('Неизвестный твик')
    os_info=windows_compatibility()
    invalid=[mapping[i]['title'] for i in ids if not tweak_compatibility(mapping[i],os_info)[0]]
    if invalid: raise RuntimeError('Unsupported tweaks for this Windows build: '+', '.join(invalid))
    results=[]
    with LOCK:
        state=load_state()
        state.setdefault('registry', {})
        for ident in ids:
            t=mapping[ident]
            try:
                if ident not in state['registry']:
                    state['registry'][ident]=reg_get(t['key'],t['name'])
                    save_state(state)
                with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,t['key'],0,winreg.KEY_SET_VALUE) as h:
                    typ=winreg.REG_SZ if t.get('regtype')=='sz' else winreg.REG_DWORD
                    winreg.SetValueEx(h,t['name'],0,typ,t['value'])
                results.append((t['title'],'OK'))
                log('Твик '+ident,'OK',t['title'])
            except OSError as e:
                results.append((t['title'],'ОШИБКА: '+str(e))); log('Твик '+ident,'ERROR',e)
    return results

def restore_tweaks():
    require_windows()
    import winreg
    with LOCK:
        state=load_state(); state.setdefault('registry', {}); results=[]
        for ident,previous in list(state['registry'].items()):
            t=next((x for x in TWEAKS if x['id']==ident),None)
            if not t: continue
            try:
                if previous.get('exists'):
                    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,t['key'],0,winreg.KEY_SET_VALUE) as h:
                        winreg.SetValueEx(h,t['name'],0,previous['type'],previous['value'])
                else:
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,t['key'],0,winreg.KEY_SET_VALUE) as h: winreg.DeleteValue(h,t['name'])
                    except FileNotFoundError: pass
                del state['registry'][ident]; save_state(state)
                results.append((t['title'],'Восстановлено'))
                log('Откат '+ident,'OK')
            except OSError as e:
                results.append((t['title'],'ОШИБКА: '+str(e))); log('Откат '+ident,'ERROR',e)
        return results

def powershell(script, timeout=35):
    require_windows()
    proc=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
       '[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); '+script],capture_output=True,timeout=timeout)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode('utf-8','replace')[:1000] or f'PowerShell exit {proc.returncode}')
    return proc.stdout.decode('utf-8-sig','replace').strip()

def installed_apps():
    """List only allowlisted optional apps, never critical packages."""
    names=','.join("'"+x[0]+"'" for x in APPS)
    ps=f"$names=@({names}); Get-AppxPackage | Where-Object {{$names -contains $_.Name}} | Select-Object Name,PackageFullName | ConvertTo-Json -Compress"
    raw=powershell(ps,60)
    val=json.loads(raw) if raw else []
    if isinstance(val,dict): val=[val]
    return val

def remove_apps(names):
    require_windows()
    allowed={n for n,_ in APPS}
    if any(n not in allowed for n in names): raise ValueError('Приложение отсутствует в безопасном списке')
    if not windows_compatibility()['supported']: raise RuntimeError('Unsupported Windows build. Uninstallation is blocked.')
    result=[]
    for name in names:
        try:
            # Exact package name; current user only; no provisioning or system package changes.
            ps=f"Get-AppxPackage -Name '{name}' | ForEach-Object {{ Remove-AppxPackage -Package $_.PackageFullName -ErrorAction Stop }}"
            powershell(ps,90)
            result.append((name,'Команда выполнена'))
            log('Удаление '+name,'OK','Текущий пользователь')
        except Exception as e:
            result.append((name,'ОШИБКА: '+str(e))); log('Удаление '+name,'ERROR',e)
    return result

def startup_entries():
    require_windows()
    import winreg
    places=[('Пользователь',winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run'),
            ('Компьютер',winreg.HKEY_LOCAL_MACHINE,r'Software\Microsoft\Windows\CurrentVersion\Run'),
            ('Компьютер 32-bit',winreg.HKEY_LOCAL_MACHINE,r'Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run')]
    result=[]
    for label,hive,key in places:
        try:
            with winreg.OpenKey(hive,key) as h:
                for idx in range(winreg.QueryInfoKey(h)[1]):
                    name,val,typ=winreg.EnumValue(h,idx)
                    result.append({'name':name,'command':str(val),'scope':label,'key':key,'editable':hive==winreg.HKEY_CURRENT_USER})
        except OSError: pass
    state=load_state()
    for name,entry in state.get('startup',{}).items():
        result.append({'name':name,'command':entry['value'],'scope':'Отключено Personal Lite','key':entry['key'],'editable':True,'disabled':True})
    return result

def toggle_startup(name, disable=True):
    require_windows()
    import winreg
    key=r'Software\Microsoft\Windows\CurrentVersion\Run'
    with LOCK:
        state=load_state()
        state.setdefault('startup', {})
        if disable:
            if name in state['startup']: return 'Уже отключено'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key,0,winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE) as h:
                val,typ=winreg.QueryValueEx(h,name)
                state['startup'][name]={'value':val,'type':typ,'key':key}
                save_state(state)
                winreg.DeleteValue(h,name)
            log('Автозагрузка - '+name,'OK')
            return 'Отключено'
        entry=state['startup'].get(name)
        if not entry: raise ValueError('Нет сохранённой записи')
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,key,0,winreg.KEY_SET_VALUE) as h:
            # Do not override an entry created by another application.
            try: winreg.QueryValueEx(h,name); raise RuntimeError('Запись уже существует. Восстановление отменено.')
            except FileNotFoundError: pass
            winreg.SetValueEx(h,name,0,entry['type'],entry['value'])
        del state['startup'][name]; save_state(state)
        log('Автозагрузка + '+name,'OK')
        return 'Восстановлено'

def native_windows_details():
    """Read OS, CPU, RAM and GPU via fast local Win32 interfaces; no shell needed."""
    import ctypes
    from ctypes import wintypes
    import winreg

    result = {}
    # Registry provides the installed edition without CIM startup overhead.
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SOFTWARE\Microsoft\Windows NT\CurrentVersion') as key:
            edition = str(winreg.QueryValueEx(key, 'ProductName')[0]).strip()
            if edition:
                result['edition'] = edition
    except OSError:
        pass
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            result['cpu'] = str(winreg.QueryValueEx(key, 'ProcessorNameString')[0]).strip()
    except OSError:
        pass

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [('dwLength', wintypes.DWORD), ('dwMemoryLoad', wintypes.DWORD),
                    ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
    memory = MEMORYSTATUSEX()
    memory.dwLength = ctypes.sizeof(memory)
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        result['ram'] = int(memory.ullTotalPhys)

    class DISPLAY_DEVICEW(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('DeviceName', wintypes.WCHAR * 32),
                    ('DeviceString', wintypes.WCHAR * 128), ('StateFlags', wintypes.DWORD),
                    ('DeviceID', wintypes.WCHAR * 128), ('DeviceKey', wintypes.WCHAR * 128)]
    enum = ctypes.windll.user32.EnumDisplayDevicesW
    enum.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DISPLAY_DEVICEW), wintypes.DWORD]
    enum.restype = wintypes.BOOL
    gpus = []
    for index in range(32):
        adapter = DISPLAY_DEVICEW()
        adapter.cb = ctypes.sizeof(adapter)
        if not enum(None, index, ctypes.byref(adapter), 0):
            break
        name = adapter.DeviceString.strip()
        if name and name not in gpus and not any(x in name.lower() for x in
                ('microsoft basic display', 'rdp', 'remote display', 'mirror driver')):
            gpus.append(name)
    if gpus:
        result['gpu'] = gpus
    return result


def system_info():
    """Read-only startup snapshot using fast Win32 calls, with narrow GPU fallback."""
    os_info = windows_compatibility()
    info = {
        'Windows': f"Windows {os_info['family']}" if os_info['family'] in ('10', '11') else platform.system(),
        'Редакция': '—', 'Версия': os_info['release'],
        'Процессор': '—', 'Видеокарта': '—', 'Объём ОЗУ': '—',
    }
    if not IS_WINDOWS:
        return info
    try:
        native = native_windows_details()
    except (OSError, ValueError, AttributeError):
        native = {}
    edition = str(native.get('edition') or '').replace('Майкрософт', 'Microsoft').strip()
    if edition:
        if os_info['family'] == '11' and 'Windows 10' in edition:
            edition = edition.replace('Windows 10', 'Windows 11')
        info['Редакция'] = edition
    if native.get('cpu'):
        info['Процессор'] = str(native['cpu'])
    gpus = native.get('gpu') or []
    if gpus:
        info['Видеокарта'] = ' / '.join(dict.fromkeys(gpus))
    ram = int(native.get('ram') or 0)
    if ram > 0:
        info['Объём ОЗУ'] = f'{ram/(1024 ** 3):.1f} ГБ'
    # Only use WMI when native display enumeration genuinely yields no GPU.
    if not gpus:
        try:
            raw = powershell("@(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) | ConvertTo-Json -Compress", 8)
            names = json.loads(raw)
            if isinstance(names, str): names = [names]
            names = [n for n in names if isinstance(n, str) and
                     'Microsoft Basic Display' not in n]
            if names: info['Видеокарта'] = ' / '.join(dict.fromkeys(names))
        except (ValueError, TypeError, OSError, RuntimeError, subprocess.SubprocessError):
            pass
    return info

def export_profile(path, ids):
    valid={t['id'] for t in TWEAKS}
    if any(i not in valid for i in ids): raise ValueError('Неизвестный твик')
    pathlib.Path(path).write_text(json.dumps({'format':'personal-lite-profile-v1','tweaks':list(ids)},ensure_ascii=False,indent=2),encoding='utf-8')

def import_profile(path):
    obj=json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    valid={t['id'] for t in TWEAKS}
    if obj.get('format')!='personal-lite-profile-v1' or not isinstance(obj.get('tweaks'),list) or any(i not in valid for i in obj['tweaks']):
        raise ValueError('Неподдерживаемый или некорректный профиль')
    return obj['tweaks']
