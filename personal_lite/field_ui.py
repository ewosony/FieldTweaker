"""FIELD 1.0: native-feeling bilingual desktop shell with dark/light appearance.
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
from .catalog import TWEAKS, APPS, PRESETS
from .ui import Studio, clear, label, button, QMessageBox as LocalizedMessageBox
from .app_installer import AppInstallerPage
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


def app_style(p):
    return f"""
    QWidget {{font-family:'Segoe UI';font-size:13px;color:{p['text']};}}
    QMainWindow, QWidget#root, QWidget#content, QWidget#page, QScrollArea, QScrollArea > QWidget > QWidget {{background:{p['bg']};}}
    QLabel {{background:transparent;border:none;}}
    QLabel#muted {{color:{p['muted']};}}
    QLabel#pageTitle {{font-size:29px;font-weight:750;color:{p['text']};}}
    QLabel#sectionTitle {{font-size:19px;font-weight:750;color:{p['text']};}}
    QFrame#sidebar {{background:{p['sidebar']};border-right:1px solid {p['line']};}}
    QFrame#topbar {{background:{p['bg']};border-bottom:1px solid {p['line']};}}
    QFrame#card, QFrame#row, QFrame#toolPanel {{background:{p['surface']};border:1px solid {p['line']};border-radius:15px;}}
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
    """


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
    NAV = [('Сведения о системе','◎'),('Твики','◈'),('Приложения','▤'),('Установка ПО','↓'),('Автозагрузка','◴'),
           ('Инструменты','⌕'),('Профили','◇'),('История','≡')]

    def __init__(self):
        try:
            saved=json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except (OSError,ValueError):
            saved={}
        self.theme=saved.get('theme','dark') if saved.get('theme') in ('dark','light') else 'dark'
        # Match the Windows user interface locale on every launch.
        # Manual RU/EN changes affect this session only.
        self.lang=i18n.detect_system_language()
        i18n.set_language(self.lang)
        super().__init__()
        self.setWindowTitle('FIELD')
        self.setWindowIcon(QIcon(str(Path(__file__).resolve().parent.parent / 'assets' / 'field_icon.png')))
        self.resize(1370,850)
        self.setMinimumSize(1010,680)
        self.apply_appearance()

    def save_state(self):
        try:
            STATE_DIR.mkdir(parents=True,exist_ok=True)
            STATE_FILE.write_text(json.dumps({'theme':self.theme},indent=2),encoding='utf-8')
        except OSError:
            pass

    def create_shell(self):
        outer=QWidget();outer.setObjectName('root');self.setCentralWidget(outer)
        root=QHBoxLayout(outer);root.setContentsMargins(0,0,0,0);root.setSpacing(0)
        rail=QFrame();rail.setObjectName('sidebar');rail.setFixedWidth(226)
        side=QVBoxLayout(rail);side.setContentsMargins(16,24,16,19);side.setSpacing(7)
        brand=QHBoxLayout();brand.setSpacing(12)
        icon=QLabel();icon.setFixedSize(42,42)
        icon.setPixmap(QPixmap(str(Path(__file__).resolve().parent.parent / 'assets' / 'field_icon.png')).scaled(42,42,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        brand.addWidget(icon)
        self.brand=block('FIELD',22,weight=850);self.brand.setObjectName('brand');brand.addWidget(self.brand,1)
        side.addLayout(brand);side.addSpacing(27)
        self.nav_caption=block('WORKSPACE',10,'muted',750);side.addWidget(self.nav_caption);side.addSpacing(6)
        self.nav={}
        for name,ic in self.NAV:
            b=QPushButton(f'{ic}    {i18n.translate(name)}');b.setObjectName('nav')
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(46)
            b.clicked.connect(lambda checked=False,n=name:self.navigate(n))
            side.addWidget(b);self.nav[name]=b
        side.addStretch()
        side.addWidget(block('FIELD   /   1.0',10,'muted',600))
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

    def update_chrome(self):
        page_title = (
            'App Installer'
            if self.current == 'Установка ПО' and self.lang == 'en'
            else i18n.translate(self.current)
    )

        self.header.setText('FIELD  /  ' + page_title.upper())
        self.nav_caption.setText('РАЗДЕЛЫ' if self.lang == 'ru' else 'WORKSPACE')

        for name, ic in self.NAV:
            translated = (
            'App Installer'
            if name == 'Установка ПО' and self.lang == 'en'
            else i18n.translate(name)
        )
            self.nav[name].setText(f'{ic}    {translated}')

        self.theme_button.setText(
        ('☀  Светлая' if self.theme == 'dark' else '☾  Тёмная')
        if self.lang == 'ru'
        else ('☀  Light' if self.theme == 'dark' else '☾  Dark')
    )

    def navigate(self,name):
        existing = getattr(self, '_installer_page', None)
        if name != 'Установка ПО' and existing is not None and existing.is_installing():
            QMessageBox.information(self, 'FIELD', 'Сначала останови или заверши установку приложений.')
            return
        if name=='Обзор':
            name='Сведения о системе'
        if name=='Установка ПО':
            self.current=name
            for key,item in self.nav.items():
                item.setProperty('active','true' if key==name else 'false')
                item.style().unpolish(item);item.style().polish(item)
            clear(self.body)
            self._installer_page = AppInstallerPage(self.page)
            self.body.addWidget(self._installer_page)
            self.scroll.verticalScrollBar().setValue(0)
        elif name=='Сведения о системе':
            self._installer_page = None
            self.current=name
            for key,item in self.nav.items():
                item.setProperty('active','true' if key==name else 'false')
                item.style().unpolish(item);item.style().polish(item)
            clear(self.body)
            self.system_details_page()
            self.body.addStretch()
            self.scroll.verticalScrollBar().setValue(0)
        elif name=='Инструменты':
            self._installer_page = None
            self.current=name
            for key,item in self.nav.items():
                item.setProperty('active','true' if key==name else 'false')
                item.style().unpolish(item);item.style().polish(item)
            clear(self.body)
            self.tools_page()
            self.body.addStretch()
            self.scroll.verticalScrollBar().setValue(0)
        else:
            self._installer_page = None
            super().navigate(name)
        self.update_chrome()
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
        self.palette_tokens=DARK if self.theme=='dark' else LIGHT
        QApplication.instance().setStyleSheet(app_style(self.palette_tokens))
        self.update_chrome()

    def toggle_theme(self):
        self.theme='light' if self.theme=='dark' else 'dark'
        self.save_state()
        self.apply_appearance()
        self.navigate(self.current)

    def change_language(self,lang):
        if lang not in ('ru','en') or lang == self.lang:return
        self.lang=lang
        i18n.set_language(self.lang)
        self.save_state()
        self.navigate(self.current)

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

    from pathlib import Path
    from PySide6.QtGui import QIcon

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    app.setWindowIcon(QIcon(str(base / "assets" / "field.ico")))

    win = FieldStudio()
    win.show()

    sys.exit(app.exec())
