"""Offline checks for FIELD's app icons and winget catalog."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path
from personal_lite.brand_icons import ICON_SOURCES, _validate_icon

ROOT = Path(__file__).resolve().parents[1]


class BrandedIconCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (ROOT / 'personal_lite' / 'app_installer.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        cls.apps = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id == 'AppEntry' and len(node.args) >= 3:
                cls.apps.append(tuple(v.value for v in node.args[:3]))

    def test_all_26_catalog_items_have_distinct_ids(self):
        ids = [app[1] for app in self.apps]
        self.assertEqual(len(ids), 26)
        self.assertEqual(len(set(ids)), 26)

    def test_all_apps_have_curated_sources(self):
        for _, package_id, _ in self.apps:
            self.assertIn(package_id, ICON_SOURCES)

    def test_afterburner_package(self):
        self.assertIn(('MSI Afterburner', 'Guru3D.Afterburner', 'Мониторинг'), self.apps)

    def test_bundled_brand_icons_are_real_png_images(self):
        image_dir = ROOT / 'assets' / 'app_icons'
        logos = list(image_dir.glob('*.png'))
        self.assertGreaterEqual(len(logos), 8)
        for image in logos:
            data = image.read_bytes()
            self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertGreater(len(data), 200)

    def test_untrusted_image_content_not_accepted(self):
        with self.assertRaises(ValueError):
            _validate_icon('https://example.test/test', b'<html><script>test</script></html>')


if __name__ == '__main__':
    unittest.main()
