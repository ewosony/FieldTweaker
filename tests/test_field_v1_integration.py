import ast
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "personal_lite" / "field_ui.py"
SOURCE = FILE.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
CLASS = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == "FieldStudio")
METHODS = {n.name for n in CLASS.body if isinstance(n, ast.FunctionDef)}

class FieldVersionTwelveTests(unittest.TestCase):
    def test_system_refresh_exists(self):
        self.assertIn("fetch_system_details", METHODS)
        self.assertIn("render_system_details", METHODS)
    def test_duplicate_diagnostics_not_in_nav(self):
        nav = next(n for n in CLASS.body if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "NAV" for x in n.targets))
        names = [x.elts[0].value for x in nav.value.elts]
        self.assertIn("Сведения о системе", names)
        self.assertNotIn("Диагностика", names)
    def test_version_and_footer(self):
        self.assertIn("side.addWidget(block('FIELD   /   '+VERSION", SOURCE)
        self.assertIn("VERSION = '1.2.1'", SOURCE)
        self.assertNotIn("self.bottom_label", SOURCE)

if __name__ == "__main__":
    unittest.main()
