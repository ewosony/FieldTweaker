"""Offline unit tests; never interact with the host Windows registry."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from personal_lite import advanced_core as core

class ReversibleSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        core.STATE_DIR = Path(self.tmp.name)
        core.BACKUP_FILE = core.STATE_DIR / 'settings.json'
        self.values = {}
        self.start = 3
        self._orig = (core._require_windows, core._is_admin, core._read, core._write, core._restore, core._service_start, core._set_service_start, core._run_sc, core.winreg)
        core._require_windows = lambda: None
        core._is_admin = lambda: True
        core.winreg = SimpleNamespace(REG_DWORD=4)
        core._read = self.read
        core._write = self.write
        core._restore = self.restore
        core._service_start = lambda: self.start
        core._set_service_start = self.set_start
        core._run_sc = lambda *a,**kw: True

    def tearDown(self):
        (core._require_windows, core._is_admin, core._read, core._write, core._restore, core._service_start, core._set_service_start, core._run_sc, core.winreg) = self._orig

    def read(self, root, key, name):
        return self.values.get((root,key,name), {'exists':False}).copy()

    def write(self,root,key,name,value,kind):
        self.values[(root,key,name)] = {'exists':True,'value':value,'type':kind}

    def restore(self,root,key,name,previous):
        if previous['exists']:
            self.values[(root,key,name)] = previous.copy()
        else:
            self.values.pop((root,key,name),None)

    def set_start(self,start):
        self.start = start

    def test_update_restoration(self):
        self.write('HKLM',core.UPDATE_KEY,'NoAutoUpdate',0,4)
        core.set_windows_updates_disabled(True)
        self.assertTrue(core.update_status()['blocked'])
        self.assertTrue(core.update_status()['can_restore'])
        core.set_windows_updates_disabled(False)
        self.assertEqual(self.start, 3)
        self.assertEqual(self.read('HKLM',core.UPDATE_KEY,'NoAutoUpdate')['value'],0)
        self.assertFalse(core.update_status()['can_restore'])

    def test_feature_exact_previous_values(self):
        reg = core.FEATURES['gamedvr']['values']
        self.write(reg[0][0], reg[0][1], reg[0][2], 1, 4)
        core.set_feature('gamedvr', True)
        self.assertTrue(core.feature_status('gamedvr')['applied'])
        core.set_feature('gamedvr', False)
        self.assertEqual(self.read(*reg[0][:3])['value'],1)
        self.assertFalse(self.read(*reg[1][:3])['exists'])

    def test_no_backup_blocks_restore(self):
        with self.assertRaises(RuntimeError):
            core.set_windows_updates_disabled(False)



if __name__ == '__main__': unittest.main()
