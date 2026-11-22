"""FIELD 1.2 — embedded app installer, with a safe QProcess lifecycle.

The page is part of FIELD's central navigation, not a separate window.
No installation starts until the user explicitly chooses packages and confirms.
"""
from __future__ import annotations

import shutil
import sys
import re
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QProcess, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget, QComboBox, QProgressBar,
)
from shiboken6 import isValid


@dataclass(frozen=True)
class AppEntry:
    name: str
    package_id: str
    category: str


APPS = (
    AppEntry('Google Chrome', 'Google.Chrome', 'Браузеры'),
    AppEntry('Mozilla Firefox', 'Mozilla.Firefox', 'Браузеры'),
    AppEntry('Brave', 'Brave.Brave', 'Браузеры'),
    AppEntry('Discord', 'Discord.Discord', 'Общение'),
    AppEntry('Telegram', 'Telegram.TelegramDesktop', 'Общение'),
    AppEntry('Steam', 'Valve.Steam', 'Игры'),
    AppEntry('Epic Games Launcher', 'EpicGames.EpicGamesLauncher', 'Игры'),
    AppEntry('OBS Studio', 'OBSProject.OBSStudio', 'Медиа'),
    AppEntry('VLC media player', 'VideoLAN.VLC', 'Медиа'),
    AppEntry('7-Zip', '7zip.7zip', 'Утилиты'),
    AppEntry('Notepad++', 'Notepad++.Notepad++', 'Утилиты'),
    AppEntry('Microsoft PowerToys', 'Microsoft.PowerToys', 'Утилиты'),
    AppEntry('Visual Studio Code', 'Microsoft.VisualStudioCode', 'Разработка'),
    AppEntry('Git', 'Git.Git', 'Разработка'),
    AppEntry('Happ', 'Happ.Happ', 'Сеть'),
    AppEntry('Throne', 'Throneproj.Throne', 'Сеть'),
    AppEntry('MSI Afterburner', 'Guru3D.Afterburner', 'Мониторинг'),
    AppEntry('HWiNFO', 'REALiX.HWiNFO', 'Мониторинг'),
    AppEntry('HWMonitor', 'CPUID.HWMonitor', 'Мониторинг'),
    AppEntry('Everything', 'voidtools.Everything', 'Утилиты'),
    AppEntry('ShareX', 'ShareX.ShareX', 'Утилиты'),
    AppEntry('qBittorrent', 'qBittorrent.qBittorrent', 'Сеть'),
    AppEntry('Spotify', 'Spotify.Spotify', 'Медиа'),
    AppEntry('Audacity', 'Audacity.Audacity', 'Медиа'),
    AppEntry('Bitwarden', 'Bitwarden.Bitwarden', 'Безопасность'),
    AppEntry('KeePassXC', 'KeePassXCTeam.KeePassXC', 'Безопасность'),
)

CATEGORY_EN = {
    'Браузеры': 'Browsers', 'Общение': 'Communication', 'Игры': 'Games',
    'Медиа': 'Media', 'Утилиты': 'Utilities', 'Разработка': 'Development',
    'Сеть': 'Network', 'Мониторинг': 'Monitoring', 'Безопасность': 'Security',
}

# Local, intentionally non-trademark fallback initials. Real PNG/SVG logos,
# when available, are loaded from assets/app_icons/<winget-id>.png/.svg.
ICON_BADGES = {
    'Google.Chrome': ('G', '#E94335'),
    'Mozilla.Firefox': ('F', '#FF7139'),
    'Brave.Brave': ('B', '#FB542B'),
    'Discord.Discord': ('D', '#5865F2'),
    'Telegram.TelegramDesktop': ('T', '#249BD7'),
    'Valve.Steam': ('S', '#1B587C'),
    'EpicGames.EpicGamesLauncher': ('E', '#252A35'),
    'OBSProject.OBSStudio': ('O', '#655585'),
    'VideoLAN.VLC': ('V', '#F28C28'),
    '7zip.7zip': ('7z', '#4C966D'),
    'Notepad++.Notepad++': ('N+', '#62A843'),
    'Microsoft.PowerToys': ('P', '#2178C6'),
    'Microsoft.VisualStudioCode': ('VS', '#1879B9'),
    'Git.Git': ('git', '#EB4D30'),
    'Happ.Happ': ('H', '#3F86D8'),
    'Throneproj.Throne': ('T', '#805CC9'),
    'Guru3D.Afterburner': ('MSI', '#2BA46A'),
    'REALiX.HWiNFO': ('HW', '#2F85CD'),
    'CPUID.HWMonitor': ('HM', '#4982CE'),
    'voidtools.Everything': ('E', '#F3A900'),
    'ShareX.ShareX': ('SX', '#377AB8'),
    'qBittorrent.qBittorrent': ('qB', '#396DAB'),
    'Spotify.Spotify': ('S', '#1DB954'),
    'Audacity.Audacity': ('A', '#2888D5'),
    'Bitwarden.Bitwarden': ('BW', '#175DDC'),
    'KeePassXCTeam.KeePassXC': ('K', '#69A742'),
}


