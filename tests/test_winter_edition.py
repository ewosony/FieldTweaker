"""Version 1.2.1 festive mode contracts (no Qt needed for static checks)."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = (ROOT / 'personal_lite' / 'field_ui.py').read_text(encoding='utf-8')
OVERLAY = (ROOT / 'personal_lite' / 'winter_effects.py').read_text(encoding='utf-8')
DASH = (ROOT / 'personal_lite' / 'dashboard_page.py').read_text(encoding='utf-8')


class WinterEditionSourceTests(unittest.TestCase):
    def test_winter_overlay_compiles(self):
        ast.parse(OVERLAY)
        ast.parse(UI)
        ast.parse(DASH)

    def test_snow_has_no_user_input_or_network_requirements(self):
        tree = ast.parse(OVERLAY)
        imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        self.assertNotIn('requests', imported)
        self.assertNotIn('urllib.request', imported)
        self.assertIn('WA_TransparentForMouseEvents', OVERLAY)
        self.assertIn('self._timer.stop()', OVERLAY)
        self.assertIn('def _paint_garlands', OVERLAY)

    def test_persistent_toggle_and_existing_modules(self):
        self.assertIn("VERSION = '1.2.1'", UI)
        self.assertIn("'winter_enabled':self.winter_enabled", UI)
        self.assertIn('def toggle_winter', UI)
        self.assertIn('WINTER_DARK', UI)
        self.assertIn('WINTER_LIGHT', UI)
        self.assertIn('AppInstallerPage', UI)
        self.assertIn('CleanerPage', UI)
        self.assertIn('PowerPage', UI)

    def test_dashboard_has_seasonal_copy(self):
        self.assertIn('def set_winter_enabled', DASH)
        self.assertIn('W I N T E R   E D I T I O N', DASH)
        self.assertIn('winter=self.winter_enabled', UI)


if __name__ == '__main__':
    unittest.main()
