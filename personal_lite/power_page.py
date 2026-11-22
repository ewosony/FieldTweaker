"""Power plan selection page. Doesn't create unsupported schemes or change timers."""
from __future__ import annotations

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QFrame
from . import power_core


class PowerPage(QWidget):
    def __init__(self, parent=None, lang='ru'):
        super().__init__(parent)
        self.lang = lang
        self._busy = False
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)
        self.heading = QLabel()
        self.heading.setStyleSheet('font-size:27px;font-weight:750;')
        root.addWidget(self.heading)
        self.subtitle = QLabel()
        self.subtitle.setObjectName('muted')
        self.subtitle.setWordWrap(True)
        root.addWidget(self.subtitle)
        self.cards_host = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        root.addWidget(self.cards_host)
        buttons = QHBoxLayout()
        self.reload = QPushButton()
        self.reload.clicked.connect(self.refresh)
        self.revert = QPushButton()
        self.revert.clicked.connect(self.restore)
        buttons.addWidget(self.reload)
        buttons.addWidget(self.revert)
        buttons.addStretch()
        root.addLayout(buttons)
        self.status = QLabel()
        self.status.setObjectName('muted')
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        root.addStretch()
        self.set_language(lang)
        self.refresh()

    def _tr(self, ru, en):
        return en if self.lang == 'en' else ru

    def is_busy(self):
        return self._busy

    def set_language(self, language):
        self.lang = language
        self.heading.setText(self._tr('Профили электропитания', 'Power plans'))
        self.subtitle.setText(self._tr(
            'Выбери доступный режим питания Windows. FIELD сохранит предыдущий режим для восстановления.',
            'Choose an available Windows power plan. FIELD saves your previous plan for restoration.'))
        self.reload.setText(self._tr('Обновить список', 'Refresh plans'))
        self.revert.setText(self._tr('Вернуть прежний режим', 'Restore previous plan'))

    def _clear(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh(self):
        self._clear()
        if os.name != 'nt':
            self.status.setText('Windows only')
            self.revert.setEnabled(False)
            return
        try:
            plans = power_core.list_plans()
            current = power_core.active_guid()
            for plan in plans:
                frame = QFrame()
                frame.setObjectName('row')
                row = QHBoxLayout(frame)
                row.setContentsMargins(18, 15, 18, 15)
                names = power_core.KNOWN.get(plan['guid'])
                display_name = (names[1] if self.lang == 'en' else names[0]) if names else plan['name']
                name = QLabel(display_name + (self._tr('  ·  Активен', '  ·  Active') if plan['guid'] == current else ''))
                row.addWidget(name, 1)
                action = QPushButton(self._tr('Выбрать', 'Choose'))
                action.setEnabled(plan['guid'] != current)
                action.clicked.connect(lambda _checked=False, guid=plan['guid']: self.apply(guid))
                row.addWidget(action)
                self.cards_layout.addWidget(frame)
            self.revert.setEnabled(power_core.can_restore())
            self.status.setText(self._tr(
                f'Доступно схем: {len(plans)}', f'Available plans: {len(plans)}'))
        except Exception as exc:
            self.status.setText(str(exc))
            self.revert.setEnabled(False)

    def apply(self, guid):
        if QMessageBox.question(self, 'FIELD', self._tr(
            'Применить выбранный профиль электропитания?', 'Switch to the selected power plan?'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            power_core.apply_plan(guid)
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, 'FIELD', str(exc))

    def restore(self):
        if QMessageBox.question(self, 'FIELD', self._tr(
            'Вернуть предыдущую схему электропитания?', 'Restore your previous power plan?'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            power_core.restore_plan()
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, 'FIELD', str(exc))
