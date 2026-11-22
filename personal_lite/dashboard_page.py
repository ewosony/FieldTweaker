"""FIELD dashboard: live read-only system health and quick actions."""
from __future__ import annotations

import os
import platform
from pathlib import Path

import psutil
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QPushButton


def nice_bytes(value, lang='ru'):
    return f'{value / 1024**3:.1f} ' + ('GB' if lang == 'en' else 'ГБ')


class DashboardPage(QWidget):
    def __init__(self, parent=None, lang='ru', navigate=None, winter=False):
        super().__init__(parent)
        self.lang = lang
        self.winter_enabled = bool(winter)
        self.navigate_to = navigate
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(20)
        hero = QFrame()
        hero.setObjectName('hero')
        h = QVBoxLayout(hero)
        h.setContentsMargins(25, 23, 25, 23)
        self.eyebrow = QLabel('FIELD  /  SYSTEM CONTROL')
        self.eyebrow.setObjectName('eyebrow')
        h.addWidget(self.eyebrow)
        self.holiday_banner=QLabel('❄   W I N T E R   E D I T I O N   ✦')
        self.holiday_banner.setStyleSheet('font-size:13px;font-weight:800;color:#ebcf84;padding:8px 0px;')
        h.addWidget(self.holiday_banner)
        self.heading = QLabel()
        self.heading.setStyleSheet('font-size:29px;font-weight:800;')
        h.addWidget(self.heading)
        self.sub = QLabel()
        self.sub.setObjectName('muted')
        h.addWidget(self.sub)
        root.addWidget(hero)
        self.cards = {}
        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        for i, key in enumerate(('cpu', 'ram', 'disk', 'windows')):
            frame = QFrame()
            frame.setObjectName('card')
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(20, 17, 20, 17)
            title = QLabel()
            title.setObjectName('muted')
            value = QLabel('—')
            value.setStyleSheet('font-size:26px;font-weight:750;')
            frame_layout.addWidget(title)
            frame_layout.addWidget(value)
            self.cards[key] = (title, value)
            self.grid.addWidget(frame, i // 2, i % 2)
        root.addLayout(self.grid)
        self.actions_title = QLabel()
        self.actions_title.setStyleSheet('font-size:19px;font-weight:750;')
        root.addWidget(self.actions_title)
        actions = QHBoxLayout()
        self.action_buttons = []
        for ru, en, target in (
            ('Очистка системы', 'System cleanup', 'Очистка системы'),
            ('Установка ПО', 'App installer', 'Установка ПО'),
            ('Электропитание', 'Power plans', 'Электропитание'),
            ('Твики', 'Tweaks', 'Твики'),
        ):
            btn = QPushButton()
            btn.setMinimumHeight(46)
            btn.clicked.connect(lambda _checked=False, x=target: self.navigate_to(x))
            self.action_buttons.append((btn, ru, en))
            actions.addWidget(btn)
        root.addLayout(actions)
        self.status = QLabel()
        self.status.setObjectName('muted')
        root.addWidget(self.status)
        root.addStretch()
        self.timer = QTimer(self)
        self.timer.setInterval(3500)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.set_language(lang)
        self.set_winter_enabled(winter)
        self.refresh()

    def set_language(self, language):
        self.lang = language
        en = language == 'en'
        self.heading.setText(
            ('Winter-ready control center' if en else 'Зимний FIELD — всё под контролем')
            if self.winter_enabled else
            ('Your PC at a glance' if en else 'Твой компьютер под контролем')
        )
        self.sub.setText(
            ('System overview, winter mood and quick actions.' if en else 'Состояние системы, зимняя атмосфера и быстрые действия.')
            if self.winter_enabled else
            ('System metrics and quick access to FIELD tools.' if en else 'Состояние системы и быстрый доступ к инструментам FIELD.')
        )
        self.actions_title.setText('Quick actions' if en else 'Быстрые действия')
        for key, name in [('cpu', 'Processor' if en else 'Процессор'),
                          ('ram', 'Memory' if en else 'Оперативная память'),
                          ('disk', 'Free disk space' if en else 'Свободно на диске'),
                          ('windows', 'Operating system' if en else 'Операционная система')]:
            self.cards[key][0].setText(name)
        for button, ru, english in self.action_buttons:
            button.setText(english if en else ru)
        self.refresh()

    def set_winter_enabled(self, enabled):
        self.winter_enabled = bool(enabled)
        self.holiday_banner.setVisible(self.winter_enabled)
        self.eyebrow.setText('FIELD  /  WINTER CONTROL' if self.winter_enabled else 'FIELD  /  SYSTEM CONTROL')
        self.set_language(self.lang)

    def refresh(self):
        try:
            usage = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            drive = os.environ.get('SystemDrive', 'C:') + '\\' if os.name == 'nt' else '/'
            space = psutil.disk_usage(drive)
            self.cards['cpu'][1].setText(f'{usage:.0f}%')
            self.cards['ram'][1].setText(f'{nice_bytes(memory.used, self.lang)} / {nice_bytes(memory.total, self.lang)}')
            self.cards['disk'][1].setText(nice_bytes(space.free, self.lang))
            if os.name == 'nt':
                import sys
                win_major = '11' if sys.getwindowsversion().build >= 22000 else '10'
                os_name = 'Windows ' + win_major
            else:
                os_name = platform.system()
            self.cards['windows'][1].setText(os_name)
            self.status.setText('Live data' if self.lang == 'en' else 'Показатели обновляются автоматически')
        except Exception:
            self.status.setText('Metrics unavailable' if self.lang == 'en' else 'Не удалось получить показатели')
