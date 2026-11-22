"""RU/EN UI translations. The registry data and app IDs are never translated."""
import re

EN = {
'Главная':'Home','Очистка системы':'System cleanup','Электропитание':'Power plans',
'Расширенные настройки':'Advanced settings',
'Установка ПО':'App installer',
'Установка программ':'App installer',
'Сведения о системе':'System information',
'Основные характеристики компьютера и Windows.':'Essential PC and Windows details.',
'Редакция':'Edition','Видеокарта':'Graphics card','Объём ОЗУ':'Installed RAM',
'Совместимая версия Windows':'Supported Windows release',
'Версия Windows не проверена':'Windows release not verified',
'Локальная диагностика Windows 10 / 11. Эта страница ничего не изменяет.':'Local read-only Windows 10 / 11 diagnostics.',
'FIELD проверяет совместимость каждой настройки перед применением. Неподдерживаемые изменения блокируются.':'FIELD checks every tweak before applying it. Unsupported changes are blocked.',
'ОС':'OS','Версия':'Version','Сборка':'Build','Поддержка FIELD':'FIELD support',
'Архитектура':'Architecture','Процессор':'Processor','Режим':'Mode',
'Редакция Windows':'Windows edition','Оперативная память':'Memory',
'Свободно ОЗУ':'Free memory','Последняя загрузка':'Last boot',
'Текущий пользователь':'Current user','Не проверена':'Not validated',
'Не поддерживается':'Unsupported',
'Обзор':'Overview','Твики':'Tweaks','Приложения':'Apps','Автозагрузка':'Startup','Диагностика':'Diagnostics','История':'History','Профили':'Profiles','Инструменты':'Tools',
'Настройка системы':'System settings','Встроенные приложения':'Built-in apps','Диагностика системы':'System diagnostics',
'История действий':'Activity history','Профили и резервирование':'Presets & backup',
'Только разрешённые параметры HKCU. Исходные значения сохраняются для отката.':'Only allowlisted HKCU settings. Previous values are backed up for rollback.',
'Удаляем только необязательные Appx-пакеты текущего пользователя. Это действие не откатывается автоматически.':'Remove optional Appx packages for the current user only. Uninstallation cannot be automatically undone.',
'«Погода», Microsoft Store, игровые службы Xbox и системные приложения исключены из каталога.':'Weather, Microsoft Store, Xbox Gaming Services and system apps are excluded.',
'Управление записями HKCU\\Run с откатом. Системные записи отображаются только для чтения.':'Manage HKCU\\Run entries with rollback. System entries are read-only.',
'Информация читается локально, настройки Windows не изменяются.':'Local read-only system information; Windows settings are unchanged.',
'Локальный журнал. Можно проверить, что именно менялось.':'Local activity log showing what changed.',
'Профиль хранит выбор твиков. Применение — только после отдельного подтверждения.':'Presets store tweak selections and require confirmation before applying.',
'Поиск по названию или категории...':'Search by name or category...',
'Выбрать всё':'Select all','Снять выбор':'Clear selection','Предпросмотр и применение':'Preview & apply','Откатить мои твики':'Restore my tweaks',
'Проверить установленные':'Scan installed apps','Удалить выбранные':'Uninstall selected',
'Нажми «Проверить установленные», чтобы получить актуальный список.':'Click “Scan installed apps” to load the current list.',
'УСТАНОВЛЕНО':'INSTALLED','НЕ НАЙДЕНО':'NOT FOUND',
'Обновить список':'Refresh list','Отключить выбранную':'Disable selected','Восстановить':'Restore',
'Программа':'Program','Область':'Scope','Команда':'Command','Обновить сведения':'Refresh details',
'Здесь пока нет выполненных действий.':'No actions recorded yet.',
'Чистая система':'Clean system','Игры':'Gaming','Разработка':'Development','Выбрать':'Select',
'Экспорт выбора в JSON':'Export selection to JSON','Импорт выбора из JSON':'Import selection from JSON',
'Открыть папку резервных копий':'Open backup folder',
'Важно: откат восстанавливает только сохранённые настройки реестра и управляемые записи автозагрузки. Удалённые приложения автоматически не восстановятся.':'Important: rollback restores backed-up registry preferences and managed startup entries only. Removed apps are not restored automatically.',
'Проводник':'File Explorer','Панель задач':'Taskbar','Меню «Пуск»':'Start menu','Рекомендации':'Suggestions','Конфиденциальность':'Privacy','Интерфейс':'Appearance',
'Показывать расширения файлов':'Show file extensions','Видеть .exe, .json, .ts и другие расширения.':'Show .exe, .json, .ts and other extensions.',
'Показывать скрытые файлы':'Show hidden files','Показывать скрытые элементы в Проводнике.':'Display hidden items in File Explorer.',
'Открывать «Этот компьютер»':'Open This PC by default','Вместо главной страницы Проводника.':'Instead of the Explorer home page.',
'Секунды на часах':'Show seconds in taskbar clock','Показывать секунды в системных часах.':'Display seconds in the taskbar clock.',
'Скрыть поле поиска':'Hide taskbar search','Поиск останется доступным через Win + S.':'Search remains available using Win + S.',
'Скрыть кнопку виджетов':'Hide Widgets button','Не удаляет «Погоду» и её данные.':'Does not uninstall Weather or its data.',
'Скрыть недавно открытые файлы':'Hide recently opened files','Не удаляет документы и файлы.':'Does not delete any files or documents.',
'Скрыть недавно добавленные приложения':'Hide recently added apps','Отключает соответствующий список в «Пуске».':'Hides the corresponding Start menu list.',
'Меньше предложений Windows':'Reduce Windows suggestions','Отключает предложения и подсказки пользователя.':'Disables selected Windows tips and suggestions.',
'Отключить предложения в настройках':'Disable Settings suggestions','Персонализированные рекомендации Windows.':'Personalized Windows recommendations.',
'Отключить рекламный идентификатор':'Disable advertising ID','Ограничивает персонализацию рекламы приложениями.':'Reduces app ad personalization.',
'Отключить анимации окон':'Disable window animations','Может сделать интерфейс визуально быстрее.':'May make the interface feel faster.',
'Уменьшить задержку меню':'Reduce menu delay','Задержка появления меню 100 мс.':'Sets menu appearance delay to 100 ms.',
'Применён':'Applied','Не применён':'Not applied','Неизвестно':'Unknown',
'Новый Outlook':'New Outlook','Outlook (новый)':'Outlook (new)',
'Проверка приложений':'Scanning apps','Применение твиков':'Applying tweaks','Откат':'Rollback','Удаление приложений':'Uninstalling apps',
'Автозагрузка':'Startup','Диагностика':'Diagnostics','Чтение автозагрузки':'Reading startup','Готово':'Ready',
'Не выбрано':'Nothing selected','Сначала выбери настройки.':'Select some settings first.',
'Нет отмеченных установленных приложений.':'No installed apps selected.',
'Предпросмотр изменений':'Preview changes','Продолжить?':'Continue?',
'Восстановить сохранённые значения твиков?':'Restore backed-up tweak values?',
'Подтвердить удаление':'Confirm uninstall','Удалить для текущего пользователя?':'Uninstall for current user?',
'Данные приложений могут быть потеряны. Откат недоступен.':'App data may be lost. Automatic rollback is not available.',
'Выбор':'Selection','Выбери строку.':'Select a row.','Недоступно':'Unavailable','Эту запись нельзя изменить здесь.':'This entry cannot be edited here.',
'Отключить':'Disable','Восстановить':'Restore',
'Готово':'Done','Ошибка':'Error','Профиль сохранён.':'Profile saved.','Папка':'Folder',
'Не удалось выполнить':'Operation failed','Ошибка операции':'Operation failed','Выполнено с ошибками':'Completed with errors',
'Экспорт профиля':'Export profile','Импорт профиля':'Import profile',
'ПОИСК БЛОКИРОВОК ФАЙЛА':'FILE LOCK INSPECTOR',
'Показывает приложения, которые используют файл. Не разблокирует принудительно и не удаляет.':'Finds apps using a file. Does not forcibly unlock or delete it.',
'Путь к существующему файлу…':'Path to an existing file…','Обзор…':'Browse…','Найти блокировки':'Find locks',
'Программа':'Program','Перезапускаемая':'Restartable','Выбери файл и запусти проверку.':'Choose a file and run a scan.',
'Файл':'File','Выбери файл.':'Choose a file.','Проверка…':'Scanning…','Поиск блокировки файла':'Looking for file locks',
'Да':'Yes','Нет':'No',
'МОНИТОР ПРОЦЕССОВ':'PROCESS MONITOR',
'Просмотр процессов. Завершение только своего приложения с подтверждением; может привести к потере несохранённых данных.':'Inspect processes. Only your own unprotected apps can be terminated with confirmation; unsaved data may be lost.',
'Поиск по имени, PID или владельцу…':'Search by name, PID or owner…','Обновить':'Refresh','Сведения':'Details','Завершить процесс':'End process',
'Имя':'Name','Владелец':'Owner','Статус':'Status',
'Нажми «Обновить», чтобы прочитать процессы.':'Click Refresh to load processes.','Загрузка списка…':'Loading processes…',
'Сканирование процессов':'Scanning processes','Процессы':'Processes','Выбери процесс в таблице.':'Select a process in the table.',
'Выбери процесс.':'Select a process.','Завершение запрещено: ':'Cannot terminate: ',
'Информация о процессе':'Process details','Память, МБ':'Memory, MB','Состояние':'State','Недоступен':'Unavailable',
'Подтвердить завершение':'Confirm termination','Завершение процесса':'Terminating process','Результат':'Result',
'Несохранённые данные приложения могут быть потеряны.':'Unsaved app data may be lost.',
'ИНСТРУМЕНТЫ':'TOOLS','Загляни внутрь системы.':'Look inside your system.','Файловые блокировки и процессы — без скрытых действий.':'File locks and processes, with no hidden actions.',
'Файлы / Lock Inspector':'Files / Lock Inspector','Процессы / Process Monitor':'Processes / Process Monitor',
'Выбрано настроек: ':'Selected tweaks: ','Показано ':'Showing ',' из ':' of ',' процессов.':' processes.',
'Обнаружено процессов: ':'Processes found: ',
'Пустой список не гарантирует отсутствия всех видов блокировок.':'An empty list does not rule out every kind of lock.',
'Локальная папка данных: ':'Local data folder: ',
' настроек · список можно изменить во вкладке «Твики»':' tweaks · you can edit the list in Tweaks',
'Будут изменены параметры текущего пользователя:':'Current-user preferences will change:',
'Готово · изменения только после подтверждения':'Ready · changes require confirmation',
'Выполняется: ':'Working: ','Обработано: ':'Processed: ',
'Успешно':'Success',
'Завершить процесс':'End process',
}