def _resource_dir() -> Path:
    # In a PyInstaller build, included assets are inside the extracted bundle.
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent)) / 'assets'


def _fallback_icon(package_id: str, size: int = 40) -> QPixmap:
    text, color = ICON_BADGES.get(package_id, ('?', '#566E85'))
    scale = 3
    pix = QPixmap(size * scale, size * scale)
    pix.fill(QColor('transparent'))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawRoundedRect(pix.rect(), 10 * scale, 10 * scale)
    painter.setPen(QColor('#FFFFFF'))
    font = QFont('Segoe UI')
    font.setBold(True)
    font.setPixelSize((16 if len(text) <= 2 else 13) * scale)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, text)
    painter.end()
    return pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


def app_icon(package_id: str, size: int = 40) -> QPixmap:
    """Use downloaded real logos first, then bundled brand icons, then initials."""
    from .brand_icons import icon_cache_dir, load_svg_pixmap
    for directory in (icon_cache_dir(), _resource_dir() / 'app_icons'):
        for ext in ('png', 'svg', 'ico', 'jpg'):
            path = directory / f'{package_id}.{ext}'
            if not path.is_file():
                continue
            if ext == 'svg':
                image = load_svg_pixmap(path, size)
            else:
                image = QIcon(str(path)).pixmap(size, size)
            if not image.isNull():
                return image
    return _fallback_icon(package_id, size)


