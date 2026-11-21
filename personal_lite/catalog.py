"""Allowlisted, reversible user-scoped Windows preferences."""
TWEAKS = [
    dict(id='extensions', category='Проводник', title='Показывать расширения файлов', detail='Видеть .exe, .json, .ts и другие расширения.', key=r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', name='HideFileExt', value=0, default=1),
    dict(id='hidden', category='Проводник', title='Показывать скрытые файлы', detail='Показывать скрытые элементы в Проводнике.', key=r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', name='Hidden', value=1, default=2),
    dict(id='thispc', category='Проводник', title='Открывать «Этот компьютер»', detail='Вместо главной страницы Проводника.', key=r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', name='LaunchTo', value=1, default=2),
    dict(id='seconds', category='Панель задач', title='Секунды на часах', detail='Показывать секунды в системных часах.', key=r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', name='ShowSecondsInSystemClock', value=1, default=0),
    dict(id='tasksearch', category='Панель задач', title='Скрыть поле поиска', detail='Поиск останется доступным через Win + S.', key=r'Software\Microsoft\Windows\CurrentVersion\Search', name='SearchboxTaskbarMode', value=0, default=1),
    dict(id='widgets', category='Панель задач', title='Скрыть кнопку виджетов', detail='Не удаляет «Погоду» и её данные.', key=r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', name='TaskbarDa', value=0, default=1),
    dict(id='trackdocs', category='Меню «Пуск»', title='Скрыть недавно открытые файлы', detail='Не удаляет документы и файлы.', key=r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', name='Start_TrackDocs', value=0, default=1),
    dict(id='recentapps', category='Меню «Пуск»', title='Скрыть недавно добавленные приложения', detail='Отключает соответствующий список в «Пуске».', key=r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', name='Start_NotifyNewApps', value=0, default=1),
    dict(id='suggest', category='Рекомендации', title='Меньше предложений Windows', detail='Отключает предложения и подсказки пользователя.', key=r'Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager', name='SoftLandingEnabled', value=0, default=1),
    dict(id='suggest2', category='Рекомендации', title='Отключить предложения в настройках', detail='Персонализированные рекомендации Windows.', key=r'Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager', name='SubscribedContent-338393Enabled', value=0, default=1),
    dict(id='adsid', category='Конфиденциальность', title='Отключить рекламный идентификатор', detail='Ограничивает персонализацию рекламы приложениями.', key=r'Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo', name='Enabled', value=0, default=1),
    dict(id='animations', category='Интерфейс', title='Отключить анимации окон', detail='Может сделать интерфейс визуально быстрее.', key=r'Control Panel\Desktop\WindowMetrics', name='MinAnimate', value='0', default='1', regtype='sz'),
    dict(id='menudelay', category='Интерфейс', title='Уменьшить задержку меню', detail='Задержка появления меню 100 мс.', key=r'Control Panel\Desktop', name='MenuShowDelay', value='100', default='400', regtype='sz'),
]
APPS = [
    ('Microsoft.MicrosoftSolitaireCollection','Microsoft Solitaire Collection'),
    ('Clipchamp.Clipchamp','Clipchamp'),
    ('Microsoft.BingNews','Microsoft News'),
    ('Microsoft.GetHelp','Get Help'),
    ('Microsoft.Getstarted','Get Started'),
    ('Microsoft.WindowsFeedbackHub','Feedback Hub'),
    ('Microsoft.MicrosoftOfficeHub','Microsoft 365 Hub'),
    ('Microsoft.People','People'),
    ('Microsoft.WindowsMaps','Maps'),
    ('Microsoft.OutlookForWindows','Outlook (новый)'),
    ('Microsoft.PowerAutomateDesktop','Power Automate Desktop'),
    ('Microsoft.Todos','Microsoft To Do'),
]
PRESETS = {
    'Чистая система': ['extensions','thispc','trackdocs','recentapps','suggest','suggest2','adsid'],
    'Игры': ['extensions','thispc','tasksearch','suggest','adsid'],
    'Разработка': ['extensions','hidden','thispc','seconds','trackdocs'],
}
PROTECTED_NAMES = ['Microsoft.BingWeather','Microsoft.WindowsStore','Microsoft.StorePurchaseApp', 'Microsoft.DesktopAppInstaller','Microsoft.GamingServices','Microsoft.Windows.ShellExperienceHost','Microsoft.Windows.StartMenuExperienceHost','Microsoft.SecHealthUI']
