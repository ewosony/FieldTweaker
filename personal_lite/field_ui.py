"""FIELD 1.2.1: bilingual Windows control center with optional winter look.
Core tweak, process and file-lock operations are unchanged from 0.7.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QLocale
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QFrame, QLabel, QVBoxLayout,
    QHBoxLayout, QPushButton, QScrollArea, QLineEdit, QCheckBox, QComboBox,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QTabWidget, QStackedWidget, QButtonGroup)
from . import core, system_tools, i18n
from .advanced_settings import AdvancedSettingsPage
from .dashboard_page import DashboardPage
from .cleaner_page import CleanerPage
from .power_page import PowerPage
from .catalog import TWEAKS, APPS, PRESETS
from .ui import Studio, clear, label, button, QMessageBox as LocalizedMessageBox
from .app_installer import AppInstallerPage
from .winter_effects import WinterOverlay
from shiboken6 import isValid
QMessageBox = LocalizedMessageBox

DARK = {
    'bg':'#091325', 'sidebar':'#0c192e', 'surface':'#111f36', 'raised':'#172941',
    'line':'#263c58', 'text':'#eef5ff', 'muted':'#95aac5', 'accent':'#65a8ff',
    'accentStrong':'#3587f6', 'accentText':'#071727', 'hover':'#1c3553',
    'input':'#0d1d33', 'selection':'#274c79', 'chip':'#132d4e'
}
LIGHT = {
    'bg':'#f4f7fc', 'sidebar':'#ffffff', 'surface':'#ffffff', 'raised':'#f1f5fc',
    'line':'#d8e2f0', 'text':'#152640', 'muted':'#62758e', 'accent':'#1969d2',
    'accentStrong':'#145dbc', 'accentText':'#ffffff', 'hover':'#e9f1fc',
    'input':'#ffffff', 'selection':'#daeafd', 'chip':'#edf4fe'
}
STATE_DIR = Path(os.environ.get('APPDATA', str(Path.home()))) / 'FIELD'
STATE_FILE = STATE_DIR / 'appearance.json'
VERSION = '1.2.1'

# A complete winter palette, keeping all existing UI tokens intact.
WINTER_DARK = {
    **DARK,
    'bg': '#081a24', 'sidebar': '#0b242b', 'surface': '#102c33',
    'raised': '#163740', 'line': '#33545a', 'text': '#f0fafb',
    'muted': '#acc6c9', 'accent': '#f1d28a', 'accentStrong': '#168f84',
    'accentText': '#ffffff', 'hover': '#20505a', 'input': '#0c2830',
    'selection': '#245f61', 'chip': '#1a4148',
}
WINTER_LIGHT = {
    **LIGHT,
    'bg': '#f2fafb', 'sidebar': '#f7fffe', 'surface': '#ffffff',
    'raised': '#e5f3f1', 'line': '#cee4e2', 'text': '#153d46',
    'muted': '#577781', 'accent': '#116b63', 'accentStrong': '#168f84',
    'accentText': '#ffffff', 'hover': '#e0f0ec', 'input': '#ffffff',
    'selection': '#d4ebe7', 'chip': '#e2f3ed',
}



def resource_path(*parts):
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
    return base.joinpath(*parts)


def app_style(p, winter=False):
    style = f"""
    QWidget {{font-family:'Segoe UI';font-size:13px;color:{p['text']};}}
    QMainWindow, QWidget#root, QWidget#content, QWidget#page, QScrollArea, QScrollArea > QWidget > QWidget {{background:{p['bg']};}}
    QLabel {{background:transparent;border:none;}}
    QLabel#muted {{color:{p['muted']};}}
    QLabel#pageTitle {{font-size:29px;font-weight:750;color:{p['text']};}}
    QLabel#sectionTitle {{font-size:19px;font-weight:750;color:{p['text']};}}
    QFrame#sidebar, QWidget#navHost, QScrollArea#navScroll {{background:{p['sidebar']};border-right:0;}}
    QFrame#sidebar {{border-right:1px solid {p['line']};}}
    QFrame#topbar {{background:{p['bg']};border-bottom:1px solid {p['line']};}}
    QFrame#card, QFrame#row, QFrame#toolPanel {{background:{p['surface']};border:1px solid {p['line']};border-radius:15px;}}
    QFrame#hero {{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {p['raised']},stop:1 {p['chip']});border:1px solid {p['line']};border-radius:18px;}}
    QFrame#toolbar {{background:{p['surface']};border:1px solid {p['line']};border-radius:13px;}}
    QFrame#statusBar {{background:{p['sidebar']};border-top:1px solid {p['line']};}}
    QLabel#eyebrow {{color:{p['accent']};font-size:11px;font-weight:800;}}
    QLabel#brand {{font-size:21px;font-weight:900;color:{p['text']};}}
    QPushButton {{background:{p['raised']};border:1px solid {p['line']};border-radius:10px;padding:10px 15px;color:{p['text']};font-weight:600;}}
    QPushButton:hover {{background:{p['hover']};border-color:{p['accent']};}}
    QPushButton:disabled {{color:{p['muted']};background:{p['surface']};border-color:{p['line']};}}
    QPushButton#primary {{background:{p['accentStrong']};color:white;border:1px solid {p['accentStrong']};}}
    QPushButton#primary:hover {{background:{p['accent']};border-color:{p['accent']};}}
    QPushButton#nav {{text-align:left;background:transparent;border:0;border-radius:10px;padding:13px 15px;color:{p['muted']};font-weight:650;}}
    QPushButton#nav:hover {{background:{p['hover']};color:{p['text']};}}
    QPushButton#nav[active="true"] {{background:{p['chip']};color:{p['accent']};border-left:3px solid {p['accent']};font-weight:750;}}
    QPushButton#themeToggle {{background:{p['chip']};border:1px solid {p['line']};border-radius:16px;padding:7px 13px;color:{p['accent']};}}
    QFrame#languageSwitch {{background:{p['input']};border:1px solid {p['line']};border-radius:13px;}}
    QPushButton#langOption {{background:transparent;border:0;border-radius:9px;padding:7px 13px;color:{p['muted']};font-weight:750;}}
    QPushButton#langOption:hover {{background:{p['hover']};color:{p['text']};}}
    QPushButton#langOption:checked {{background:{p['accentStrong']};color:white;}}
    QComboBox,QLineEdit {{background:{p['input']};border:1px solid {p['line']};border-radius:9px;padding:10px 12px;color:{p['text']};}}
    QComboBox QAbstractItemView {{background:{p['surface']};color:{p['text']};selection-background-color:{p['selection']};}}
    QLineEdit:focus,QComboBox:focus {{border-color:{p['accent']};}}
    QCheckBox {{spacing:10px;}}
    QCheckBox::indicator {{width:18px;height:18px;}}
    QCheckBox::indicator:unchecked {{background:{p['input']};border:1px solid {p['muted']};border-radius:5px;}}
    QCheckBox::indicator:checked {{background:{p['accentStrong']};border:1px solid {p['accentStrong']};border-radius:5px;}}
    QTableWidget {{background:{p['surface']};alternate-background-color:{p['raised']};color:{p['text']};gridline-color:{p['line']};border:1px solid {p['line']};border-radius:11px;selection-background-color:{p['selection']};selection-color:{p['text']};}}
    QHeaderView::section {{background:{p['raised']};padding:12px;color:{p['muted']};border:0;border-bottom:1px solid {p['line']};font-weight:650;}}
    QScrollArea {{border:0;}}
    QScrollBar:vertical {{background:transparent;width:9px;}}
    QScrollBar::handle:vertical {{background:{p['line']};border-radius:4px;min-height:25px;}}
    QTabWidget::pane {{background:{p['surface']};border:1px solid {p['line']};border-radius:12px;}}
    QTabBar::tab {{background:{p['raised']};color:{p['muted']};padding:12px 16px;border-radius:9px;margin-right:5px;}}
    QTabBar::tab:selected {{background:{p['chip']};color:{p['accent']};font-weight:750;}}
    QToolTip {{background:{p['raised']};color:{p['text']};border:1px solid {p['line']};}}
    QPushButton#winterToggle {{background:{p['raised']};border:1px solid {p['line']};border-radius:16px;padding:7px 12px;color:{p['muted']};}}
    QPushButton#winterToggle[winter="true"] {{background:{p['chip']};color:{p['accent']};border:1px solid {p['accent']};font-weight:750;}}
    QLabel#winterBadge {{color:{p['accent']};background:{p['chip']};border:1px solid {p['line']};border-radius:10px;padding:8px 12px;font-size:10px;font-weight:800;}}
    QPlainTextEdit {{background:{p['input']};color:{p['text']};border:1px solid {p['line']};border-radius:10px;padding:10px;}}
    """
    if winter:
        style += f"""
        QFrame#topbar {{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {p['sidebar']},stop:0.7 {p['bg']},stop:1 {p['chip']});border-bottom:1px solid {p['line']};}}
        QFrame#hero {{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {p['surface']},stop:0.55 {p['raised']},stop:1 {p['chip']});border:1px solid {p['line']};border-radius:18px;}}
        QPushButton#primary {{background:{p['accentStrong']};border:1px solid {p['accentStrong']};color:#ffffff;}}
        QPushButton#primary:hover {{background:{p['selection']};border-color:{p['accentStrong']};}}
        """
    return style


def block(text, size=13, color=None, weight=400):
    x = QLabel(i18n.translate(str(text)))
    x.setWordWrap(True)
    x.setStyleSheet(f'font-size:{size}px;font-weight:{weight};')
    if color == 'muted':
        x.setObjectName('muted')
    elif color == 'accent':
        x.setObjectName('eyebrow')
    return x


class FieldStudio(Studio):
    NAV = [('Главная','▦'),('Сведения о системе','◎'),('Твики','◈'),('Приложения','▤'),
           ('Установка ПО','↓'),('Очистка системы','⌁'),('Электропитание','⚡'),
           ('Расширенные настройки','⚙'),('Автозагрузка','◴'),('Инструменты','⌕'),
           ('Профили','◇'),('История','≡')]

    def __init__(self):
        try:
            saved=json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except (OSError,ValueError):
            saved={}
        self.theme=saved.get('theme','dark') if saved.get('theme') in ('dark','light') else 'dark'
        # This winter edition opens in festive mode, but users can turn it off.
        self.winter_enabled = saved.get('winter_enabled', True) is not False
        # Match the Windows user interface locale on every launch.
        # Manual RU/EN changes affect this session only.
        self.lang=i18n.detect_system_language()
        i18n.set_language(self.lang)
        super().__init__()
        self.setWindowTitle('FIELD ' + VERSION)
        self.setWindowIcon(QIcon(str(resource_path('assets', 'field.ico'))))
        self.resize(1370,850)
        self.setMinimumSize(1010,680)
        self.apply_appearance()

    def save_state(self):
        try:
            STATE_DIR.mkdir(parents=True,exist_ok=True)
            STATE_FILE.write_text(json.dumps({'theme':self.theme, 'winter_enabled':self.winter_enabled},indent=2),encoding='utf-8')
        except OSError:
            pass

    def create_shell(self):
        outer=QWidget();outer.setObjectName('root');self.setCentralWidget(outer)
        root=QHBoxLayout(outer);root.setContentsMargins(0,0,0,0);root.setSpacing(0)
        rail=QFrame();rail.setObjectName('sidebar');rail.setFixedWidth(226)
        side=QVBoxLayout(rail);side.setContentsMargins(16,24,16,19);side.setSpacing(7)
        brand=QHBoxLayout();brand.setSpacing(12)
        icon=QLabel();icon.setFixedSize(42,42)
        icon.setPixmap(QPixmap(str(resource_path('assets', 'field_icon.png'))).scaled(42,42,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        brand.addWidget(icon)
        self.brand=block('FIELD',22,weight=850);self.brand.setObjectName('brand');brand.addWidget(self.brand,1)
        side.addLayout(brand)
        side.addSpacing(12)
        self.winter_badge=QLabel('❄  WINTER EDITION  /  1.2.1')
        self.winter_badge.setObjectName('winterBadge')
        self.winter_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side.addWidget(self.winter_badge)
        side.addSpacing(14)
        self.nav_caption=block('WORKSPACE',10,'muted',750);side.addWidget(self.nav_caption);side.addSpacing(6)
        self.nav={}
        # Scrollable navigation: all 12 sections fit even on 720p screens.
        nav_scroll=QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.NoFrame)
        nav_scroll.setObjectName('navScroll')
        nav_host=QWidget()
        nav_host.setObjectName('navHost')
        nav_layout=QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(0, 0, 3, 0)
        nav_layout.setSpacing(4)
        for name,ic in self.NAV:
            b=QPushButton(f'{ic}    {i18n.translate(name)}');b.setObjectName('nav')
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(43)
            b.clicked.connect(lambda checked=False,n=name:self.navigate(n))
            nav_layout.addWidget(b);self.nav[name]=b
        nav_layout.addStretch()
        nav_scroll.setWidget(nav_host)
        side.addWidget(nav_scroll,1)
        side.addWidget(block('FIELD   /   '+VERSION,10,'muted',600))
        root.addWidget(rail)

        content=QWidget();content.setObjectName('content')
        cv=QVBoxLayout(content);cv.setContentsMargins(0,0,0,0);cv.setSpacing(0)
        top=QFrame();top.setObjectName('topbar');top.setFixedHeight(79)
        row=QHBoxLayout(top);row.setContentsMargins(31,0,31,0);row.setSpacing(13)
        self.header=block('',15,weight=750);row.addWidget(self.header)
        row.addStretch()
        self.theme_button=QPushButton();self.theme_button.setObjectName('themeToggle')
        self.theme_button.setFixedWidth(112);self.theme_button.setAccessibleName('Toggle light and dark theme')
        self.theme_button.clicked.connect(self.toggle_theme);row.addWidget(self.theme_button)
        self.winter_button=QPushButton()
        self.winter_button.setObjectName('winterToggle')
        self.winter_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.winter_button.setFixedWidth(133)
        self.winter_button.setAccessibleName('Toggle festive winter decorations')
        self.winter_button.clicked.connect(self.toggle_winter)
        row.addWidget(self.winter_button)
        # Compact segmented language switch: no native combobox arrow or clipping.
        self.language_switch=QFrame();self.language_switch.setObjectName('languageSwitch')
        self.language_switch.setFixedHeight(39)
        ls=QHBoxLayout(self.language_switch);ls.setContentsMargins(4,4,4,4);ls.setSpacing(3)
        self.language_buttons=QButtonGroup(self);self.language_buttons.setExclusive(True)
        for code in ('ru','en'):
            caption='RU' if code=='ru' else 'EN'
            option=QPushButton(caption);option.setObjectName('langOption')
            option.setCursor(Qt.PointingHandCursor);option.setCheckable(True)
            option.setFixedSize(48,30);option.setChecked(self.lang==code)
            option.setToolTip('Русский' if code=='ru' else 'English')
            option.clicked.connect(lambda checked=False,c=code:self.change_language(c))
            self.language_buttons.addButton(option);ls.addWidget(option)
        row.addWidget(self.language_switch)
        cv.addWidget(top)

        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True)
        self.page=QWidget();self.page.setObjectName('page')
        self.body=QVBoxLayout(self.page);self.body.setContentsMargins(31,30,31,28);self.body.setSpacing(18)
        self.scroll.setWidget(self.page);cv.addWidget(self.scroll,1)
        foot=QFrame();foot.setObjectName('statusBar');foot.setFixedHeight(38)
        fr=QHBoxLayout(foot);fr.setContentsMargins(31,0,31,0)
        self.status=block('Готово · изменения только после подтверждения',11,'muted')
        fr.addWidget(self.status);fr.addStretch()
        cv.addWidget(foot)
        root.addWidget(content,1)
        # Overlay is a click-through child of the shell, not a new window.
        self.winter_overlay = WinterOverlay(outer, active=self.winter_enabled)

    def update_chrome(self):
        self.header.setText('FIELD  /  ' + i18n.translate(self.current).upper())
        self.nav_caption.setText('РАЗДЕЛЫ' if self.lang == 'ru' else 'WORKSPACE')
        for name, icon in self.NAV:
            self.nav[name].setText(f'{icon}    {i18n.translate(name)}')
        self.theme_button.setText(
            ('☀  Светлая' if self.theme == 'dark' else '☾  Тёмная')
            if self.lang == 'ru' else
            ('☀  Light' if self.theme == 'dark' else '☾  Dark')
        )
        self.winter_button.setText(
            ('❄  Зима: вкл' if self.winter_enabled else '❄  Зима: выкл')
            if self.lang == 'ru' else
            ('❄  Winter: on' if self.winter_enabled else '❄  Winter: off')
        )
        self.winter_button.setProperty('winter', 'true' if self.winter_enabled else 'false')
        self.winter_button.style().unpolish(self.winter_button)
        self.winter_button.style().polish(self.winter_button)
        self.winter_badge.setVisible(self.winter_enabled)

    def _live_page(self, attr):
        """Don't invoke a PySide wrapper after Qt deleted its C++ object."""
        page = getattr(self, attr, None)
        if page is None:
            return None
        try:
            if isValid(page):
                return page
        except RuntimeError:
            pass
        setattr(self, attr, None)
        return None

    def _mark_navigation(self, name):
        self.current = name
        for key, item in self.nav.items():
            item.setProperty('active', 'true' if key == name else 'false')
            item.style().unpolish(item)
            item.style().polish(item)

    def navigate(self, name, force=False):
        if name == 'Обзор':
            name = 'Главная'

        installer = self._live_page('_installer_page')
        advanced = self._live_page('_advanced_page')
        cleaner = self._live_page('_cleaner_page')
        if installer and installer.is_installing() and name != 'Установка ПО':
            QMessageBox.information(self, 'FIELD',
                'Сначала заверши или останови установку приложений.' if self.lang == 'ru'
                else 'Finish or stop the app installation before leaving this page.')
            return
        if installer and installer.is_checking() and name != 'Установка ПО':
            QMessageBox.information(self, 'FIELD',
                'Дождись проверки приложений.' if self.lang == 'ru'
                else 'Wait for app detection to finish.')
            return
        if advanced and advanced.is_busy() and name != 'Расширенные настройки':
            QMessageBox.information(self, 'FIELD',
                'Дождись завершения изменения настроек.' if self.lang == 'ru'
                else 'Wait for the current settings operation to finish.')
            return
        if cleaner and cleaner.is_busy() and name != 'Очистка системы':
            QMessageBox.information(self, 'FIELD',
                'Дождись завершения проверки или очистки.' if self.lang == 'ru'
                else 'Wait for the cleanup operation to finish.')
            return

        custom = {
            'Главная': ('_dashboard_page', lambda: DashboardPage(self.page, self.lang, self.navigate, winter=self.winter_enabled)),
            'Установка ПО': ('_installer_page', lambda: AppInstallerPage(self.page, lang=self.lang)),
            'Очистка системы': ('_cleaner_page', lambda: CleanerPage(self.page, lang=self.lang)),
            'Электропитание': ('_power_page', lambda: PowerPage(self.page, lang=self.lang)),
            'Расширенные настройки': ('_advanced_page', lambda: AdvancedSettingsPage(self.page, lang=self.lang)),
        }
        if not force and name == getattr(self, 'current', None) and name in custom:
            self.update_chrome()
            return
        # Clear stale wrapper references before clear() schedules Qt deletion.
        for attr in ('_dashboard_page', '_installer_page', '_cleaner_page', '_power_page', '_advanced_page'):
            setattr(self, attr, None)
        if name in custom:
            self._mark_navigation(name)
            clear(self.body)
            attr, factory = custom[name]
            page = factory()
            setattr(self, attr, page)
            self.body.addWidget(page)
            self.body.addStretch()
            self.scroll.verticalScrollBar().setValue(0)
        elif name == 'Сведения о системе':
            self._mark_navigation(name)
            clear(self.body)
            self.system_details_page()
            self.body.addStretch()
            self.scroll.verticalScrollBar().setValue(0)
        elif name == 'Инструменты':
            self._mark_navigation(name)
            clear(self.body)
            self.tools_page()
            self.body.addStretch()
            self.scroll.verticalScrollBar().setValue(0)
        else:
            super().navigate(name)
        self.update_chrome()
        if name not in custom:
            self.translate_page()

    def system_details_page(self):
        self.body.addWidget(block('Сведения о системе',30,None,800))
        self.body.addWidget(block('Основные характеристики компьютера и Windows.',12,'muted'))
        row=QHBoxLayout()
        row.addWidget(button('Обновить сведения',self.fetch_system_details,True))
        row.addStretch()
        self.body.addLayout(row)
        self.info_host=QWidget()
        self.info_layout=QVBoxLayout(self.info_host)
        self.info_layout.setContentsMargins(0,0,0,0)
        self.info_layout.setSpacing(10)
        self.body.addWidget(self.info_host)
        self.info_layout.addWidget(block('Получение сведений Windows…' if self.lang=='ru' else 'Reading Windows hardware information…',14,'muted'))
        # Query the current machine automatically on every visit, including initial launch.
        QTimer.singleShot(0,self.fetch_system_details)

    def fetch_system_details(self, checked=False):
        """Refresh the System Info page asynchronously on start and on demand."""
        if self.current != 'Сведения о системе':
            return
        self.work('Сведения о системе', core.system_info, self.render_system_details)

    def render_system_details(self,info):
        if self.current!='Сведения о системе':return
        clear(self.info_layout)
        for key in ('Windows','Редакция','Версия','Процессор','Видеокарта','Объём ОЗУ'):
            frame=QFrame();frame.setObjectName('row')
            r=QHBoxLayout(frame);r.setContentsMargins(22,18,22,18);r.setSpacing(20)
            title=block(key,13,'muted',600)
            title.setMinimumWidth(145)
            r.addWidget(title)
            value=block(str(info.get(key,'—')),16,None,750)
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            r.addWidget(value,1)
            self.info_layout.addWidget(frame)
        QTimer.singleShot(0,self.translate_page)

    def tweaks(self):
        # No dashboard. Launch directly into an actionable catalogue.
        band=QFrame();band.setObjectName('toolbar')
        strip=QHBoxLayout(band);strip.setContentsMargins(18,12,18,12)
        strip.addWidget(block('FIELD    /    WINDOWS SETTINGS',11,'accent',750))
        strip.addStretch()
        strip.addWidget(block(f'{len(TWEAKS):02d}  /  '+('НАСТРОЕК' if self.lang=='ru' else 'SETTINGS'),11,'muted',750))
        self.body.addWidget(band)
        super().tweaks()

    def select_all(self,on):
        self.selected={t['id'] for t in TWEAKS if core.tweak_compatibility(t)[0]} if on else set()
        self.rebuild_tweaks()

    def rebuild_tweaks(self):
        super().rebuild_tweaks()
        # Mark unsupported options disabled; compatibility is enforced again by core.
        for i,t in enumerate([t for t in TWEAKS if self.search.text().casefold() in
                (t['title']+' '+t['category']+' '+t['detail']).casefold()]):
            item=self.tweaks_layout.itemAt(i)
            if not item or not item.widget():continue
            checks=item.widget().findChildren(QCheckBox)
            ok, reason=core.tweak_compatibility(t)
            if not ok:
                self.selected.discard(t['id'])
                for check in checks:
                    check.blockSignals(True);check.setChecked(False);check.blockSignals(False)
                    check.setEnabled(False);check.setToolTip(reason)
        if hasattr(self,'selection_info'):
            self.selection_info.setText(('Selected tweaks: ' if self.lang=='en' else 'Выбрано настроек: ')+str(len(self.selected)))

    def apply_selected(self):
        rejected=[t['title'] for t in TWEAKS if t['id'] in self.selected and not core.tweak_compatibility(t)[0]]
        if rejected:
            return QMessageBox.warning(self,'Недоступно','Неподдерживаемые настройки: '+', '.join(rejected))
        return super().apply_selected()

    def apply_appearance(self):
        self.palette_tokens=(WINTER_DARK if self.theme=='dark' else WINTER_LIGHT) if self.winter_enabled else (DARK if self.theme=='dark' else LIGHT)
        QApplication.instance().setStyleSheet(app_style(self.palette_tokens, self.winter_enabled))
        self.update_chrome()

    def toggle_theme(self):
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        self.save_state()
        # Style changes do not require rebuilding the current page: important
        # when a QProcess or QThread is in flight.
        self.apply_appearance()

    def toggle_winter(self):
        # Do not rebuild the page, avoiding QProcess/QThread deletion mid-operation.
        self.winter_enabled = not self.winter_enabled
        self.save_state()
        self.winter_overlay.set_winter(self.winter_enabled)
        self.apply_appearance()
        dashboard = self._live_page('_dashboard_page')
        if dashboard is not None:
            dashboard.set_winter_enabled(self.winter_enabled)

    def change_language(self, lang):
        if lang not in ('ru', 'en') or lang == self.lang:
            return
        advanced = self._live_page('_advanced_page')
        if advanced and advanced.is_busy():
            QMessageBox.information(self, 'FIELD',
                'Дождись завершения изменения настроек.' if self.lang == 'ru'
                else 'Wait for the current settings operation to finish.')
            return
        self.lang = lang
        i18n.set_language(lang)
        self.save_state()
        for option in self.language_buttons.buttons():
            option.setChecked(option.text() == lang.upper())
        for attr, section in (
            ('_installer_page', 'Установка ПО'),
            ('_dashboard_page', 'Главная'),
            ('_cleaner_page', 'Очистка системы'),
            ('_power_page', 'Электропитание'),
        ):
            page = self._live_page(attr)
            if page is not None and self.current == section:
                page.set_language(lang)
                self.update_chrome()
                return
        self.navigate(self.current, force=True)

    def closeEvent(self, event):
        installer = self._live_page('_installer_page')
        if installer and (installer.is_installing() or installer.is_checking()):
            QMessageBox.information(self, 'FIELD',
                'Останови или заверши установку и проверку перед выходом.' if self.lang == 'ru'
                else 'Finish installing or checking apps before quitting.')
            event.ignore()
            return
        for attr in ('_advanced_page', '_cleaner_page'):
            page = self._live_page(attr)
            if page and page.is_busy():
                QMessageBox.information(self, 'FIELD',
                    'Дождись завершения операции перед выходом.' if self.lang == 'ru'
                    else 'Wait for the operation to finish before quitting.')
                event.ignore()
                return
        super().closeEvent(event)

    def translate_page(self):
        if self.lang!='en':
            return
        # Existing shared modules construct localized Qt labels, placeholders and table headers.
        # Preserve original strings so refreshes and theme switches remain reversible.
        for widget in self.page.findChildren(QLabel):
            source=widget.property('_field_source')
            if source is None:
                source=widget.text();widget.setProperty('_field_source',source)
            widget.setText(i18n.translate(source))
        for widget in self.page.findChildren(QPushButton):
            source=widget.property('_field_source')
            if source is None:
                source=widget.text();widget.setProperty('_field_source',source)
            widget.setText(i18n.translate(source))
        for widget in self.page.findChildren(QLineEdit):
            source=widget.property('_field_placeholder')
            if source is None:
                source=widget.placeholderText();widget.setProperty('_field_placeholder',source)
            widget.setPlaceholderText(i18n.translate(source))
        for widget in self.page.findChildren(QTabWidget):
            for n in range(widget.count()):
                widget.setTabText(n,i18n.translate(widget.tabText(n)))
        for widget in self.page.findChildren(QTableWidget):
            for n in range(widget.columnCount()):
                item=widget.horizontalHeaderItem(n)
                if item:
                    source=item.data(Qt.UserRole+40)
                    if source is None:
                        source=item.text();item.setData(Qt.UserRole+40,source)
                    item.setText(i18n.translate(source))

    def completed(self,ident,payload):
        super().completed(ident,payload)
        QTimer.singleShot(0,self.translate_page)

    def render_filtered_processes(self):
        super().render_filtered_processes()
        QTimer.singleShot(0,self.translate_page)

    def render_locks(self, rows):
        super().render_locks(rows)
        QTimer.singleShot(0,self.translate_page)

    def tools_page(self):
        self.body.addWidget(block('ИНСТРУМЕНТЫ',11,"accent",800))
        self.body.addWidget(block('Загляни внутрь системы.',30,None,800))
        self.body.addWidget(block('Файловые блокировки и процессы — без скрытых действий.',12,"muted"))
        tabs=QTabWidget()
        
        tabs.addTab(self.file_tools_tab(),'Файлы / Lock Inspector')
        tabs.addTab(self.process_tools_tab(),'Процессы / Process Monitor')
        self.body.addWidget(tabs)

    def file_tools_tab(self):
        host=QWidget(); layout=QVBoxLayout(host);layout.setContentsMargins(20,23,20,23);layout.setSpacing(15)
        layout.addWidget(block('ПОИСК БЛОКИРОВОК ФАЙЛА',12,"accent",800))
        layout.addWidget(block('Показывает приложения, которые используют файл. Не разблокирует принудительно и не удаляет.',12,"muted"))
        h=QHBoxLayout();self.lock_path=QLineEdit();self.lock_path.setPlaceholderText('Путь к существующему файлу…')
        h.addWidget(self.lock_path,1);h.addWidget(button('Обзор…',self.choose_lock_file));h.addWidget(button('Найти блокировки',self.check_locks,True));layout.addLayout(h)
        self.lock_results=QTableWidget(0,3)
        self.lock_results.setHorizontalHeaderLabels(['Программа','PID','Перезапускаемая'])
        self.lock_results.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        self.lock_results.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeToContents)
        self.lock_results.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeToContents)
        self.lock_results.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lock_results.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lock_results.setMinimumHeight(285);layout.addWidget(self.lock_results)
        self.lock_note=block('Выбери файл и запусти проверку.',11,"muted");layout.addWidget(self.lock_note)
        return host

    def choose_lock_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Выбери заблокированный файл')
        if path:self.lock_path.setText(path)

    def check_locks(self):
        path=self.lock_path.text().strip()
        if not path:return QMessageBox.information(self,'Файл','Выбери файл.')
        self.lock_note.setText('Проверка…')
        self.work('Поиск блокировки файла',lambda:system_tools.find_file_lockers(path),self.render_locks)

    def render_locks(self, rows):
        if self.current!='Инструменты':return
        self.lock_results.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate((row['name'],str(row['pid']),'Да' if row['restartable'] else 'Нет')):
                self.lock_results.setItem(i,j,QTableWidgetItem(value))
        self.lock_note.setText(i18n.translate(f'Обнаружено процессов: {len(rows)}. Пустой список не гарантирует отсутствия всех видов блокировок.'))

    def process_tools_tab(self):
        host=QWidget();layout=QVBoxLayout(host);layout.setContentsMargins(20,23,20,23);layout.setSpacing(13)
        layout.addWidget(block('МОНИТОР ПРОЦЕССОВ',12,"accent",800))
        layout.addWidget(block('Просмотр процессов. Завершение только своего приложения с подтверждением; может привести к потере несохранённых данных.',12,"muted"))
        bar=QHBoxLayout();self.proc_search=QLineEdit();self.proc_search.setPlaceholderText('Поиск по имени, PID или владельцу…')
        self.proc_search.textChanged.connect(self.render_filtered_processes);bar.addWidget(self.proc_search,1)
        bar.addWidget(button('Обновить',self.refresh_processes));bar.addWidget(button('Сведения',self.show_process_info));bar.addWidget(button('Завершить процесс',self.terminate_process))
        layout.addLayout(bar)
        self.proc_table=QTableWidget(0,5)
        self.proc_table.setHorizontalHeaderLabels(['Имя','PID','RAM, МБ','Владелец','Статус'])
        self.proc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.proc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.proc_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.proc_table.setSortingEnabled(True)
        self.proc_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        for j in range(1,5):self.proc_table.horizontalHeader().setSectionResizeMode(j,QHeaderView.ResizeToContents)
        self.proc_table.setMinimumHeight(380);layout.addWidget(self.proc_table)
        self.proc_rows=[]
        self.proc_note=block('Нажми «Обновить», чтобы прочитать процессы.',11,"muted");layout.addWidget(self.proc_note)
        return host

    def refresh_processes(self):
        self.proc_note.setText('Загрузка списка…')
        self.work('Сканирование процессов',system_tools.list_processes,self.handle_processes)

    def handle_processes(self,rows):
        if self.current!='Инструменты':return
        self.proc_rows=rows
        self.render_filtered_processes()

    def render_filtered_processes(self):
        if not hasattr(self,'proc_table'):return
        query=self.proc_search.text().casefold()
        rows=[p for p in getattr(self,'proc_rows',[]) if query in (p['name']+' '+str(p['pid'])+' '+p['user']).casefold()]
        self.proc_table.setSortingEnabled(False)
        self.proc_table.setRowCount(len(rows))
        for i,p in enumerate(rows):
            for j,val in enumerate((p['name'],p['pid'],p['memory_mb'],p['user'],p['status'])):
                cell=QTableWidgetItem(str(val));cell.setData(Qt.UserRole,p['pid'])
                if j in (1,2):cell.setData(Qt.DisplayRole,val)
                self.proc_table.setItem(i,j,cell)
        self.proc_table.setSortingEnabled(True)
        self.proc_note.setText(i18n.translate(f'Показано {len(rows)} из {len(getattr(self,"proc_rows",[]))} процессов.'))

    def chosen_process(self):
        row=self.proc_table.currentRow()
        cell=self.proc_table.item(row,0) if row>=0 else None
        if cell is None:return None
        pid=cell.data(Qt.UserRole)
        return next((p for p in self.proc_rows if p['pid']==pid),None)

    def show_process_info(self):
        p=self.chosen_process()
        if p is None:return QMessageBox.information(self,'Процессы','Выбери процесс в таблице.')
        details=[('Имя',p['name']),('PID',p['pid']),('Владелец',p['user']),('Память, МБ',p['memory_mb']),('Состояние',p['status']),('Файл',p['exe'] or 'Недоступен')]
        QMessageBox.information(self,'Информация о процессе','\n'.join(f'{key}: {val}' for key,val in details))

    def terminate_process(self):
        p=self.chosen_process()
        if p is None:return QMessageBox.information(self,'Процессы','Выбери процесс.')
        ok,reason=system_tools.is_safe_target(p['pid'])
        if not ok:return QMessageBox.warning(self,'Недоступно','Завершение запрещено: '+reason)
        if QMessageBox.warning(self,'Подтвердить завершение',f'Принудительно завершить «{p["name"]}» (PID {p["pid"]})?\n\nНесохранённые данные приложения могут быть потеряны.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        self.work('Завершение процесса',lambda:system_tools.close_user_process(p['pid']),self.process_terminated)

    def process_terminated(self,result):
        QMessageBox.information(self,'Результат',result)
        self.refresh_processes()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setWindowIcon(QIcon(str(resource_path('assets', 'field.ico'))))
    win = FieldStudio()
    win.show()
    return app.exec()
