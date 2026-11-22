from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / 'personal_lite' / 'field_ui.py').read_text('utf-8')

class NavigationContracts(unittest.TestCase):
    def test_new_pages_connected(self):
        for name in ('Главная', 'Очистка системы', 'Электропитание'):
            self.assertIn("'" + name + "'", SOURCE)
        self.assertIn('CleanerPage(self.page', SOURCE)
        self.assertIn('PowerPage(self.page', SOURCE)
        self.assertIn('DashboardPage(self.page', SOURCE)

    def test_guard_against_destroying_worker(self):
        self.assertIn("cleaner and cleaner.is_busy()", SOURCE)
        self.assertIn('installer and installer.is_installing()', SOURCE)

if __name__ == '__main__':
    unittest.main()
