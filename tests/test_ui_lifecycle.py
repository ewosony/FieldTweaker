"""No-GUI regression contracts; full Qt navigation smoke tests are in MANUAL_TESTS.md."""
import ast
import unittest
from pathlib import Path
from personal_lite import i18n

ROOT = Path(__file__).resolve().parents[1]
UI = (ROOT / 'personal_lite' / 'field_ui.py').read_text('utf-8')
INSTALLER = (ROOT / 'personal_lite' / 'app_installer.py').read_text('utf-8')

class UiLifecycleTests(unittest.TestCase):
    def test_installer_is_embedded(self):
        self.assertIn("'Установка ПО': ('_installer_page'", UI)
        self.assertIn('self.body.addWidget(page)', UI)
        self.assertNotIn('AppInstallerDialog(', UI)
    def test_alive_guard_before_process_call(self):
        self.assertIn('isValid(page)', UI)
        self.assertIn('installer and installer.is_installing()', UI)
        self.assertIn('isValid(self.process)', INSTALLER)
        self.assertIn('def closeEvent(self, event):', UI)
    def test_language_and_version(self):
        self.assertEqual(i18n.translate('Установка ПО', 'en'), 'App installer')
        self.assertEqual(i18n.translate('Расширенные настройки', 'en'), 'Advanced settings')
        self.assertIn("VERSION = '1.2.0'", UI)
        self.assertIn('def set_language(self, language: str)', INSTALLER)
    def test_package_ids_are_declarative(self):
        tree = ast.parse(INSTALLER)
        names = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        self.assertIn('AppInstallerPage', [c.name for c in names])

if __name__ == '__main__': unittest.main()
