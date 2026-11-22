"""Real Qt regression test (skipped when PySide6 is not installed)."""
import os
import unittest

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QProcess
    from shiboken6 import isValid
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False


@unittest.skipUnless(QT_AVAILABLE, 'PySide6 is required for interactive Qt smoke test')
class NavigationSmokeTests(unittest.TestCase):
    def test_reopen_installer_after_page_deleted(self):
        from personal_lite.field_ui import FieldStudio

        app = QApplication.instance() or QApplication([])
        window = FieldStudio()
        try:
            window.navigate('Установка ПО')
            first = window._installer_page
            self.assertTrue(isValid(first))
            window.navigate('Сведения о системе')
            app.processEvents()  # deleteLater() destroys C++ widget + its QProcess
            self.assertIsNone(window._installer_page)
            window.navigate('Твики')
            window.navigate('Установка ПО')
            second = window._installer_page
            self.assertTrue(isValid(second))
            self.assertIsNot(first, second)
            self.assertFalse(second.is_installing())
            window.change_language('en')
            self.assertEqual(second.lang, 'en')
            window.toggle_theme()
            self.assertIs(window._installer_page, second)
            window.navigate('Расширенные настройки')
            app.processEvents()
            window.navigate('Установка ПО')
            self.assertFalse(window._installer_page.is_installing())
        finally:
            window.close()
            app.processEvents()


if __name__ == '__main__':
    unittest.main()
