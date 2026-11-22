"""Safe offline tests: don't touch user's Windows caches or power settings."""
import os
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from personal_lite import cleaner_core, power_core


class CleanerCoreTests(unittest.TestCase):
    def test_only_scanned_old_files_are_deleted(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            old = root / 'old.tmp'
            fresh = root / 'fresh.tmp'
            old.write_bytes(b'abc')
            fresh.write_bytes(b'new data')
            old_when = time.time() - 4 * 86400
            os.utime(old, (old_when, old_when))
            with patch.object(cleaner_core, 'candidate_roots', return_value=[root]):
                result = cleaner_core.scan(['temp'])
            self.assertEqual(result.count('temp'), 1)
            self.assertEqual(result.size('temp'), 3)
            cleaned = cleaner_core.clean(result, ['temp'])
            self.assertEqual(cleaned['deleted'], 1)
            self.assertFalse(old.exists())
            self.assertTrue(fresh.exists())

    def test_changed_file_not_deleted(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            f = root / 'old.log'
            f.write_text('outdated')
            older = time.time() - 4 * 86400
            os.utime(f, (older, older))
            with patch.object(cleaner_core, 'candidate_roots', return_value=[root]):
                result = cleaner_core.scan(['temp'])
            f.write_text('new important text')
            self.assertEqual(cleaner_core.clean(result, ['temp'])['deleted'], 0)
            self.assertTrue(f.exists())

    def test_unknown_category_not_allowed(self):
        with self.assertRaises(ValueError):
            cleaner_core.scan(['Documents'])


class PowerCoreTests(unittest.TestCase):
    def test_parse_powercfg_list(self):
        data = ('Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced) *\n'
                'Power Scheme GUID: a1841308-3541-4fab-bc81-f71556f20b4a  (Power saver)\n')
        items = power_core.parse_plans(data)
        self.assertEqual(len(items), 2)
        self.assertTrue(items[0]['active'])
        self.assertEqual(items[1]['name'], 'Power saver')

    def test_reject_invalid_guid(self):
        with self.assertRaises(ValueError):
            power_core.apply_plan('not-a-guid')


if __name__ == '__main__':
    unittest.main()
