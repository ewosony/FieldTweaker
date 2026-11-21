"""Personal Lite Studio 0.3 — Qt interface. No commands execute until confirmed."""
from __future__ import annotations
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import Qt, Signal, QObject
from .i18n import translate as tr
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QVBoxLayout,
    QHBoxLayout, QGridLayout, QPushButton, QScrollArea, QLineEdit,
    QCheckBox, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QAbstractItemView, QTextEdit,
    QSizePolicy
)
from . import core
from .catalog import TWEAKS, APPS, PRESETS

_QtMessageBox = QMessageBox
class _TranslatedMessageBox:
    Yes = _QtMessageBox.Yes
    No = _QtMessageBox.No
    @staticmethod
    def information(parent, title, content, *args):
        return _QtMessageBox.information(parent, tr(title), tr(content), *args)
    @staticmethod
    def warning(parent, title, content, *args):
        return _QtMessageBox.warning(parent, tr(title), tr(content), *args)
    @staticmethod
    def critical(parent, title, content, *args):
        return _QtMessageBox.critical(parent, tr(title), tr(content), *args)
    @staticmethod
    def question(parent, title, content, *args):
        return _QtMessageBox.question(parent, tr(title), tr(content), *args)
QMessageBox = _TranslatedMessageBox

# Colors match the visual language of the user's «Линия» application.
BG='#161720'; SIDEBAR='#20212e'; SURFACE='#20222f'; SURFACE2='#292b3d'
LINE='#333548'; WHITE='#f4f1ff'; MUTED='#a0a2ba'; GOLD='#8a75ee'; GREEN='#56cfaa'; RED='#e889a4'

STYLE=f'''
QMainWindow {{background:{BG};}}
QWidget {{color:{WHITE};font-family:"Segoe UI";font-size:13px;}}
QWidget#root, QWidget#content, QWidget#page, QScrollArea, QScrollArea > QWidget > QWidget {{background:{BG};}}
QLabel {{background:transparent;border:0;}}
QFrame#sidebar {{background:{SIDEBAR};border-right:1px solid {LINE};}}
QFrame#topbar {{background:#1f2030;border-bottom:1px solid {LINE};}}
QFrame#card, QFrame#row {{background:{SURFACE};border:1px solid {LINE};border-radius:15px;}}
QFrame#hero {{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #302b5a,stop:1 #4c467b);border:0;border-radius:19px;}}
QLabel#muted {{color:{MUTED};}}
QLabel#eyebrow {{color:#b2a3ff;font-weight:700;font-size:11px;letter-spacing:1px;}}
QLabel#pageTitle {{font-size:26px;font-weight:700;}}
QLabel#stat {{font-size:27px;font-weight:750;}}
QPushButton {{background:{SURFACE2};border:1px solid #41435a;border-radius:10px;padding:11px 16px;font-weight:600;}}
QPushButton:hover {{background:#35364e;border-color:#7469ae;}}
QPushButton:disabled {{color:#77798d;background:#232433;}}
QPushButton#primary {{background:#816be2;color:white;border:0;}}
QPushButton#primary:hover {{background:#9b89f6;}}
QPushButton#nav {{text-align:left;background:transparent;border:0;border-radius:11px;padding:14px 17px;color:#a6a9c4;font-weight:500;}}
QPushButton#nav:hover {{background:#2c2d3d;color:{WHITE};}}
QPushButton#nav[active="true"] {{background:#eeeafe;color:#5b49bf;border:0;border-radius:11px;font-weight:700;}}
QLineEdit {{background:#242637;border:1px solid #393b50;border-radius:11px;padding:11px 14px;}}
QLineEdit:focus {{border-color:#9785f0;}}
QCheckBox {{spacing:10px;}}
QCheckBox::indicator {{width:18px;height:18px;}}
QCheckBox::indicator:unchecked {{border:1px solid #787a9c;border-radius:5px;background:#292b3c;}}
QCheckBox::indicator:checked {{background:#8a75ee;border:1px solid #8a75ee;border-radius:5px;}}
QTableWidget {{background:{SURFACE};alternate-background-color:{SURFACE2};border:1px solid {LINE};border-radius:10px;gridline-color:{LINE};selection-background-color:#534983;}}
QHeaderView::section {{background:{SIDEBAR};color:{MUTED};padding:10px;border:0;border-bottom:1px solid {LINE};}}
QScrollArea {{border:0;}}
QScrollBar:vertical {{width:10px;background:transparent;}}
QScrollBar::handle:vertical {{background:#44465c;border-radius:5px;min-height:24px;}}
QTextEdit {{background:{SURFACE};border:1px solid {LINE};border-radius:8px;padding:12px;}}
'''

