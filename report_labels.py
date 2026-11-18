"""Подписи отчёта о проблеме на языках интерфейса (сборка 60). Отдельно от app.py: там только английский текст."""

LABELS = {
    "en": {"title": "problem report", "time": "Time", "version": "Version", "build": "Build", "system": "System",
           "app": "app", "source": "source", "move": "Move address", "signed": "Signed in to Move", "yes": "yes",
           "no": "no", "ssh": "pad control (SSH)", "on": "on", "off": "off", "lib": "Library folder",
           "data": "Data folder", "what": "What happened:", "nodesc": "(no description)",
           "errors": "Recent errors (cache/errors.log):", "slow": "Slow Move commands (cache/ssh-timing.log):",
           "empty": "(empty)", "unread": "(could not read)"},
    "ru": {"title": "отчёт о проблеме", "time": "Время", "version": "Версия", "build": "Сборка", "system": "Система",
           "app": "программа", "source": "из исходников", "move": "Адрес Move", "signed": "Вход на Move", "yes": "да",
           "no": "нет", "ssh": "управление пэдами (SSH)", "on": "вкл.", "off": "выкл.", "lib": "Папка проектов",
           "data": "Папка данных", "what": "Что случилось:", "nodesc": "(без описания)",
           "errors": "Последние ошибки (cache/errors.log):", "slow": "Медленные команды Move (cache/ssh-timing.log):",
           "empty": "(пусто)", "unread": "(не прочитать)"},
}
