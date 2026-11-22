"""Apply the FIELD advanced-settings integration without clobbering user changes."""
from pathlib import Path
import shutil
import re

ROOT = Path(__file__).resolve().parent
UI = ROOT / 'personal_lite' / 'field_ui.py'
I18N = ROOT / 'personal_lite' / 'i18n.py'
ADVANCED = ROOT / 'personal_lite' / 'advanced_settings.py'
CORE = ROOT / 'personal_lite' / 'advanced_core.py'
MARKER = "if name == 'Расширенные настройки':"


def patch(root=ROOT):
    ui = root / 'personal_lite' / 'field_ui.py'
    i18n = root / 'personal_lite' / 'i18n.py'
    if not (root / 'personal_lite' / 'advanced_settings.py').exists() or not (root / 'personal_lite' / 'advanced_core.py').exists():
        raise FileNotFoundError('Сначала скопируй advanced_settings.py и advanced_core.py в personal_lite')
    if not ui.exists() or not i18n.exists():
        raise FileNotFoundError('Нужны personal_lite/field_ui.py и personal_lite/i18n.py')

    content = ui.read_text(encoding='utf-8')
    if MARKER in content:
        print('FIELD already patched. No files changed.')
        return

    imp = 'from .advanced_settings import AdvancedSettingsPage\n'
    anchor = 'from . import core, system_tools, i18n\n'
    if anchor not in content:
        raise RuntimeError('Не найден импорт из field_ui.py; ничего не изменено')
    content = content.replace(anchor, anchor + imp, 1)

    nav_start = content.find('    NAV = [')
    nav_end = content.find(']', nav_start)
    if nav_start < 0 or nav_end < 0:
        raise RuntimeError('Не найден NAV в field_ui.py; ничего не изменено')
    nav = content[nav_start:nav_end + 1]
    if "('Расширенные настройки'" not in nav:
        if "('Автозагрузка'" not in nav:
            raise RuntimeError('Не найден пункт Автозагрузка в NAV')
        nav = nav.replace("('Автозагрузка'", "('Расширенные настройки','⚙'),('Автозагрузка'", 1)
    content = content[:nav_start] + nav + content[nav_end + 1:]

    definition = re.search(r'(?m)^    def navigate\(self,\s*name\):\s*\n', content)
    if definition is None:
        raise RuntimeError('Не найден def navigate(self, name)')
    insertion = """        advanced = getattr(self, '_advanced_page', None)
        if advanced is not None and advanced.is_busy() and name != 'Расширенные настройки':
            QMessageBox.information(self, 'FIELD', 'Дождись завершения изменения настроек.')
            return
        if name == 'Расширенные настройки':
            self.current = name
            for key, item in self.nav.items():
                item.setProperty('active', 'true' if key == name else 'false')
                item.style().unpolish(item)
                item.style().polish(item)
            clear(self.body)
            self._advanced_page = AdvancedSettingsPage(self.page, lang=self.lang)
            self.body.addWidget(self._advanced_page)
            self.body.addStretch()
            self.scroll.verticalScrollBar().setValue(0)
            self.update_chrome()
            return
        self._advanced_page = None
"""
    content = content[:definition.end()] + insertion + content[definition.end():]

    words = i18n.read_text(encoding='utf-8')
    if "'Расширенные настройки':'Advanced settings'" not in words:
        if 'EN = {' not in words:
            raise RuntimeError('Не найден словарь EN в i18n.py')
        words = words.replace('EN = {', "EN = {\n'Расширенные настройки':'Advanced settings',", 1)

    # Only replace AFTER all integration checks passed.
    backup_dir = root / '.field_patch_backups'
    backup_dir.mkdir(exist_ok=True)
    shutil.copy2(ui, backup_dir / 'field_ui.py.before_advanced.bak')
    shutil.copy2(i18n, backup_dir / 'i18n.py.before_advanced.bak')
    ui.write_text(content, encoding='utf-8')
    i18n.write_text(words, encoding='utf-8')
    ignore = root / '.gitignore'
    if ignore.exists():
        text = ignore.read_text(encoding='utf-8')
        if '.field_patch_backups/' not in text:
            ignore.write_text(text.rstrip() + '\n.field_patch_backups/\n', encoding='utf-8')
    print('OK: the Advanced settings page is added. Backups created.')


if __name__ == '__main__':
    patch()
