"""Embedded FIELD page for opt-in advanced Windows settings (RU/EN)."""
from __future__ import annotations

import os

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox,
)

from . import advanced_core as engine


def _tr(lang, ru, en):
    return en if lang == 'en' else ru


class _Task(QThread):
    ok = Signal(str)
    problem = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn

    def run(self):
        try:
            self.ok.emit(str(self.fn()))
        except Exception as exc:
            self.problem.emit(str(exc))


class AdvancedSettingsPage(QWidget):
    """Rendered inside FIELD's central area, not in a popup window."""

    def __init__(self, parent=None, lang='ru'):
        super().__init__(parent)
        self.lang = lang
        self._job = None
        self._busy = False
        self.setObjectName('advancedSettingsPage')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        self._add_text(layout, _tr(lang, 'РАСШИРЕННЫЕ НАСТРОЙКИ', 'ADVANCED SETTINGS'), 12, 'eyebrow')
        self._add_text(layout, _tr(lang, 'Управление Windows и производительностью', 'Windows and performance controls'), 26)
        self._add_text(layout, _tr(lang,
            'Все изменения выполняются только после подтверждения. FIELD сохраняет предыдущие значения для восстановления.',
            'Changes are opt-in and previous settings are saved for restoration.'), 12, 'muted')

        update_card, update_layout = self._card()
        self._add_text(update_layout, _tr(lang, 'Windows Update', 'Windows Update'), 19)
        self._add_text(update_layout, _tr(lang,
            'Отключает автоматические обновления до обратного включения. Windows может восстановить их самостоятельно.',
            'Disables automatic updates until you turn them back on. Windows may restore them automatically.'), 12, 'muted')
        self._add_text(update_layout, _tr(lang,
            'ВНИМАНИЕ: отсутствие обновлений повышает риск уязвимостей и заражений. Не отключайте на компьютерах без регулярного обслуживания.',
            'WARNING: missing security updates increases vulnerability and malware risks. Not recommended on unmanaged PCs.'), 12)
        self.update_status_label = self._add_text(update_layout, '—', 13)
        row = QHBoxLayout()
        self.update_disable = QPushButton(_tr(lang, 'Отключить обновления', 'Disable updates'))
        self.update_restore = QPushButton(_tr(lang, 'Включить обратно / откат', 'Restore previous settings'))
        self.update_disable.clicked.connect(lambda: self._change_updates(True))
        self.update_restore.clicked.connect(lambda: self._change_updates(False))
        row.addWidget(self.update_disable)
        row.addWidget(self.update_restore)
        row.addStretch(1)
        update_layout.addLayout(row)
        layout.addWidget(update_card)

        self._add_text(layout, _tr(lang, 'Дополнительные параметры',
                                  'Additional settings'), 19)
        self.feature_buttons = {}
        for feature_id, spec in engine.FEATURES.items():
            card, content = self._card()
            self._add_text(content, spec['name_en'] if lang == 'en' else spec['name_ru'], 16)
            self._add_text(content, spec['desc_en'] if lang == 'en' else spec['desc_ru'], 12, 'muted')
            status = self._add_text(content, '—', 12)
            controls = QHBoxLayout()
            enable = QPushButton(_tr(lang, 'Применить', 'Apply'))
            restore = QPushButton(_tr(lang, 'Восстановить', 'Restore'))
            enable.clicked.connect(lambda _checked=False, fid=feature_id: self._change_feature(fid, True))
            restore.clicked.connect(lambda _checked=False, fid=feature_id: self._change_feature(fid, False))
            controls.addWidget(enable)
            controls.addWidget(restore)
            controls.addStretch(1)
            content.addLayout(controls)
            layout.addWidget(card)
            self.feature_buttons[feature_id] = (status, enable, restore)

        self.message = self._add_text(layout, _tr(lang,
            'Для системных настроек может потребоваться запуск FIELD от администратора.',
            'Some controls require FIELD to run as administrator.'), 12, 'muted')
        layout.addStretch(1)
        self.refresh()

    def _card(self):
        frame = QFrame(self)
        frame.setObjectName('card')
        content = QVBoxLayout(frame)
        content.setContentsMargins(20, 18, 20, 18)
        content.setSpacing(10)
        return frame, content

    def _add_text(self, layout, text, size, style_name=None):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f'font-size: {size}px;')
        if style_name:
            label.setObjectName(style_name)
        layout.addWidget(label)
        return label

    def is_busy(self):
        return self._busy

    def refresh(self):
        if os.name != 'nt':
            self.update_status_label.setText('Windows only')
            self.update_disable.setEnabled(False)
            self.update_restore.setEnabled(False)
            for label, apply, undo in self.feature_buttons.values():
                label.setText('Windows only')
                apply.setEnabled(False)
                undo.setEnabled(False)
            return
        try:
            state = engine.update_status()
            active = state['blocked']
            saved = state['can_restore']
            self.update_status_label.setText(_tr(self.lang,
                'Статус: ' + ('отключены' if active else 'не полностью отключены') + (' · сохранено состояние FIELD' if saved else ' · копии FIELD нет'),
                'Status: ' + ('disabled' if active else 'not fully disabled') + (' · FIELD backup present' if saved else ' · no FIELD backup')))
            self.update_disable.setEnabled(not self._busy and (not saved or not active))
            self.update_restore.setEnabled(not self._busy and saved)
        except Exception as exc:
            self.update_status_label.setText(str(exc))
            self.update_disable.setEnabled(False)
            self.update_restore.setEnabled(False)
        for fid, (label, apply, undo) in self.feature_buttons.items():
            try:
                state = engine.feature_status(fid)
                label.setText(_tr(self.lang,
                    'Применено' if state['applied'] else 'Не применено',
                    'Applied' if state['applied'] else 'Not applied'))
                apply.setEnabled(not self._busy and not state['can_restore'])
                undo.setEnabled(not self._busy and state['can_restore'])
            except Exception as exc:
                label.setText(str(exc))
                apply.setEnabled(False)
                undo.setEnabled(False)

    def _confirm(self, title, description):
        reply = QMessageBox.warning(self, title, description,
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def _change_updates(self, disabled):
        if disabled:
            if not self._confirm('Windows Update', _tr(self.lang,
                'Отключить автоматические обновления Windows? Это повышает риск уязвимостей. Режим не гарантирован против восстановления службой Windows. Продолжить?',
                'Disable automatic Windows updates? This increases security risks and is not guaranteed against Windows service recovery. Continue?')):
                return
        else:
            if not self._confirm('Windows Update', _tr(self.lang,
                'Восстановить прежние параметры Windows Update из резервной копии FIELD?',
                'Restore Windows Update settings from the FIELD backup?')):
                return
        self._run(lambda: engine.set_windows_updates_disabled(disabled))

    def _change_feature(self, fid, enable):
        name = engine.FEATURES[fid]['name_en' if self.lang == 'en' else 'name_ru']
        action = _tr(self.lang, 'Применить' if enable else 'Отменить', 'Apply' if enable else 'Restore')
        if self._confirm('FIELD', f'{action}: {name}?'):
            self._run(lambda: engine.set_feature(fid, enable))

    def _run(self, fn):
        if self._busy:
            return
        self._busy = True
        self.refresh()
        self.message.setText(_tr(self.lang, 'Выполняется операция…', 'Applying changes…'))
        job = _Task(fn, self)
        self._job = job
        job.ok.connect(self._on_success)
        job.problem.connect(self._on_error)
        job.finished.connect(self._on_finished)
        job.start()

    def _on_success(self, message):
        self.message.setText(message)
        self.refresh()

    def _on_error(self, message):
        self.message.setText(message)
        QMessageBox.warning(self, 'FIELD', message)
        self.refresh()

    def _on_finished(self):
        self._busy = False
        self.refresh()
        if self._job:
            self._job.deleteLater()
            self._job = None
