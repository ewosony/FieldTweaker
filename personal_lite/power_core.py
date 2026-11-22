"""Use Windows' existing power plans; preserve and restore the previous active plan."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

STATE_FILE = Path(os.environ.get('APPDATA', str(Path.home()))) / 'FIELD' / 'power_plan_previous.json'
GUID = re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I)
KNOWN = {
    '381b4222-f694-41f0-9685-ff5bb260df2e': ('Сбалансированный', 'Balanced'),
    'a1841308-3541-4fab-bc81-f71556f20b4a': ('Экономия энергии', 'Power saver'),
    '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c': ('Высокая производительность', 'High performance'),
    'e9a42b02-d5df-448d-aa00-03f14749eb61': ('Максимальная производительность', 'Ultimate performance'),
}


def run_powercfg(*args):
    if os.name != 'nt':
        raise RuntimeError('Power plans are only available on Windows')
    opts = {'capture_output': True, 'text': True, 'errors': 'replace', 'timeout': 20}
    if hasattr(subprocess, 'CREATE_NO_WINDOW'):
        opts['creationflags'] = subprocess.CREATE_NO_WINDOW
    result = subprocess.run(['powercfg.exe', *args], **opts)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or f'powercfg exited with {result.returncode}').strip())
    return result.stdout


def parse_plans(output):
    plans = []
    for line in output.splitlines():
        m = GUID.search(line)
        if not m:
            continue
        guid = m.group(0).lower()
        after = line[m.end():].strip()
        plan_name = re.search(r'\(([^)]+)\)', after)
        name = plan_name.group(1) if plan_name else (KNOWN.get(guid) or (guid, guid))[1]
        plans.append({'guid': guid, 'name': name, 'active': '*' in after})
    return plans


def list_plans():
    return parse_plans(run_powercfg('/list'))


def active_guid():
    match = GUID.search(run_powercfg('/getactivescheme'))
    if not match:
        raise RuntimeError('Unable to read the current power plan')
    return match.group(0).lower()


def apply_plan(guid):
    if not GUID.fullmatch(guid):
        raise ValueError('Invalid power plan GUID')
    options = {p['guid'] for p in list_plans()}
    if guid.lower() not in options:
        raise RuntimeError('This power plan is not available on this computer')
    old = active_guid()
    if guid.lower() == old:
        return 'Already active'
    # On first change keep the original plan for a single-click rollback.
    if not can_restore():
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({'previous': old}), encoding='utf-8')
    run_powercfg('/setactive', guid)
    return 'Power plan changed'


def can_restore():
    try:
        return bool(GUID.fullmatch(json.loads(STATE_FILE.read_text('utf-8'))['previous']))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def restore_plan():
    if not can_restore():
        raise RuntimeError('No saved previous power plan')
    guid = json.loads(STATE_FILE.read_text('utf-8'))['previous']
    if guid not in {p['guid'] for p in list_plans()}:
        raise RuntimeError('Original power plan is not available')
    run_powercfg('/setactive', guid)
    STATE_FILE.unlink()
    return 'Previous power plan restored'
