"""FIELD: embedded application installation page powered by winget."""
from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea,
    QVBoxLayout, QWidget, QFrame,
)


@dataclass(frozen=True)
class AppEntry:
    name: str
    package_id: str
    category: str


APPS = (
    AppEntry("Google Chrome", "Google.Chrome", "Браузеры"),
    AppEntry("Mozilla Firefox", "Mozilla.Firefox", "Браузеры"),
    AppEntry("Brave", "Brave.Brave", "Браузеры"),
    AppEntry("Discord", "Discord.Discord", "Общение"),
    AppEntry("Telegram", "Telegram.TelegramDesktop", "Общение"),
    AppEntry("Steam", "Valve.Steam", "Игры"),
    AppEntry("Epic Games Launcher", "EpicGames.EpicGamesLauncher", "Игры"),
    AppEntry("OBS Studio", "OBSProject.OBSStudio", "Медиа"),
    AppEntry("VLC", "VideoLAN.VLC", "Медиа"),
    AppEntry("7-Zip", "7zip.7zip", "Утилиты"),
    AppEntry("Notepad++", "Notepad++.Notepad++", "Утилиты"),
    AppEntry("PowerToys", "Microsoft.PowerToys", "Утилиты"),
    AppEntry("Visual Studio Code", "Microsoft.VisualStudioCode", "Разработка"),
    AppEntry("Git", "Git.Git", "Разработка"),
    AppEntry("Happ", "Happ.Happ", "Сеть"),
    AppEntry("Throne", "Throneproj.Throne", "Сеть"),
)


# Offline-friendly app badges. To replace a badge with an official logo,
# place a PNG or SVG in assets/app_icons/<package_id>.png (or .svg).
# Example: assets/app_icons/Valve.Steam.png
ICON_BADGES = {
    "Google.Chrome": ("G", "#E94335"),
    "Mozilla.Firefox": ("F", "#F26B21"),
    "Brave.Brave": ("B", "#F04F2D"),
    "Discord.Discord": ("D", "#5865F2"),
    "Telegram.TelegramDesktop": ("T", "#229ED9"),
    "Valve.Steam": ("S", "#1B587C"),
    "EpicGames.EpicGamesLauncher": ("E", "#333842"),
    "OBSProject.OBSStudio": ("O", "#635B84"),
    "VideoLAN.VLC": ("V", "#E58B22"),
    "7zip.7zip": ("7z", "#4A9769"),
    "Notepad++.Notepad++": ("N+", "#4C9E40"),
    "Microsoft.PowerToys": ("P", "#2378C4"),
    "Microsoft.VisualStudioCode": ("VS", "#1687D9"),
    "Git.Git": ("git", "#E94E31"),
    "Happ.Happ": ("H", "#377CDB"),
    "Throneproj.Throne": ("T", "#7D59CA"),
}


def _make_badge(package_id: str, size: int = 36) -> QPixmap:
    """Draw original lettermarks as a built-in fallback (not brand logos)."""
    mark, bg = ICON_BADGES.get(package_id, ("?", "#56718C"))
    scale = 3
    pix = QPixmap(size * scale, size * scale)
    pix.fill(QColor("transparent"))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(bg))
    painter.drawRoundedRect(0, 0, pix.width(), pix.height(), 11 * scale, 11 * scale)
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Segoe UI", max(8, int(17 / max(1, len(mark) / 1.6))) * scale)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, mark)
    painter.end()
    return pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                      Qt.TransformationMode.SmoothTransformation)