def detect_system_language() -> str:
    """Detect Windows display language, independent of VPN or IP address."""
    import os
    import locale
    if os.name == 'nt':
        try:
            import ctypes
            from ctypes import wintypes
            name = ctypes.create_unicode_buffer(85)
            get_lang = ctypes.windll.kernel32.GetUserDefaultUILanguage
            langid = int(get_lang())
            # English primary language ID is 0x09; Russian is 0x19.
            # Use native Windows UI language rather than a geo/IP estimate.
            primary = langid & 0x3ff
            return 'ru' if primary == 0x19 else 'en'
        except (OSError, ValueError, AttributeError):
            pass
    try:
        language = locale.getlocale()[0] or ''
    except (ValueError, TypeError):
        language = ''
    return 'ru' if language.lower().startswith('ru') else 'en'

LANG = 'ru'

def set_language(lang: str):
    global LANG
    LANG = lang if lang in ('ru', 'en') else 'ru'

def translate(s: str, lang: str | None = None) -> str:
    lang = lang or LANG
    if lang != 'en' or not s:
        return s
    if s in EN:
        return EN[s]
    out = s
    # Longest-first protects substrings such as «Восстановить» in longer labels.
    for ru, en in sorted(EN.items(), key=lambda kv: len(kv[0]), reverse=True):
        if len(ru) >= 5 and ru in out:
            out = out.replace(ru, en)
    out = re.sub(r'Выбрано настроек:\s*(\d+)', r'Selected tweaks: \1', out)
    return out
