"""Integrated read-only cleanup preview and confirmation-based cleanup page."""
from __future__ import annotations

import os
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QCheckBox, QFrame, QMessageBox, QProgressBar)
from . import cleaner_core as engine


class _Worker(QThread):
    result = Signal(object)
    problem = Signal(str)
    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn
    def run(self):
        try:
            self.result.emit(self.fn())
        except Exception as exc:
            self.problem.emit(str(exc))


class CleanerPage(QWidget):
    def __init__(self, parent=None, lang='ru'):
        super().__init__(parent)
        self.lang = lang
        self._busy = False
        self._worker = None
        self.snapshot = None
        self.checks = {}
        self.sizes = {}
        self.heading = QLabel()
        self.caption = QLabel()
        self.caption.setObjectName('muted')
        self.caption.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self.heading)
        layout.addWidget(self.caption)
        for key in engine.CATEGORY_NAMES:
            frame = QFrame()
            frame.setObjectName('row')
            horizontal = QHBoxLayout(frame)
            horizontal.setContentsMargins(18, 13, 18, 13)
            check = QCheckBox()
            check.setChecked(key in ('temp', 'thumbnails'))
            count = QLabel('—')
            count.setObjectName('muted')
            horizontal.addWidget(check, 1)
            horizontal.addWidget(count)
            layout.addWidget(frame)
            self.checks[key], self.sizes[key] = check, count
            check.toggled.connect(lambda _checked: self._refresh_labels())
        buttons = QHBoxLayout()
        self.scan_button = QPushButton()
        self.scan_button.clicked.connect(self.scan)
        self.clean_button = QPushButton()
        self.clean_button.setObjectName('primary')
        self.clean_button.clicked.connect(self.cleanup)
        buttons.addWidget(self.scan_button)
        buttons.addWidget(self.clean_button)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.message = QLabel()
        self.message.setObjectName('muted')
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        layout.addStretch()
        self.set_language(lang)
        if os.name == 'nt':
            QTimer.singleShot(0, self.scan)
        else:
            self.message.setText('Windows only')
            self.scan_button.setEnabled(False)
            self.clean_button.setEnabled(False)

    def _tr(self, ru, en):
        return en if self.lang == 'en' else ru

    def is_busy(self):
        return self._busy

    def set_language(self, language):
        self.lang = language
        self.heading.setText(self._tr('Очистка системы', 'System cleanup'))
        self.heading.setStyleSheet('font-size:27px;font-weight:750;')
        self.caption.setText(self._tr(
            'Проверь объём кэша перед удалением. Личные файлы, пароли и история браузеров не затрагиваются.',
            'Review cached files before deleting. Personal files, passwords and browser history are untouched.'))
        for key, check in self.checks.items():
            check.setText(engine.CATEGORY_NAMES[key][int(language == 'en')])
        self.scan_button.setText(self._tr('Сканировать', 'Scan'))
        self.clean_button.setText(self._tr('Очистить выбранное', 'Clean selected'))
        if not self._busy and not self.snapshot:
            self.message.setText(self._tr('Готово к проверке', 'Ready to scan'))
        self._refresh_labels()

    def _refresh_labels(self):
        self.clean_button.setEnabled(not self._busy and self.snapshot is not None and
                                     any(self.checks[k].isChecked() and self.snapshot.count(k) for k in self.checks))
        self.scan_button.setEnabled(not self._busy and os.name == 'nt')
        for key, out in self.sizes.items():
            if self.snapshot is None:
                out.setText('—')
            elif key in self.snapshot.skipped:
                out.setText(self._tr('Пропущено', 'Skipped'))
            else:
                out.setText(engine.human_size(self.snapshot.size(key)))

    def _execute(self, fn, result_handler):
        if self._busy:
            return
        self._busy = True
        self.progress.setRange(0, 0)
        self._refresh_labels()
        worker = _Worker(fn, self)
        self._worker = worker
        worker.result.connect(result_handler)
        worker.problem.connect(lambda msg: self.message.setText(msg))
        worker.finished.connect(self._complete)
        worker.start()

    def _complete(self):
        self._busy = False
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self._refresh_labels()
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    def scan(self):
        if self._busy:
            return
        self.snapshot = None
        self.message.setText(self._tr('Анализ файлов…', 'Scanning files…'))
        self._execute(engine.scan, self._scan_finished)

    def _scan_finished(self, result):
        self.snapshot = result
        total = sum(result.size(k) for k in self.checks)
        self.message.setText(self._tr(
            f'Найдено: {engine.human_size(total)}. Неиспользуемые браузеры должны быть закрыты для очистки их кэша.',
            f'Found: {engine.human_size(total)}. Close browsers before cleaning their caches.'))
        self._refresh_labels()

    def cleanup(self):
        if self._busy or not self.snapshot:
            return
        chosen = [k for k, check in self.checks.items() if check.isChecked()]
        amount = sum(self.snapshot.size(k) for k in chosen)
        if not amount:
            return
        question = self._tr(
            f'Удалить выбранные временные файлы ({engine.human_size(amount)})? Файлы будут удалены без корзины.',
            f'Delete selected cache files ({engine.human_size(amount)})? Files will not go to the Recycle Bin.')
        if QMessageBox.question(self, 'FIELD', question,
             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
             QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        snapshot = self.snapshot
        self.message.setText(self._tr('Очистка…', 'Cleaning…'))
        self._execute(lambda: engine.clean(snapshot, chosen), self._clean_finished)

    def _clean_finished(self, result):
        self.message.setText(self._tr(
            f'Удалено: {result["deleted"]} файлов · освобождено {engine.human_size(result["bytes"])} · пропущено из-за ошибок: {result["errors"]}',
            f'Removed: {result["deleted"]} files · freed {engine.human_size(result["bytes"])} · errors: {result["errors"]}'))
        self.snapshot = None
        self._refresh_labels()