def app_icon(package_id: str, size: int = 36) -> QPixmap:
    """Prefer bundled PNG/SVG icons; never fetch images over the network."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        base = Path(__file__).resolve().parent.parent
    for ext in ("png", "svg"):
        file = base / "assets" / "app_icons" / f"{package_id}.{ext}"
        if file.is_file():
            pixmap = QIcon(str(file)).pixmap(size, size)
            if not pixmap.isNull():
                return pixmap
    return _make_badge(package_id, size)


class AppInstallerPage(QWidget):
    """In-window, non-blocking sequential installations with explicit selection."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.pending: list[AppEntry] = []
        self.current: AppEntry | None = None
        self.rows: list[tuple[AppEntry, QCheckBox, QWidget]] = []
        self.category_headers: dict[str, QLabel] = {}
        self._cancel_requested = False

        root = QVBoxLayout(self)
        heading = QLabel("Установка популярных приложений")
        heading.setStyleSheet("font-size: 19px; font-weight: 700;")
        root.addWidget(heading)
        root.addWidget(QLabel("Выбери нужные программы. Установкой управляет Windows Package Manager (winget)."))

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по названию или категории…")
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)

        area = QScrollArea()
        area.setWidgetResizable(True)
        content = QWidget()
        self.apps_layout = QVBoxLayout(content)
        self.apps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for category in dict.fromkeys(a.category for a in APPS):
            label = QLabel(category)
            label.setStyleSheet("font-weight: 700; margin-top: 10px; color: #67B7FF;")
            self.apps_layout.addWidget(label)
            self.category_headers[category] = label
            for app in (a for a in APPS if a.category == category):
                # Keep the icon and checkbox in a single row so filtering
                # hides both, and clicking the name still selects the app.
                item = QWidget()
                line = QHBoxLayout(item)
                line.setContentsMargins(8, 5, 8, 5)
                line.setSpacing(12)
                icon_label = QLabel()
                icon_label.setFixedSize(36, 36)
                icon_label.setPixmap(app_icon(app.package_id))
                icon_label.setToolTip(app.name)
                line.addWidget(icon_label)
                box = QCheckBox(app.name)
                box.setToolTip(app.package_id)
                line.addWidget(box, 1)
                self.apps_layout.addWidget(item)
                self.rows.append((app, box, item))
        area.setWidget(content)
        area.setMinimumHeight(260)
        root.addWidget(area, 1)

        actions = QHBoxLayout()
        self.install_button = QPushButton("Установить выбранные")
        self.install_button.clicked.connect(self.install_selected)
        actions.addWidget(self.install_button)
        self.cancel_button = QPushButton("Остановить")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        actions.addWidget(self.cancel_button)
        root.addLayout(actions)

        self.status = QLabel("Готово к установке")
        root.addWidget(self.status)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(155)
        root.addWidget(self.log)

    def _filter(self, phrase: str) -> None:
        phrase = phrase.casefold().strip()
        visible_categories = set()
        for app, check, row in self.rows:
            matched = phrase in f"{app.name} {app.category} {app.package_id}".casefold()
            row.setVisible(matched)
            if matched:
                visible_categories.add(app.category)
        for category, header in self.category_headers.items():
            header.setVisible(category in visible_categories)

    def install_selected(self) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return
        if sys.platform != "win32":
            QMessageBox.warning(self, "FIELD", "Установка через winget доступна только в Windows.")
            return
        if not shutil.which("winget"):
            QMessageBox.warning(self, "FIELD", "winget не найден. Установите или восстановите App Installer от Microsoft.")
            return
        chosen = [app for app, check, row in self.rows if check.isChecked()]
        if not chosen:
            QMessageBox.information(self, "FIELD", "Сначала выбери хотя бы одно приложение.")
            return
        answer = QMessageBox.question(
            self, "Подтвердить установку",
            "FIELD установит через winget следующие приложения:\n\n"
            + "\n".join(a.name for a in chosen)
            + "\n\nWindows может запросить права администратора.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.pending = chosen
        self._cancel_requested = False
        self.install_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.log.clear()
        self._install_next()

    def _install_next(self) -> None:
        if self._cancel_requested or not self.pending:
            self.current = None
            self.install_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.status.setText("Остановлено" if self._cancel_requested else "Очередь завершена — проверь журнал")
            return
        self.current = self.pending.pop(0)
        self.status.setText(f"Установка: {self.current.name} ({len(self.pending)} в очереди)")
        self.log.appendPlainText(f"\n▶ {self.current.name} — {self.current.package_id}")
        self.process.start("winget", [
            "install", "--id", self.current.package_id, "--exact", "--source", "winget",
            "--accept-package-agreements", "--accept-source-agreements",
            "--disable-interactivity",
        ])

    def _read_output(self) -> None:
        data = bytes(self.process.readAllStandardOutput())
        if data:
            # Output encoding varies by Windows locale and winget version.
            text = data.decode("utf-8", errors="replace")
            self.log.appendPlainText(text.rstrip())

    def _finished(self, code: int, _status) -> None:
        self._read_output()
        if self.current:
            self.log.appendPlainText(f"{'✓' if code == 0 else '✗'} {self.current.name}: код {code}")
        self._install_next()

    def _error(self, error) -> None:
        self.log.appendPlainText(f"Ошибка запуска winget: {self.process.errorString()}")
        # QProcess.finished may not arrive if process failed to start.
        if error == QProcess.ProcessError.FailedToStart:
            self._cancel_requested = True
            self.pending.clear()
            self.current = None
            self.install_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.status.setText("Не удалось запустить winget")

    def cancel(self) -> None:
        self._cancel_requested = True
        self.pending.clear()
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            self.status.setText("Останавливаем текущую установку…")
        else:
            self._install_next()

    def is_installing(self) -> bool:
        return self.process.state() != QProcess.ProcessState.NotRunning
