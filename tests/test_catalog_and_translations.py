"""Pure-Python smoke tests: no Windows or PySide6 required."""
import unittest
from personal_lite.i18n import translate
from personal_lite.catalog import APPS, PROTECTED_NAMES, TWEAKS

class FieldBasicTests(unittest.TestCase):
    def test_i18n(self):
        self.assertEqual(translate('Твики','en'),'Tweaks')
        self.assertEqual(translate('Автозагрузка','en'),'Startup')
        self.assertEqual(translate('Настройка системы','en'),'System settings')
        self.assertEqual(translate('Твики','ru'),'Твики')

    def test_safe_allowlist(self):
        app_names={name for name,_ in APPS}
        self.assertFalse(app_names.intersection(PROTECTED_NAMES))
        self.assertTrue(all('HKLM' not in t['key'].upper() for t in TWEAKS))

if __name__=='__main__': unittest.main()