class Signals(QObject):
    done = Signal(object, object)


def label(text, size=None, muted=False, bold=False):
    x = QLabel(tr(str(text)))
    x.setWordWrap(True)
    if muted:
        x.setObjectName('muted')
    if size or bold:
        x.setStyleSheet(f'font-size:{size or 13}px;' + ('font-weight:700;' if bold else ''))
    return x


def button(text, callback=None, primary=False):
    b = QPushButton(tr(text))
    if primary:
        b.setObjectName('primary')
    if callback:
        b.clicked.connect(callback)
    return b


def card():
    f=QFrame(); f.setObjectName('card'); return f


def clear(layout):
    while layout.count():
        item=layout.takeAt(0)
        if item.widget():item.widget().deleteLater()
        elif item.layout():clear(item.layout())


class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FIELD · 1.0')
        self.resize(1370,870); self.setMinimumSize(1040,660)
        self.selected=set(); self.pool=ThreadPoolExecutor(max_workers=2)
        self.signals=Signals(); self.signals.done.connect(self.completed)
        self.tasks={}; self.next_id=0
        self.app_checks={}; self.start_map={}; self.current='Обзор'
        self.create_shell(); self.navigate('Обзор')

    def create_shell(self):
        outer=QWidget();outer.setObjectName('root');self.setCentralWidget(outer)
        root=QHBoxLayout(outer);root.setContentsMargins(0,0,0,0);root.setSpacing(0)
        aside=QFrame();aside.setObjectName('sidebar');aside.setFixedWidth(261)
        nav=QVBoxLayout(aside);nav.setContentsMargins(20,24,18,18);nav.setSpacing(5)

        brand_row=QHBoxLayout();brand_row.setSpacing(12)
        emblem=label('◈',23,bold=True);emblem.setAlignment(Qt.AlignCenter)
        emblem.setFixedSize(44,44)
        emblem.setStyleSheet('background:#816be2;color:white;border-radius:15px;font-size:25px;font-weight:700;')
        brand_row.addWidget(emblem)
        brand_text=QVBoxLayout();brand_text.setSpacing(2)
        brand_text.addWidget(label('PERSONAL LITE',15,bold=True))
        brand_text.addWidget(label('твоя система • твои правила',10,muted=True))
        brand_row.addLayout(brand_text,1);nav.addLayout(brand_row)
        nav.addSpacing(39)
        nav.addWidget(label('РАБОЧЕЕ ПРОСТРАНСТВО',11,muted=True))
        nav.addSpacing(7)
        self.nav={}
        for name,icon in [('Обзор','▦'),('Твики','✧'),('Приложения','▣'),('Автозагрузка','◷'),('Диагностика','◎'),('История','◴'),('Профили','▤')]:
            b=button(f'{icon}    {name}',lambda _,n=name:self.navigate(n));b.setObjectName('nav');b.setCursor(Qt.PointingHandCursor)
            nav.addWidget(b);self.nav[name]=b
        nav.addStretch()
        bottom=card();lay=QVBoxLayout(bottom);lay.setContentsMargins(16,15,16,15);lay.setSpacing(5)
        lay.addWidget(label('●  ЗАЩИЩЁННЫЙ РЕЖИМ',11,bold=True))
        lay.addWidget(label('Изменения только по твоему подтверждению',11,muted=True))
        nav.addWidget(bottom)
        nav.addSpacing(8)
        nav.addWidget(label('PERSONAL LITE   /   v0.4',10,muted=True))
        root.addWidget(aside)

        content=QWidget();content.setObjectName('content')
        ct=QVBoxLayout(content);ct.setContentsMargins(0,0,0,0);ct.setSpacing(0)
        top=QFrame();top.setObjectName('topbar');top.setFixedHeight(74)
        top_layout=QHBoxLayout(top);top_layout.setContentsMargins(40,0,40,0)
        self.header=label('');self.header.setStyleSheet('color:#b0a2ff;font-size:13px;font-weight:650;')
        top_layout.addWidget(self.header);top_layout.addStretch()
        safe=label('◈  Локальная утилита  •  без фоновых служб',11,muted=True)
        top_layout.addWidget(safe);ct.addWidget(top)
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True)
        ct.addWidget(self.scroll,1)
        self.page=QWidget();self.page.setObjectName('page')
        self.body=QVBoxLayout(self.page);self.body.setContentsMargins(40,34,40,30);self.body.setSpacing(19)
        self.scroll.setWidget(self.page)
        foot=QHBoxLayout();foot.setContentsMargins(40,10,40,13)
        self.status=label('Готово · изменения только после подтверждения',11,muted=True)
        foot.addWidget(self.status);foot.addStretch();foot.addWidget(label('Personal Lite Studio',10,muted=True))
        ct.addLayout(foot)
        root.addWidget(content,1)

    def title(self,text,subtitle):
        t=label(text);t.setObjectName('pageTitle');self.body.addWidget(t)
        self.body.addWidget(label(subtitle,12,muted=True))

    def navigate(self,name):
        self.current=name;self.header.setText('PERSONAL LITE   ›   '+name)
        for k,b in self.nav.items():b.setProperty('active','true' if k==name else 'false');b.style().unpolish(b);b.style().polish(b)
        clear(self.body)
        {'Обзор':self.overview,'Твики':self.tweaks,'Приложения':self.apps,'Автозагрузка':self.startup,'Диагностика':self.diagnostics,'История':self.history,'Профили':self.profiles}[name]()
        self.body.addStretch();self.scroll.verticalScrollBar().setValue(0)

    def horizontal(self,items):
        h=QHBoxLayout();h.setSpacing(12)
        for w in items:h.addWidget(w)
        self.body.addLayout(h)

    def tile(self,title,value,desc,accent):
        c=card();v=QVBoxLayout(c);v.setContentsMargins(19,19,19,19);v.setSpacing(9)
        top=QHBoxLayout();top.addWidget(label(title,11,muted=True));top.addStretch()
        icon_label=label(accent,18,bold=True);icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(35,35);icon_label.setStyleSheet('background:#393356;color:#c8baff;border-radius:10px;')
        top.addWidget(icon_label);v.addLayout(top)
        val=label(value,30,bold=True);v.addWidget(val)
        v.addWidget(label(desc,11,muted=True));return c

    def overview(self):
        hero=QFrame();hero.setObjectName('hero');hero.setMinimumHeight(225)
        h=QHBoxLayout(hero);h.setContentsMargins(39,27,34,27);h.setSpacing(12)
        left=QVBoxLayout();left.setSpacing(10)
        eyebrow=label('ТВОЯ СИСТЕМА  ·  ЧИСТОТА И КОНТРОЛЬ',11,bold=True)
        eyebrow.setStyleSheet('color:#d0c6ff;letter-spacing:1px;')
        left.addWidget(eyebrow)
        greet=label('Windows, которая работает\nпо твоим правилам.',28,bold=True)
        greet.setStyleSheet('color:white;font-size:28px;font-weight:750;')
        left.addWidget(greet)
        sub=label('Меньше лишнего. Больше контроля. Без сомнительных\nоптимизаций и удаления важных компонентов.',12)
        sub.setStyleSheet('color:#dcd7f6;line-height:1.4;')
        left.addWidget(sub);left.addSpacing(6)
        actions=QHBoxLayout();actions.setSpacing(9)
        actions.addWidget(button('✦   Настроить Windows',lambda:self.navigate('Твики'),True))
        actions.addWidget(button('Просмотр приложений',lambda:self.navigate('Приложения')))
        actions.addStretch();left.addLayout(actions);h.addLayout(left,1)
        art=label('✧\n◈\n✦',44,bold=True);art.setFixedWidth(165);art.setAlignment(Qt.AlignCenter)
        art.setStyleSheet('color:#c9baff;font-size:48px;line-height:0.9;')
        h.addWidget(art)
        self.body.addWidget(hero)
        row=QHBoxLayout();row.setSpacing(14)
        row.addWidget(self.tile('ДОСТУПНО ТВИКОВ',str(len(TWEAKS)),'Настройки с возможностью отката','✧'))
        row.addWidget(self.tile('ПРИЛОЖЕНИЯ',str(len(APPS)),'Каталог необязательных пакетов','▣'))
        row.addWidget(self.tile('ПРОФИЛИ',str(len(PRESETS)),'Для работы, игр и чистой системы','▤'))
        self.body.addLayout(row)
        section=QHBoxLayout();section.addWidget(label('Быстрые действия',18,bold=True));section.addStretch()
        section.addWidget(label('Управляй системой в одном месте',11,muted=True))
        self.body.addLayout(section)
        quick=QHBoxLayout();quick.setSpacing(14)
        for title,desc,icon,action in [
            ('Настройка интерфейса','Приведи Пуск и Проводник в порядок','✧','Твики'),
            ('Удаление лишнего','Выбери необязательные приложения','▣','Приложения'),
            ('Автозагрузка','Управляй запуском программ','◷','Автозагрузка')]:
            c=card();v=QVBoxLayout(c);v.setContentsMargins(20,19,20,19);v.setSpacing(10)
            v.addWidget(label(icon,25,bold=True));v.addWidget(label(title,14,bold=True))
            v.addWidget(label(desc,11,muted=True));v.addWidget(button('Открыть  →',lambda _,x=action:self.navigate(x)))
            quick.addWidget(c)
        self.body.addLayout(quick)
        note=card();v=QVBoxLayout(note);v.setContentsMargins(21,17,21,17);v.setSpacing(8)
        v.addWidget(label('◈   Стабильность важнее сомнительных ускорений',13,bold=True))
        v.addWidget(label('Defender • Windows Update • календарь • уведомления • служба времени • Secure Boot • Store • Xbox • драйверы • «Погода» остаются нетронутыми.',11,muted=True))
        self.body.addWidget(note)

    def tweaks(self):
        self.title('Настройка системы','Только разрешённые параметры HKCU. Исходные значения сохраняются для отката.')
        controls=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText('Поиск по названию или категории...');self.search.textChanged.connect(self.rebuild_tweaks)
        controls.addWidget(self.search,1);controls.addWidget(button('Выбрать всё',lambda:self.select_all(True)));controls.addWidget(button('Снять выбор',lambda:self.select_all(False)));self.body.addLayout(controls)
        self.selection_info=label('',11,muted=True);self.body.addWidget(self.selection_info)
        self.tweaks_host=QWidget();self.tweaks_layout=QVBoxLayout(self.tweaks_host);self.tweaks_layout.setContentsMargins(0,0,0,0);self.tweaks_layout.setSpacing(8);self.body.addWidget(self.tweaks_host)
        row=QHBoxLayout();row.addWidget(button('Предпросмотр и применение',self.apply_selected,True));row.addWidget(button('Откатить мои твики',self.restore));row.addStretch();self.body.addLayout(row)
        self.rebuild_tweaks()

    def select_all(self,on):
        self.selected=set(t['id'] for t in TWEAKS) if on else set();self.rebuild_tweaks()

    def rebuild_tweaks(self):
        clear(self.tweaks_layout);needle=self.search.text().casefold()
        for t in TWEAKS:
            if needle not in (t['title']+' '+t['category']+' '+t['detail']).casefold():continue
            f=QFrame();f.setObjectName('row');r=QHBoxLayout(f);r.setContentsMargins(16,13,16,13);r.setSpacing(13)
            box=QCheckBox();box.setChecked(t['id'] in self.selected)
            box.toggled.connect(lambda checked,ident=t['id']:self.update_selection(ident,checked));r.addWidget(box)
            info=QVBoxLayout();info.setSpacing(4);info.addWidget(label(t['title'],13,bold=True));info.addWidget(label(t['category']+'  ·  '+t['detail'],11,muted=True));r.addLayout(info,1)
            st=core.tweak_status(t);r.addWidget(label(st,11,muted=st!='Применён'))
            self.tweaks_layout.addWidget(f)
        self.selection_info.setText(f'Выбрано настроек: {len(self.selected)}')

    def update_selection(self,ident,on):
        if on:self.selected.add(ident)
        else:self.selected.discard(ident)
        self.selection_info.setText(f'Выбрано настроек: {len(self.selected)}')

    def apply_selected(self):
        chosen=[t for t in TWEAKS if t['id'] in self.selected]
        if not chosen:return QMessageBox.information(self,'Не выбрано','Сначала выбери настройки.')
        details='\n'.join('• '+t['title'] for t in chosen)
        if QMessageBox.question(self,'Предпросмотр изменений',f'Будут изменены параметры текущего пользователя:\n\n{details}\n\nПродолжить?')!=QMessageBox.Yes:return
        self.work('Применение твиков',lambda:core.apply_tweaks([x['id'] for x in chosen]),lambda result:self.show_results(result,'Твики'))

    def restore(self):
        if QMessageBox.question(self,'Откат','Восстановить сохранённые значения твиков?')==QMessageBox.Yes:
            self.work('Откат',core.restore_tweaks,lambda r:self.show_results(r,'Твики'))

    def apps(self):
        self.title('Встроенные приложения','Удаляем только необязательные Appx-пакеты текущего пользователя. Это действие не откатывается автоматически.')
        self.body.addWidget(label('«Погода», Microsoft Store, игровые службы Xbox и системные приложения исключены из каталога.',12,muted=True))
        self.horizontal([button('Проверить установленные',self.fetch_apps),button('Удалить выбранные',self.remove_apps,True)])
        self.apps_host=QWidget();self.apps_layout=QVBoxLayout(self.apps_host);self.apps_layout.setContentsMargins(0,0,0,0);self.apps_layout.setSpacing(8);self.body.addWidget(self.apps_host)
        self.app_checks={};self.body.addWidget(label('Нажми «Проверить установленные», чтобы получить актуальный список.',12,muted=True));

    def fetch_apps(self):self.work('Проверка приложений',core.installed_apps,self.render_apps)

    def render_apps(self,rows):
        if self.current!='Приложения':return
        clear(self.apps_layout);present={p['Name'] for p in rows};self.app_checks={}
        for ident,title in APPS:
            f=QFrame();f.setObjectName('row');r=QHBoxLayout(f);r.setContentsMargins(16,13,16,13)
            ck=QCheckBox();ck.setEnabled(ident in present);self.app_checks[ident]=ck;r.addWidget(ck)
            r.addWidget(label(title,13,bold=True),1)
            r.addWidget(label('УСТАНОВЛЕНО' if ident in present else 'НЕ НАЙДЕНО',11,muted=ident not in present));self.apps_layout.addWidget(f)

    def remove_apps(self):
        ids=[ident for ident,ck in self.app_checks.items() if ck.isChecked()]
        if not ids:return QMessageBox.information(self,'Не выбрано','Нет отмеченных установленных приложений.')
        names={x[0]:x[1] for x in APPS}
        txt='\n'.join('• '+names[i] for i in ids)
        if QMessageBox.warning(self,'Подтвердить удаление',f'Удалить для текущего пользователя?\n\n{txt}\n\nДанные приложений могут быть потеряны. Откат недоступен.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        self.work('Удаление приложений',lambda:core.remove_apps(ids),lambda r:self.show_results(r,'Приложения'))

    def startup(self):
        self.title('Автозагрузка','Управление записями HKCU\\Run с откатом. Системные записи отображаются только для чтения.')
        self.horizontal([button('Обновить список',self.fetch_startup),button('Отключить выбранную',lambda:self.toggle_start(True),True),button('Восстановить',lambda:self.toggle_start(False))])
        self.start_table=QTableWidget(0,3);self.start_table.setHorizontalHeaderLabels(['Программа','Область','Команда']);self.start_table.setAlternatingRowColors(True)
        self.start_table.setSelectionBehavior(QAbstractItemView.SelectRows);self.start_table.setSelectionMode(QAbstractItemView.SingleSelection);self.start_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.start_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents);self.start_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeToContents);self.start_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
        self.start_table.setMinimumHeight(330);self.body.addWidget(self.start_table);self.fetch_startup()

    def fetch_startup(self):self.work('Чтение автозагрузки',core.startup_entries,self.render_startup)

    def render_startup(self,rows):
        if self.current!='Автозагрузка':return
        self.start_map=rows;self.start_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,v in enumerate([r['name'],r['scope'],r['command']]):
                self.start_table.setItem(i,j,QTableWidgetItem(str(v)))

    def toggle_start(self,disable):
        row=self.start_table.currentRow()
        if row<0 or row>=len(self.start_map):return QMessageBox.information(self,'Выбор','Выбери строку.')
        item=self.start_map[row]
        if not item.get('editable') or bool(item.get('disabled'))==disable:
            return QMessageBox.information(self,'Недоступно','Эту запись нельзя изменить здесь.')
        action='Отключить' if disable else 'Восстановить'
        if QMessageBox.question(self,'Автозагрузка',f'{action} «{item["name"]}»?')!=QMessageBox.Yes:return
        self.work('Автозагрузка',lambda:core.toggle_startup(item['name'],disable),lambda r:self.fetch_startup())

    def diagnostics(self):
        self.title('Диагностика системы','Информация читается локально, настройки Windows не изменяются.')
        self.horizontal([button('Обновить сведения',self.fetch_diag)])
        self.diag_host=QWidget();self.diag_layout=QVBoxLayout(self.diag_host);self.diag_layout.setContentsMargins(0,0,0,0);self.diag_layout.setSpacing(8);self.body.addWidget(self.diag_host);self.fetch_diag()

    def fetch_diag(self):self.work('Диагностика',core.system_info,self.render_diag)

    def render_diag(self,info):
        if self.current!='Диагностика':return
        clear(self.diag_layout)
        for key,val in info.items():
            f=QFrame();f.setObjectName('row');r=QHBoxLayout(f);r.setContentsMargins(16,14,16,14);r.addWidget(label(key,12,muted=True));r.addStretch();r.addWidget(label(str(val),13,bold=True));self.diag_layout.addWidget(f)

    def history(self):
        self.title('История действий','Локальный журнал. Можно проверить, что именно менялось.')
        entries=core.history()
        if not entries:self.body.addWidget(label('Здесь пока нет выполненных действий.',12,muted=True))
        for x in entries:
            f=QFrame();f.setObjectName('row');r=QHBoxLayout(f);r.setContentsMargins(16,13,16,13)
            r.addWidget(label(x['time'],11,muted=True));r.addWidget(label(x['action']+' — '+x['result'],12),1);self.body.addWidget(f)

    def profiles(self):
        self.title('Профили и резервирование','Профиль хранит выбор твиков. Применение — только после отдельного подтверждения.')
        for name,ids in PRESETS.items():
            f=QFrame();f.setObjectName('row');r=QHBoxLayout(f);r.setContentsMargins(16,16,16,16)
            a=QVBoxLayout();a.addWidget(label(name,14,bold=True));a.addWidget(label(f'{len(ids)} настроек · список можно изменить во вкладке «Твики»',11,muted=True));r.addLayout(a,1)
            r.addWidget(button('Выбрать',lambda _,name=name:self.choose_preset(name)));self.body.addWidget(f)
        self.horizontal([button('Экспорт выбора в JSON',self.export),button('Импорт выбора из JSON',self.import_)])
        self.body.addWidget(label('Локальная папка данных: '+str(core.DATA),11,muted=True))
        self.body.addWidget(button('Открыть папку резервных копий',self.open_data))
        self.body.addWidget(label('Важно: откат восстанавливает только сохранённые настройки реестра и управляемые записи автозагрузки. Удалённые приложения автоматически не восстановятся.',12,muted=True))

    def choose_preset(self,name):self.selected=set(PRESETS[name]);self.navigate('Твики')

    def export(self):
        path,_=QFileDialog.getSaveFileName(self,'Экспорт профиля','PersonalLiteProfile.json','JSON (*.json)')
        if path:
            try:core.export_profile(path,self.selected);QMessageBox.information(self,'Готово','Профиль сохранён.')
            except Exception as e:QMessageBox.critical(self,'Ошибка',str(e))

    def import_(self):
        path,_=QFileDialog.getOpenFileName(self,'Импорт профиля','','JSON (*.json)')
        if path:
            try:self.selected=set(core.import_profile(path));self.navigate('Твики')
            except Exception as e:QMessageBox.critical(self,'Ошибка',str(e))

    def open_data(self):
        core.DATA.mkdir(parents=True,exist_ok=True)
        if sys.platform=='win32':os.startfile(core.DATA)
        else:QMessageBox.information(self,'Папка',str(core.DATA))

    def work(self,label_,fn,callback):
        self.next_id+=1;ident=self.next_id;self.tasks[ident]=callback;self.status.setText('Выполняется: '+label_+'…')
        future=self.pool.submit(fn)
        def dispatch(done):
            try:result=done.result();error=None
            except Exception as e:result=None;error=str(e)
            self.signals.done.emit(ident,(result,error))
        future.add_done_callback(dispatch)

    def completed(self,ident,payload):
        callback=self.tasks.pop(ident,None)
        if not callback:return
        value,error=payload
        self.status.setText('Готово' if not error else 'Ошибка операции')
        if error:QMessageBox.critical(self,'Не удалось выполнить',error)
        else:callback(value)

    def show_results(self,rows,next_page):
        failed=[f'{name}: {result}' for name,result in rows if 'ОШИБКА' in result]
        if failed:QMessageBox.warning(self,'Выполнено с ошибками','\n'.join(failed)[:2800])
        else:QMessageBox.information(self,'Готово',f'Обработано: {len(rows)}')
        self.navigate(next_page)

    def closeEvent(self,event):
        self.pool.shutdown(wait=False,cancel_futures=True)
        super().closeEvent(event)


def main():
    app=QApplication(sys.argv);app.setStyle('Fusion');app.setStyleSheet(STYLE)
    window=Studio();window.show();sys.exit(app.exec())
