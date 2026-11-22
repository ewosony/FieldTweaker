# FIELD 1.2.1 — публикация новой версии

Исходники FIELD 1.0/1.1 уже есть в `https://github.com/ewosony/FieldTweaker`.
**Не используй `git init` в новой папке с другим, независимым `.git`**, если хочешь сохранить общую историю и старые версии.

## Как обновить существующий репозиторий

1. Сделай резервную копию своей текущей папки FIELD.
2. Скопируй содержимое этого архива **в рабочую папку существующего Git-репозитория** (там, где находится `.git`). Не удаляй существующую папку `assets/app_icons` с логотипами приложений.
3. Проверь работу `python main.py`, тесты и сборку `build_exe.bat`.
4. В PowerShell из рабочей папки Git:

```powershell
git remote -v
git status
git add .
git commit -m "FIELD 1.2.1 - winter edition"
git push origin main
```

5. После тестирования EXE на Windows опубликуй новую версию (пример с GitHub CLI):

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" release create v1.2.1 ".\dist\FIELD 1.2.1.exe" --repo ewosony/FieldTweaker --target main --title "FIELD 1.2.1 — Winter Edition" --notes "Winter edition: snowfall, string lights, seasonal colors and optional toggle. Includes FIELD 1.2 features."
```

Если тег уже создан, не переписывай его: для следующего исправления используй новый номер, например `v1.2.2`.

Исходники FIELD 1.0 и 1.1 сохраняются в GitHub History и по существующим тегам.