class AppInstallerPage(QWidget):
    """Non-blocking winget queue; the page stays alive during a running job."""

    def __init__(self, parent=None, lang: str = 'ru'):
        super().__init__(parent)
        self.lang = lang if lang in ('ru', 'en') else 'ru'
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)

        self.check_process = QProcess(self)
        self.check_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.check_process.finished.connect(self._list_finished)
        self.check_process.errorOccurred.connect(self._list_error)
        self.installed_ids: set[str] | None = None
        self.indicators: dict[str, QLabel] = {}
        self.logos: dict[str, QLabel] = {}
        self.operation = 'install'

        self.pending: list[AppEntry] = []
        self.current: AppEntry | None = None
        self.rows: list[tuple[AppEntry, QCheckBox, QWidget]] = []
        self.category_headers: dict[str, QLabel] = {}
        self._cancel_requested = False
        self._done_count = 0
        self._total_count = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)
        self.eyebrow = QLabel()
        self.eyebrow.setObjectName('eyebrow')
        root.addWidget(self.eyebrow)
        self.heading = QLabel()
        self.heading.setStyleSheet('font-size: 27px; font-weight: 750;')
        root.addWidget(self.heading)
        self.description = QLabel()
        self.description.setObjectName('muted')
        self.description.setWordWrap(True)
        root.addWidget(self.description)

        toolbar = QFrame()
        toolbar.setObjectName('toolbar')
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(14, 12, 14, 12)
        self.search = QLineEdit()
        self.search.textChanged.connect(self._filter)
        toolbar_layout.addWidget(self.search, 1)
        self.category_filter = QComboBox()
        self.category_filter.addItem('Все категории', '')
        for category in CATEGORY_EN:
            self.category_filter.addItem(category, category)
        self.category_filter.currentIndexChanged.connect(lambda _: self._filter(self.search.text()))
        toolbar_layout.addWidget(self.category_filter)
        self.selection_label = QLabel()
        self.selection_label.setObjectName('muted')
        toolbar_layout.addWidget(self.selection_label)
        root.addWidget(toolbar)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setMinimumHeight(240)
        content = QWidget()
        content.setObjectName('installerContent')
        self.apps_layout = QVBoxLayout(content)
        self.apps_layout.setContentsMargins(4, 4, 4, 4)
        self.apps_layout.setSpacing(9)
        self.apps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for category in dict.fromkeys(a.category for a in APPS):
            category_label = QLabel(category)
            category_label.setObjectName('eyebrow')
            category_label.setStyleSheet('font-size: 12px; font-weight: 750; margin-top: 9px;')
            self.apps_layout.addWidget(category_label)
            self.category_headers[category] = category_label
            for app in (item for item in APPS if item.category == category):
                row = QFrame()
                row.setObjectName('row')
                line = QHBoxLayout(row)
                line.setContentsMargins(15, 10, 15, 10)
                line.setSpacing(14)
                logo = QLabel()
                logo.setFixedSize(40, 40)
                logo.setPixmap(app_icon(app.package_id))
                logo.setToolTip(app.name)
                self.logos[app.package_id] = logo
                line.addWidget(logo)
                label = QCheckBox(app.name)
                label.setToolTip(f'winget: {app.package_id}')
                label.toggled.connect(self._update_selection)
                line.addWidget(label, 1)
                state = QLabel('—')
                state.setObjectName('muted')
                line.addWidget(state)
                self.indicators[app.package_id] = state
                self.apps_layout.addWidget(row)
                self.rows.append((app, label, row))
        area.setWidget(content)
        root.addWidget(area, 1)

        actions = QHBoxLayout()
        self.install_button = QPushButton()
        self.install_button.setObjectName('primary')
        self.install_button.clicked.connect(self.install_selected)
        actions.addWidget(self.install_button)
        self.upgrade_button = QPushButton()
        self.upgrade_button.clicked.connect(self.upgrade_selected)
        actions.addWidget(self.upgrade_button)
        self.cancel_button = QPushButton()
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        actions.addWidget(self.cancel_button)
        actions.addStretch(1)
        root.addLayout(actions)
        actions = QHBoxLayout()
        self.detect_button = QPushButton()
        self.detect_button.clicked.connect(self.detect_installed)
        actions.addWidget(self.detect_button)
        self.icon_button = QPushButton()
        self.icon_button.clicked.connect(self.refresh_logos)
        actions.addWidget(self.icon_button)
        self.preset_button = QPushButton()
        self.preset_button.clicked.connect(self.select_basics)
        actions.addWidget(self.preset_button)
        actions.addStretch(1)
        root.addLayout(actions)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        root.addWidget(self.progress)

        self.status = QLabel()
        self.status.setObjectName('muted')
        root.addWidget(self.status)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(115)
        self.log.setMaximumHeight(170)
        root.addWidget(self.log)
        self.set_language(self.lang)
        # Image retrieval runs in daemon threads; Qt objects are only updated
        # from this timer on the GUI thread, avoiding QThread lifecycle issues.
        self._icon_timer = QTimer(self)
        self._icon_timer.timeout.connect(self._update_logo_images)
        self._icon_timer.start(1200)
        QTimer.singleShot(350, self._schedule_missing_icons)

    def _schedule_missing_icons(self):
        from .brand_icons import start_icon_downloads
        start_icon_downloads([app.package_id for app in APPS], bundled_dir=_resource_dir() / 'app_icons')

    def refresh_logos(self):
        from .brand_icons import start_icon_downloads
        started = start_icon_downloads([app.package_id for app in APPS], refresh=True)
        self._icon_timer.start(1200)
        if not started:
            self.status.setText(self._tr('Загрузка значков уже идёт.', 'Icons are already downloading.'))
        else:
            self.status.setText(self._tr('Загружаем значки из открытых источников…', 'Downloading brand icons…'))

    def _update_logo_images(self):
        from .brand_icons import downloads_active, icon_cache_dir
        for app in APPS:
            self.logos[app.package_id].setPixmap(app_icon(app.package_id))
        if not downloads_active():
            self._icon_timer.stop()

    def _tr(self, ru: str, en: str) -> str:
        return en if self.lang == 'en' else ru

    def set_language(self, language: str) -> None:
        self.lang = 'en' if language == 'en' else 'ru'
        self.eyebrow.setText('FIELD / SOFTWARE')
        self.heading.setText(self._tr('Установка программ', 'App installer'))
        self.description.setText(self._tr(
            'Выбери приложения. FIELD установит их через Windows Package Manager (winget) после подтверждения.',
            'Choose apps. FIELD installs them through Windows Package Manager (winget) after confirmation.',
        ))
        self.search.setPlaceholderText(self._tr('Поиск по названию или категории…', 'Search apps or categories…'))
        for category, label in self.category_headers.items():
            label.setText(CATEGORY_EN.get(category, category) if self.lang == 'en' else category)
        self.install_button.setText(self._tr('Установить выбранные', 'Install selected'))
        self.upgrade_button.setText(self._tr('Обновить выбранные', 'Upgrade selected'))
        self.detect_button.setText(self._tr('Проверить установленные', 'Detect installed'))
        self.preset_button.setText(self._tr('Базовый набор', 'Essentials'))
        self.icon_button.setText(self._tr('Обновить иконки', 'Refresh icons'))
        self.category_filter.setItemText(0, self._tr('Все категории', 'All categories'))
        for i, category in enumerate(CATEGORY_EN, 1):
            self.category_filter.setItemText(i, CATEGORY_EN[category] if self.lang == 'en' else category)
        for app in APPS:
            self._set_indicator(app.package_id)
        self.cancel_button.setText(self._tr('Остановить', 'Stop'))
        if not self.is_installing():
            self.status.setText(self._tr('Готово к установке', 'Ready to install'))
        self._update_selection()

    def _set_indicator(self, package_id):
        state = self.indicators[package_id]
        if self.installed_ids is None:
            state.setText('—')
        else:
            found = package_id.casefold() in self.installed_ids
            state.setText(self._tr('Установлено', 'Installed') if found else self._tr('Не найдено', 'Not found'))

    def is_checking(self) -> bool:
        try:
            return bool(isValid(self.check_process) and
                        self.check_process.state() != QProcess.ProcessState.NotRunning)
        except RuntimeError:
            return False

    def detect_installed(self):
        if self.is_installing() or self.is_checking():
            return
        if sys.platform != 'win32' or not shutil.which('winget'):
            QMessageBox.warning(self, 'FIELD', self._tr('winget недоступен.', 'winget is unavailable.'))
            return
        self.detect_button.setEnabled(False)
        self.status.setText(self._tr('Проверка установленных программ…', 'Checking installed apps…'))
        self.check_process.start('winget', ['list', '--disable-interactivity'])

    def _list_finished(self, code, status):
        output = bytes(self.check_process.readAllStandardOutput()).decode('utf-8', errors='replace')
        self.detect_button.setEnabled(True)
        if code != 0:
            self.installed_ids = None
            self.status.setText(self._tr('Не удалось получить список winget.', 'Could not retrieve winget app list.'))
            return
        # Match full winget IDs; never confuse e.g. Git.Git and other packages.
        found = set()
        for row in output.splitlines():
            for app in APPS:
                if re.search(r'(?<![\w.])' + re.escape(app.package_id) + r'(?![\w.])', row, re.I):
                    found.add(app.package_id.casefold())
        self.installed_ids = found
        for app in APPS:
            self._set_indicator(app.package_id)
        self.status.setText(self._tr(f'Найдено в каталоге: {len(found)}',
                                      f'Detected from catalog: {len(found)}'))

    def _list_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.detect_button.setEnabled(True)
            self.status.setText(self._tr('winget не запустился.', 'winget failed to start.'))

    def select_basics(self):
        essentials = {'Google.Chrome', 'Mozilla.Firefox', 'Discord.Discord',
                      'Telegram.TelegramDesktop', '7zip.7zip', 'VideoLAN.VLC'}
        for app, checkbox, _ in self.rows:
            checkbox.setChecked(app.package_id in essentials)
        self._update_selection()

    def _update_selection(self, _checked=False) -> None:
        count = sum(check.isChecked() for _, check, _ in self.rows)
        self.selection_label.setText(self._tr(f'Выбрано: {count}', f'Selected: {count}'))

    def _filter(self, phrase: str) -> None:
        phrase = phrase.casefold().strip()
        selected_category = self.category_filter.currentData() or ''
        visible_categories = set()
        for app, _, row in self.rows:
            matches = (not selected_category or app.category == selected_category) and phrase in (f'{app.name} {app.category} {CATEGORY_EN.get(app.category, "")} {app.package_id}').casefold()
            row.setVisible(matches)
            if matches:
                visible_categories.add(app.category)
        for category, label in self.category_headers.items():
            label.setVisible(category in visible_categories)

    def is_installing(self) -> bool:
        """Be defensive about C++ teardown; callers should also check page validity."""
        try:
            return bool(isValid(self.process) and self.process.state() != QProcess.ProcessState.NotRunning)
        except RuntimeError:
            return False

    def install_selected(self) -> None:
        self._begin_queue('install')

    def upgrade_selected(self) -> None:
        self._begin_queue('upgrade')

    def _begin_queue(self, operation: str):
        if self.is_installing() or self.is_checking():
            return
        if sys.platform != 'win32':
            QMessageBox.warning(self, 'FIELD', self._tr('winget доступен только в Windows.', 'winget works on Windows only.'))
            return
        if not shutil.which('winget'):
            QMessageBox.warning(self, 'FIELD', self._tr(
                'winget не найден. Установи Microsoft App Installer и перезапусти FIELD.',
                'winget not found. Install Microsoft App Installer and restart FIELD.',
            ))
            return
        selected = [app for app, checkbox, _ in self.rows if checkbox.isChecked()]
        if operation == 'upgrade':
            if self.installed_ids is None:
                QMessageBox.information(self, 'FIELD', self._tr(
                    'Сначала нажми «Проверить установленные».', 'Use Detect installed first.'))
                return
            selected = [app for app in selected if app.package_id.casefold() in self.installed_ids]
        if not selected:
            QMessageBox.information(self, 'FIELD', self._tr('Сначала выбери приложения.', 'Select at least one app.'))
            return
        message = self._tr(
            ('FIELD обновит' if operation == 'upgrade' else 'FIELD установит') + ' через winget:\n\n' + '\n'.join(a.name for a in selected) +
            '\n\nWindows может запросить права администратора. Продолжить?',
            ('FIELD will upgrade' if operation == 'upgrade' else 'FIELD will install') + ' through winget:\n\n' + '\n'.join(a.name for a in selected) +
            '\n\nWindows may ask for administrator approval. Continue?',
        )
        choice = QMessageBox.question(self, 'FIELD', message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if choice != QMessageBox.StandardButton.Yes:
            return
        self.pending = list(selected)
        self.operation = operation
        self._cancel_requested = False
        self._total_count = len(selected)
        self._done_count = 0
        self.install_button.setEnabled(False)
        self.upgrade_button.setEnabled(False)
        self.detect_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress.setRange(0, len(selected))
        self.progress.setValue(0)
        self.log.clear()
        self._install_next()

    def _install_next(self) -> None:
        if self._cancel_requested or not self.pending:
            self.current = None
            self.install_button.setEnabled(True)
            self.upgrade_button.setEnabled(True)
            self.detect_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.status.setText(self._tr(
                'Очередь остановлена' if self._cancel_requested else 'Операция завершена. Проверь журнал.',
                'Queue stopped' if self._cancel_requested else 'Queue complete. Check the log.',
            ))
            return
        self.current = self.pending.pop(0)
        index = self._done_count + 1
        self.status.setText(self._tr(
            f'Обработка {index}/{self._total_count}: {self.current.name}',
            f'Processing {index}/{self._total_count}: {self.current.name}',
        ))
        self.log.appendPlainText(f'\n▶ {self.current.name} [{self.current.package_id}]')
        self.process.start('winget', [
            self.operation, '--id', self.current.package_id, '--exact', '--source', 'winget',
            '--accept-package-agreements', '--accept-source-agreements',
            '--disable-interactivity',
        ])

    def _read_output(self) -> None:
        if not isValid(self.process):
            return
        output = bytes(self.process.readAllStandardOutput())
        if output:
            decoded = output.decode('utf-8', errors='replace').strip()
            if decoded:
                self.log.appendPlainText(decoded)

    def _finished(self, code: int, status) -> None:
        self._read_output()
        if self.current:
            self.log.appendPlainText(f'{"✓" if code == 0 else "✗"} {self.current.name}: exit code {code}')
            self._done_count += 1
            self.progress.setValue(self._done_count)
        self._install_next()

    def _error(self, error) -> None:
        if not isValid(self.process):
            return
        self.log.appendPlainText(self._tr('Ошибка winget: ', 'winget error: ') + self.process.errorString())
        if error == QProcess.ProcessError.FailedToStart:
            self._cancel_requested = True
            self.pending.clear()
            self.current = None
            self.install_button.setEnabled(True)
            self.upgrade_button.setEnabled(True)
            self.detect_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.status.setText(self._tr('Не удалось запустить winget', 'Failed to start winget'))

    def cancel(self) -> None:
        if not self.is_installing():
            self._cancel_requested = True
            self.pending.clear()
            self._install_next()
            return
        answer = QMessageBox.question(self, 'FIELD', self._tr(
            'Остановить текущую установку и отменить очередь? Это может оставить программу частично установленной.',
            'Stop the running installation and cancel the queue? The app may be partly installed.',
        ), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._cancel_requested = True
        self.pending.clear()
        self.process.terminate()
        self.status.setText(self._tr('Остановка текущей установки…', 'Stopping current installation…'))
