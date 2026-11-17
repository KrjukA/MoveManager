/* Языки интерфейса (сборка 56). Английский текст — ключ: в коде строки английские, здесь — переводы.
   Переводчик сам следит за страницей (MutationObserver): тексты, title/placeholder/aria-label, confirm/prompt.
   Нет перевода — остаётся английский. Данные (имена проектов, сэмплов, пресетов) помечены translate="no"
   и не трогаются; в составных сообщениях не переводится текст в кавычках “…” "…" «…».
   Добавить язык = добавить ещё один словарь в I18N и кнопку. */
"use strict";
const I18N = {ru: {
exact: {
  // шапка и разделы
  "Projects": "Проекты", "Samples": "Сэмплы", "Presets": "Пресеты", "Refresh": "Обновить", "Refreshing…": "Обновление…",
  "Report": "Отчёт", "Light": "Светлая", "Dark": "Тёмная", "Switch theme": "Сменить тему", "Monitor": "Слушать вход",
  "🎧 Monitor": "🎧 Слушать", "🎧 Monitoring": "🎧 Слушаю", "Default input": "Основной вход",
  "Show all inputs… (allow access)": "Показать все входы… (разрешить доступ)", "Monitor input": "Вход для прослушивания",
  "Monitor level": "Уровень входа", "Input to monitor (e.g. Move over USB)": "Какой вход слушать (например, Move по USB)",
  "Listen to the chosen input through the computer — independent of recording": "Слушать выбранный вход через компьютер — независимо от записи",
  "Move connected": "Move подключён", "Move offline": "Move не в сети", "code needed": "нужен код", "Pads connected": "Пэды подключены",
  "connecting…": "подключение…", "App build number": "Номер сборки программы",
  "Something went wrong? Save a short report to send to the author": "Что-то не так? Сохраните короткий отчёт и отправьте the author",
  // колонки
  "Computer": "Компьютер", "Add…": "Добавить…", "+ Group": "+ Группа", "+ Folder": "+ Папка", "Folder…": "Папка…",
  "Add .ablbundle projects that are already on this computer": "Добавить проекты .ablbundle, которые уже есть на этом компьютере",
  "Create a project group": "Создать группу проектов", "Ungrouped": "Без группы", "Rename": "Переименовать", "Delete group": "Удалить группу",
  "Click to collapse or expand": "Нажмите, чтобы свернуть или развернуть",
  "The group is removed; its projects move to Ungrouped": "Группа удаляется, её проекты переходят в «Без группы»",
  "Rename group": "Переименовать группу", "New group name": "Название новой группы", "New group…": "Новая группа…",
  "Looking for Move on the network…": "Ищу Move в сети…", "No projects on Move.": "На Move нет проектов.",
  "Folder is empty. Drag a project here from Move.": "Папка пуста. Перетащите сюда проект с Move.",
  "Retry": "Повторить", "Enter code": "Ввести код", "Connect": "Подключить", "Move address": "Адрес Move",
  "move.local or 192.168.1.23": "move.local или 192.168.1.23",
  "If Move isn't found by name, type its IP address — on Move: Settings → Wi-Fi.": "Если Move не находится по имени, введите его IP-адрес — на Move: Settings → Wi-Fi.",
  "On a Mac also allow the app in System Settings → Privacy & Security → Local Network.": "На Mac также разрешите программе доступ: Системные настройки → Конфиденциальность и безопасность → Локальная сеть.",
  "Move is unreachable. Check that it is on and on the same Wi-Fi network.": "Move недоступен. Проверьте, что он включён и в той же сети Wi-Fi.",
  "Move is unreachable. Check that it is on and on the same network.": "Move недоступен. Проверьте, что он включён и в той же сети.",
  "Enter the confirmation code from the Move screen.": "Введите код подтверждения с экрана Move.",
  "No pad": "Без пэда", "This pad is taken": "Этот пэд занят", "Projects on Move and on this computer": "Проекты на Move и на этом компьютере",
  // окна
  "Confirmation code": "Код подтверждения", "Move shows a code on its screen. Enter it to connect.": "Move показывает код на экране. Введите его, чтобы подключиться.",
  "Code from the Move screen": "Код с экрана Move", "Later": "Позже", "Move is not responding": "Move не отвечает",
  "Move did not show a code. Make sure it is on and not booting.": "Move не показал код. Убедитесь, что он включён и не загружается.",
  "Report a problem": "Сообщить о проблеме", "Cancel": "Отмена", "Save report": "Сохранить отчёт", "What happened": "Что случилось",
  "What did you do, and what went wrong? A report file is saved to your Desktop — send it to the author. It contains this text, the app version, your system and recent errors; no passwords or keys.":
    "Что вы делали и что пошло не так? Файл-отчёт сохранится на Рабочий стол — отправьте его the author. В нём этот текст, версия программы, система и последние ошибки; без паролей и ключей.",
  "E.g. I dragged two loops onto track 2 of “My Song” and got an error…": "Например: перетащил два лупа на дорожку 2 в «Моей песне» и получил ошибку…",
  "Could not save the report": "Не удалось сохранить отчёт",
  // правая панель проекта
  "Pick a project on the left or right. Drag within a pane to reorder, between panes to copy.": "Выберите проект слева или справа. Перетаскивание внутри колонки меняет порядок, между колонками — копирует.",
  "To computer →": "На компьютер →", "← To Move": "← На Move", "with audio": "со звуком", "Audio format": "Формат звука",
  "Show in Finder": "Показать в Finder", "Delete": "Удалить", "Group": "Группа", "Project group": "Группа проекта",
  "Description": "Описание", "Notes": "Заметки", "In short: what this project is": "Коротко: что это за проект",
  "Ideas, to-dos, where it was played…": "Идеи, что доделать, где играл…", "Notes saved": "Заметки сохранены",
  "Saved in meta.json in the project folder.": "Хранится в meta.json в папке проекта.",
  "Descriptions and notes for projects on Move are stored on the computer in the app's config.json, not on the device. They move into the project folder when you copy it.":
    "Описания и заметки проектов на Move хранятся на компьютере в config.json программы, а не на девайсе. При копировании они переходят в папку проекта.",
  "Tracks": "Дорожки", "Clips": "Клипы", "History": "История", "Apply changes": "Применить", "Reset": "Сбросить",
  "Camelot": "Камелот", "Camelot wheel": "Колесо Камелота", "Camelot code of this key": "Код Камелота этой тональности",
  "Compatible keys light up in their wheel colour — on the wheel and as the mark on each project. Click a sector to set that key.":
    "Совместимые тональности подсвечиваются цветом колеса — на колесе и меткой на каждом проекте. Нажмите на сектор, чтобы поставить эту тональность.",
  "Double-click to change key, scale and tempo": "Двойной щелчок — изменить тональность, лад и темп",
  "Root": "Тоника", "Scale": "Лад", "Tempo, bpm": "Темп, bpm", "Done": "Готово", "Project name": "Название проекта",
  "Double-click to rename": "Двойной щелчок — переименовать", "Drag to reorder": "Перетащите, чтобы изменить порядок",
  "Reading project…": "Читаю проект…", "Audio track": "Аудиодорожка", "No audio": "Без звука", "Play": "Слушать",
  "▶ Play": "▶ Слушать", "❚❚ Pause": "❚❚ Пауза", "Export from Move": "Экспорт с Move", "Record input": "Записать вход",
  "File…": "Файл…", "Sound": "Звук",
  "Leave this project on Move before sending changes — Move saves the open project on its own and would overwrite them.":
    "Выйдите из этого проекта на Move, прежде чем отправлять изменения: Move сам сохраняет открытый проект и перезапишет их.",
  "edit the project on Move in place — pad and color are kept (otherwise a \"_edit\" copy is made)": "править проект на Move на месте — пэд и цвет сохраняются (иначе создаётся копия «_edit»)",
  "replace the original — the project moves to another pad (otherwise a \"_edit\" copy is made)": "заменить оригинал — проект переедет на другой пэд (иначе создаётся копия «_edit»)",
  // клипы
  "The project has no clip cells.": "В проекте нет ячеек для клипов.",
  "Pick a cell: a filled one can be saved as .mid, any can take a .mid. The cell shows note count and length in bars.":
    "Выберите ячейку: заполненную можно сохранить как .mid, в любую можно загрузить .mid. В ячейке — число нот и длина в тактах.",
  "Save .mid": "Сохранить .mid", "Delete clip": "Удалить клип", "Load .mid": "Загрузить .mid", "Generate…": "Сгенерировать…",
  "Add loops…": "Добавить лупы…", "Remove the clip from this cell": "Убрать клип из этой ячейки",
  "Notes from the MIDI file become the clip in this cell": "Ноты из MIDI-файла станут клипом в этой ячейке",
  "Generate a drum pattern for this cell": "Сгенерировать барабанный рисунок для этой ячейки",
  "The generator works on Drum Rack tracks": "Генератор работает на дорожках с Drum Rack",
  "This is an audio track; MIDI cannot go into it": "Это аудиодорожка, MIDI в неё не положить",
  "Import to Move needs pad control enabled": "Для загрузки на Move включите управление пэдами",
  "Deleting a clip on Move needs pad control enabled": "Для удаления клипа на Move включите управление пэдами",
  "Adding loops on Move needs pad control enabled": "Для добавления лупов на Move включите управление пэдами",
  "Editing clips on Move needs pad control enabled": "Для правки клипов на Move включите управление пэдами",
  "Restoring on Move needs pad control enabled": "Для отката на Move включите управление пэдами",
  "Adding loops works for projects on Move": "Лупы добавляются только в проекты на Move",
  "Only notes are taken from the file; clip length is rounded up to whole bars.": "Из файла берутся только ноты; длина клипа округляется вверх до целых тактов.",
  "The project is backed up before writing.": "Перед записью сохраняется версия проекта.",
  "Several files fill the track to the right, in file-name order. Loop tempo comes from the file name (\"160bpm\"); without it the loop is fitted to whole bars, like Move does.":
    "Несколько файлов ложатся вправо по дорожке в порядке имён. Темп лупа берётся из имени файла («160bpm»), без него луп подгоняется под целые такты, как это делает Move.",
  "Pick WAV, AIFF, FLAC or MP3 files: they go to Samples/UPLOAD on Move and fill this track from this cell to the right":
    "Выберите файлы WAV, AIFF, FLAC или MP3: они попадут в Samples/UPLOAD на Move и заполнят дорожку от этой ячейки вправо",
  "Drop loops on a cell of an audio track": "Бросайте лупы на ячейку аудиодорожки", "Loops can only go into an audio track": "Лупы кладутся только на аудиодорожку",
  "Cell is empty": "Ячейка пуста", "Cell is occupied": "Ячейка занята", "Pick a different cell": "Выберите другую ячейку",
  "Pick a different cell to paste into": "Выберите другую ячейку для вставки", "Could not change the clips": "Не удалось изменить клипы",
  "Could not delete the clip": "Не удалось удалить клип", "Could not save the clip": "Не удалось сохранить клип", "Could not load the clip": "Не удалось загрузить клип",
  "Could not write the clip": "Не удалось записать клип", "Could not add the loops": "Не удалось добавить лупы",
  "A MIDI clip can only go into a MIDI track": "MIDI-клип кладётся только на MIDI-дорожку",
  "Only WAV, AIFF, FLAC and MP3 files can be added as loops": "Как лупы можно добавить только файлы WAV, AIFF, FLAC и MP3",
  "The project on Move was changed on the device (Move saves an open project on its own), so this cell no longer matches. The view was refreshed — check it and try again. Leave the project on Move while editing it here.":
    "Проект на Move изменился на самом девайсе (Move сам сохраняет открытый проект), поэтому ячейка уже не совпадает. Вид обновлён — проверьте и попробуйте ещё раз. Пока правите проект здесь, выйдите из него на Move.",
  // генератор
  "Genre": "Жанр", "Genres": "Жанры", "Another": "Другой", "Put in cell": "Положить в ячейку", "Bars": "Такты", "Swing": "Свинг",
  "Mutation": "Мутация", "Ghosts": "Призрачные удары", "Euclid": "Евклид", "Loading genres…": "Загружаю жанры…", "Could not load genres": "Не удалось загрузить жанры",
  "Quiet snare hits around the main ones": "Тихие удары малого барабана вокруг основных",
  "Evenly spread hits on one hat/percussion pad (euclidean rhythm): 0 — off, higher — more hits": "Равномерные удары на одном пэде хэта или перкуссии (евклидов ритм): 0 — выкл., больше — больше ударов",
  "Half time: the rhythm plays at half speed — at 140 bpm it feels like 70": "Половинный размер: ритм идёт вдвое медленнее — при 140 bpm ощущается как 70",
  "½ time: off": "½ темпа: выкл.", "½ time: all": "½ темпа: всё", "½ time: kick": "½ темпа: бочка", "½ time: kick + snare": "½ темпа: бочка + малый",
  "At this Mutation the genre's patterns sound the same. Raise Mutation for new variations.": "При такой мутации рисунки жанра звучат одинаково. Поднимите мутацию для новых вариантов.",
  "Reading the project's kit…": "Читаю набор пэдов проекта…", "Learning from MIDI folder": "Учусь на папке MIDI", "MIDI folder": "Папка MIDI",
  "Path to a folder with drum .mid files": "Путь к папке с барабанными .mid", "MIDI folder removed": "Папка MIDI отключена",
  "■ Stop": "■ Стоп", "▶ Play pattern": "▶ Слушать рисунок",
  // история
  "No saved versions yet. A version is saved before every change made here.": "Сохранённых версий пока нет. Версия сохраняется перед каждой правкой из программы.",
  "A version is saved before every change made here (up to 20). Restore puts the project back; the current version is saved first, so a restore can be undone.":
    "Перед каждой правкой из программы сохраняется версия (до 20). «Вернуть» возвращает проект к ней; текущая версия сохраняется заранее, поэтому откат можно отменить.",
  "Restore": "Вернуть", "Put the project back to this version": "Вернуть проект к этой версии", "older backup": "старая копия",
  "Reading history…": "Читаю историю…", "Could not read history": "Не удалось прочитать историю", "Could not restore the version": "Не удалось вернуть версию",
  "Restoring on Move needs pad control enabled.": "Для отката на Move включите управление пэдами.",
  "This version is no longer in History": "Этой версии больше нет в истории", "This version is damaged and can't be restored": "Эта версия повреждена, вернуть её нельзя",
  // пэды и SSH
  "Enable pad control": "Включить управление пэдами", "Enabling pad control…": "Включаю управление пэдами…", "Reconnect": "Переподключить",
  "Pad layout and editing a project without moving it off its pad need SSH access to Move. The app creates its own key and asks you to confirm it with the wheel on the device.":
    "Раскладка пэдов и правка проекта без переноса с пэда требуют SSH-доступа к Move. Программа создаёт свой ключ и просит подтвердить его колесом на девайсе.",
  "Confirm the key with the wheel on Move": "Подтвердите ключ колесом на Move",
  "Move did not add the key. Confirm the request with the wheel on the device and try again.": "Move не добавил ключ. Подтвердите запрос колесом на девайсе и попробуйте снова.",
  "Enable pad control first": "Сначала включите управление пэдами", "Move did not answer over SSH": "Move не ответил по SSH",
  "Two projects cannot share one pad": "Два проекта не могут быть на одном пэде", "Pad number must be between 1 and 32": "Номер пэда — от 1 до 32",
  // сэмплы и пресеты
  "Samples: Move library and folders on this computer": "Сэмплы: библиотека Move и папки этого компьютера",
  "Track presets: Move library and folders on this computer": "Пресеты дорожек: библиотека Move и папки этого компьютера",
  "Left: the library on Move. Right: a folder on this computer, or a second view of Move.": "Слева — библиотека на Move. Справа — папка на этом компьютере или вторая панель Move.",
  "Reading the library on Move…": "Читаю библиотеку на Move…", "Opening the folder…": "Открываю папку…", "Read again": "Прочитать заново",
  "Unused": "Неиспользуемые", "Search": "Поиск", "Upload": "Загрузить", "Used in": "Используется в", "Name by project": "Имя по проекту",
  "Show only files no project, preset or Schwung slot uses": "Показывать только файлы, которыми не пользуется ни проект, ни пресет, ни слот Schwung",
  "Files inside, including subfolders, that a project, preset or Schwung slot uses": "Файлы внутри (и в подпапках), которыми пользуется проект, пресет или слот Schwung",
  "Create a folder here": "Создать здесь папку", "New folder": "Новая папка", "New folder name": "Название новой папки", "New name": "Новое имя",
  "Up one folder. Drop a file here to put it one level up": "На уровень выше. Бросьте сюда файл, чтобы переложить его на уровень выше",
  "Click a file or folder for details, double-click to open or play.": "Щелчок — подробности, двойной щелчок — открыть или прослушать.",
  "Double-click to open": "Двойной щелчок — открыть", "Double-click to open. Drop here to put files into this folder.": "Двойной щелчок — открыть. Бросьте сюда файлы, чтобы положить их в эту папку.",
  "Copy into the folder open on the right": "Скопировать в папку, открытую справа", "Copy into the folder open on the left": "Скопировать в папку, открытую слева",
  "Copy to computer →": "Скопировать на компьютер →", "Pick a folder on this computer": "Выберите папку на этом компьютере", "Folders on this computer": "Папки этого компьютера",
  "Choose folder…": "Выбрать папку…", "Choose…": "Выбрать…", "Change…": "Изменить…", "Stop using this folder": "Не использовать эту папку",
  "Clear selection": "Снять выделение", "A second view of the Move library, to move things between its folders": "Вторая панель библиотеки Move — чтобы переносить файлы между её папками",
  "Choose a folder in the Finder window…": "Выберите папку в окне Finder…", "Path to the projects folder": "Путь к папке проектов",
  "Drag between computer and Move to copy. Drag inside Move to move — every project, preset and Schwung slot that uses the file is updated, and you see the list first. Inside the computer, dragging moves the file.":
    "Перетаскивание между компьютером и Move копирует. Внутри Move — переносит: все проекты, пресеты и слоты Schwung с этим файлом обновляются, список покажется заранее. Внутри компьютера перетаскивание переносит файл.",
  "Double-click the name to rename. To move, drag the file onto a folder. Either way every project, preset and Schwung slot that uses it is updated; you see the list first, and a backup of each changed file is saved on the computer.":
    "Двойной щелчок по имени — переименовать. Чтобы перенести, перетащите файл на папку. В любом случае все проекты, пресеты и слоты Schwung с этим файлом обновятся; список покажется заранее, а копия каждого изменённого файла сохранится на компьютере.",
  "Drag any of them to move or copy them all. Cmd-click adds or removes one, Shift-click selects a range.": "Перетащите любой, чтобы перенести или скопировать все. Cmd-щелчок добавляет или убирает один, Shift-щелчок выделяет диапазон.",
  "Nothing found.": "Ничего не найдено.", "No unused files here.": "Здесь нет неиспользуемых файлов.", "Empty folder. Drag files here.": "Пустая папка. Перетащите сюда файлы.",
  "The file is no longer there.": "Этого файла уже нет.", "The folder is no longer there.": "Этой папки уже нет.",
  "Checking which projects use it…": "Проверяю, какие проекты им пользуются…", "Wait — the previous operation is still running": "Подождите — предыдущая операция ещё идёт",
  "The sample library on Move needs pad control enabled (SSH)": "Для библиотеки сэмплов на Move включите управление пэдами (SSH)",
  "Copying to and from Move needs pad control enabled (SSH)": "Для копирования с Move и на Move включите управление пэдами (SSH)",
  "Moving files": "Переношу файлы", "Updating references": "Обновляю ссылки", "Reading affected files": "Читаю затронутые файлы", "Rolling back": "Откатываю",
  "Nothing to move": "Нечего переносить", "A folder can't be moved into itself": "Папку нельзя перенести саму в себя",
  "The section folder itself can't be deleted": "Саму папку раздела удалить нельзя", "This folder can't be renamed here": "Эту папку здесь переименовать нельзя",
  "Move has no find/stat commands, so the library can't be read safely": "На Move нет команд find/stat, поэтому библиотеку нельзя прочитать безопасно",
  "Supported: WAV, AIFF, FLAC, MP3 (and presets)": "Поддерживаются WAV, AIFF, FLAC, MP3 (и пресеты)",
  "Supported files: WAV, MP3, M4A, WebM and OGG": "Поддерживаются WAV, MP3, M4A, WebM и OGG",
  "This folder is outside your home folder and external drives": "Эта папка вне домашней папки и внешних дисков",
  "The system folder picker isn't available on this system — type the path": "Системное окно выбора папки недоступно — введите путь",
  // запись и звук
  "Audio input for recording": "Вход для записи", "Input level": "Уровень входа", "Recording cancelled": "Запись отменена",
  "Recording saved as project audio": "Запись сохранена как звук проекта", "Project audio updated": "Звук проекта обновлён",
  "File attached as project audio": "Файл прикреплён как звук проекта", "Could not save the audio": "Не удалось сохранить звук", "Could not play": "Не удалось воспроизвести",
  "● Recording": "● Запись", "Start recording": "Начать запись", "Stop": "Стоп", "Audio export skipped": "Экспорт звука пропущен",
  "Stop waiting for the export: the project stays without audio": "Не ждать экспорт: проект останется без звука",
  "Move reported that the export failed": "Move сообщил, что экспорт не удался", "Move started the export but stopped responding": "Move начал экспорт и перестал отвечать",
  "Move did not return an audio link": "Move не дал ссылку на звук", "Move is building the file": "Move собирает файл", "Waiting in the export queue": "Жду в очереди экспорта",
  "To choose an audio input, allow microphone access for this page (the browser asks once)": "Чтобы выбрать аудиовход, разрешите этой странице доступ к микрофону (браузер спросит один раз)",
  "No other audio inputs found": "Других аудиовходов не найдено",
  // общие и сервер
  "Working…": "Выполняю…", "Reading…": "Читаю…", "Applying changes…": "Применяю изменения…", "Something went wrong": "Что-то пошло не так",
  "Did not work": "Не получилось", "Copied": "Скопировано", "Cut": "Вырезано", "Renamed": "Переименовано", "More": "Ещё", "Open": "Открыть",
  "Reading project on Move": "Читаю проект на Move", "Writing changes": "Записываю изменения", "Writing clip": "Записываю клип", "Writing clips": "Записываю клипы",
  "Removing clip": "Убираю клип", "Downloading project": "Скачиваю проект", "Uploading to Move": "Загружаю на Move", "Applying changes": "Применяю изменения",
  "Replacing the original": "Заменяю оригинал", "Saving a copy of the original": "Сохраняю копию оригинала", "Saving a copy of the previous project": "Сохраняю копию прежнего проекта",
  "Saving a copy to the computer before deleting": "Сохраняю копию на компьютер перед удалением", "Deleting from Move": "Удаляю с Move",
  "Removing the previous project from the pad": "Убираю прежний проект с пэда", "Copying Schwung state": "Копирую состояние Schwung",
  "Restoring Schwung state": "Восстанавливаю состояние Schwung", "Downloading recording from Move": "Скачиваю запись с Move", "Preparing key": "Готовлю ключ",
  "Checking connection": "Проверяю подключение", "Checking": "Проверяю", "Project saved": "Проект сохранён", "Writing the saved version": "Записываю сохранённую версию",
  "Waiting for another edit of this project to finish": "Жду окончания другой правки этого проекта",
  "Invalid request": "Неверный запрос", "Invalid identifier": "Неверный идентификатор", "Invalid name": "Недопустимое имя", "Empty name": "Пустое имя",
  "Invalid file name": "Недопустимое имя файла", "Invalid path": "Неверный путь", "Invalid key": "Неверная тональность", "Invalid tempo": "Неверный темп",
  "Tempo must be between 40 and 300 bpm": "Темп — от 40 до 300 bpm", "Invalid track number": "Неверный номер дорожки", "Invalid notes": "Неверные ноты",
  "Invalid clip length": "Неверная длина клипа", "Invalid kit": "Неверный набор", "Invalid recording name": "Неверное имя записи",
  "No cell given": "Не указана ячейка", "No cells given": "Не указаны ячейки", "No files given": "Нет файлов", "No such track in the project": "В проекте нет такой дорожки",
  "No such scene in the project": "В проекте нет такой сцены", "Unknown clip operation": "Неизвестное действие с клипом", "Unknown library section": "Неизвестный раздел библиотеки",
  "The file is too large": "Файл слишком большой", "The file is empty": "Файл пустой", "Not a file": "Это не файл", "Song.abl not found in the bundle": "В бандле нет Song.abl",
  "No .ablbundle in the project folder": "В папке проекта нет .ablbundle", "Project not found in the folder": "Проект не найден в папке", "Project not found on Move": "Проект не найден на Move",
  "A project with this name already exists in the folder": "Проект с таким именем уже есть в папке", "MIDI folder not found": "Папка MIDI не найдена",
  "This track has no Drum Rack": "На этой дорожке нет Drum Rack", "Unsafe Schwung archive": "Небезопасный архив Schwung",
  "The project to replace is no longer on Move": "Проекта, который нужно заменить, уже нет на Move",
  "This project is no longer on Move (it was replaced or deleted). The list has been refreshed.": "Этого проекта уже нет на Move (его заменили или удалили). Список обновлён.",
  "This project is not on Move now. Upload it to Move and export again.": "Этого проекта сейчас нет на Move. Загрузите его на Move и повторите экспорт.",
  "The new project was uploaded but could not be identified — the old one was kept": "Новый проект загружен, но его не удалось опознать — старый оставлен",
  "The new version was uploaded but could not be identified — the original was kept": "Новая версия загружена, но её не удалось опознать — оригинал оставлен",
  "Enter Move's address like 192.168.1.23 or move.local": "Введите адрес Move, например 192.168.1.23 или move.local",
  "Audio clips can't be moved yet": "Аудиоклипы пока нельзя переносить",
  "Some samples of this version are gone": "Некоторых сэмплов этой версии уже нет",
  ".ablbundle files needed": "Нужны файлы .ablbundle", "Recordings": "Записи",
  "Project": "Проект", "on computer": "на компьютере", "● Record input": "● Записать вход", "Right panel shows": "Справа показано", "Section": "Раздел",
  "No audio for this project yet.": "У этого проекта пока нет звука.", "Copy exists on the computer": "Копия есть на компьютере",
  "Move exports the project audio again": "Move заново экспортирует звук проекта",
  "Move exports the project audio; if the export fails, the longest recording of this set from Recordings is used": "Move экспортирует звук проекта; если экспорт не удался, берётся самая длинная запись этого проекта из Recordings",
  "Uses Schwung": "Использует Schwung", "Uses Schwung · Schwung state saved with the project": "Использует Schwung · состояние Schwung сохранено с проектом",
  "Uses Schwung; its state is copied when you move the project to the computer (pad control on)": "Использует Schwung; его состояние копируется при переносе проекта на компьютер (при включённом управлении пэдами)",
  "Uses Schwung presets; no Schwung state saved": "Использует пресеты Schwung; состояние Schwung не сохранено",
  "Schwung state is saved with this project and restored when uploading to Move": "Состояние Schwung сохранено с этим проектом и восстанавливается при загрузке на Move",
  "Upload files from this computer into this folder on Move (or drag them here from Finder)": "Загрузить файлы с этого компьютера в эту папку на Move (или перетащите их сюда из Finder)",
  "Approximate: from the scale's note set": "Приблизительно: по нотам лада", "Camelot code": "Код Камелота",
  "Approximate code: the scale is mapped to the major/minor with the same notes.": "Код приблизительный: лад сопоставлен с мажором или минором из тех же нот.",
  "⌘C copy · ⌘X cut · ⌘V paste · ⌫ delete · arrows move · drag: move, onto a clip: swap, ⌥ drag: copy": "⌘C копия · ⌘X вырезать · ⌘V вставить · ⌫ удалить · стрелки — по сетке · тащить: перенос, на клип — обмен, ⌥ — копия",
  "drop WAV, AIFF, FLAC or MP3 files on an audio track cell to add loops": "бросьте WAV, AIFF, FLAC или MP3 на ячейку аудиодорожки, чтобы добавить лупы",
  "Esc: clear clipboard": "Esc — очистить буфер", "Pads": "Пэды", "Audio": "Аудио",
  "A folder with drum .mid files to learn from; its subfolders become genres": "Папка с барабанными .mid для обучения; её подпапки становятся жанрами",
  "no folder": "папка не выбрана", "unused": "не используется", "Language": "Язык"
},
patterns: [
  // сообщения с именами и числами (группы $1… переносятся как есть)
  [/^Clip deleted: track (\d+), scene (\d+)(.*)$/s, "Клип удалён: дорожка $1, сцена $2$3"],
  [/^Clip saved: (.*)$/s, "Клип сохранён: $1"],
  [/^Clip from “(.+)” loaded: track (\d+), scene (\d+)(.*)$/s, "Клип из «$1» загружен: дорожка $2, сцена $3$4"],
  [/^Clip from "(.+)" loaded: track (\d+), scene (\d+)(.*)$/s, "Клип из «$1» загружен: дорожка $2, сцена $3$4"],
  [/^(Clip copied|Clip moved|Clips swapped): track (\d+), scene (\d+) → track (\d+), scene (\d+)(.*)$/s, (m, v, a, b, c, d, rest) => `${{"Clip copied":"Клип скопирован","Clip moved":"Клип перенесён","Clips swapped":"Клипы поменялись местами"}[v]}: дорожка ${a}, сцена ${b} → дорожка ${c}, сцена ${d}${rest}`],
  [/^(Copied|Cut): track (\d+), scene (\d+)\. Pick a cell and press ⌘V$/, (m, v, a, b) => `${v==="Cut"?"Вырезано":"Скопировано"}: дорожка ${a}, сцена ${b}. Выберите ячейку и нажмите ⌘V`],
  [/^Generated pattern written: track (\d+), scene (\d+)(.*)$/s, "Сгенерированный рисунок записан: дорожка $1, сцена $2$3"],
  [/^Track (\d+), scene (\d+):$/, "Дорожка $1, сцена $2:"],
  [/^Track (\d+), scene (\d+): (\d+) notes, ([\d.]+) bars$/, "Дорожка $1, сцена $2: нот $3, тактов $4"],
  [/^Track (\d+), scene (\d+): empty$/, "Дорожка $1, сцена $2: пусто"],
  [/^Track (\d+), scene (\d+): (.+) · ([\d.]+) bars · loop ([\d.]+) bpm(.*)$/s, "Дорожка $1, сцена $2: $3 · тактов $4 · луп $5 bpm$6"],
  [/^Delete the clip in track (\d+), scene (\d+)\?(.*)$/s, "Удалить клип на дорожке $1, сцена $2?$3"],
  [/^The cell \(track (\d+), scene (\d+)\) already has a clip\. Replace it\?$/, "В ячейке (дорожка $1, сцена $2) уже есть клип. Заменить?"],
  [/^The cell \(track (\d+), scene (\d+)\) already has a clip\. Replace it with the generated pattern\?$/, "В ячейке (дорожка $1, сцена $2) уже есть клип. Заменить его сгенерированным рисунком?"],
  [/^The cell \(track (\d+), scene (\d+)\) already has a clip\. Replace it with notes from “(.+)”\?$/, "В ячейке (дорожка $1, сцена $2) уже есть клип. Заменить его нотами из «$3»?"],
  [/^The cell \(track (\d+), scene (\d+)\) already has a clip\. Replace it with notes from "(.+)"\?$/, "В ячейке (дорожка $1, сцена $2) уже есть клип. Заменить его нотами из «$3»?"],
  [/^Replace (\d+) clips? in track (\d+), scenes? ([\d, ]+)\?$/, "Заменить клипы ($1) на дорожке $2, сцены $3?"],
  [/^Replace (\d+) clip\(s\) in track (\d+)\?$/, "Заменить клипы ($1) на дорожке $2?"],
  [/^Uploading (\d+) loops?…$/, "Загружаю лупы: $1…"],
  [/^Loops added: (\d+) to track (\d+)(.*)$/s, "Добавлено лупов: $1 на дорожку $2$3"],
  [/^Loop added T(\d+) S(\d+)$/, "Луп добавлен: Д$1 С$2"],
  [/^Loops added T(\d+) S(\d+)–S(\d+)$/, "Лупы добавлены: Д$1 С$2–С$3"],
  [/^Uploading (\d+) file\(s\) to Samples\/UPLOAD$/, "Загружаю файлы в Samples/UPLOAD: $1"],
  [/^(\d+) cell\(s\) already have a clip$/, "Ячеек с клипами: $1"],
  [/^A clip from (a Drum Rack track|a melodic track|an audio track) can only go to (a Drum Rack track|a melodic track|an audio track)$/,
    (m, a) => ({"a Drum Rack track":"Клип с дорожки Drum Rack кладётся только на дорожку Drum Rack","a melodic track":"Клип с мелодической дорожки кладётся только на мелодическую дорожку","an audio track":"Клип с аудиодорожки кладётся только на аудиодорожку"})[a]],
  [/^Restore the project to (.+)\? The current version is saved to History first\.(.*)$/s, "Вернуть проект к версии $1? Текущая версия сначала сохранится в истории.$2"],
  [/^Restored to (.+?)(\..*)?$/s, "Возвращено к версии $1$2"],
  [/^Restoring (.+)…$/, "Возвращаю $1…"],
  [/^before: (.+)$/, "перед: $1"],
  [/^Restore of (.+)$/, "Откат к $1"],
  [/^Clip moved T(\d+) S(\d+) → T(\d+) S(\d+)$/, "Клип перенесён Д$1 С$2 → Д$3 С$4"],
  [/^Clip copied T(\d+) S(\d+) → T(\d+) S(\d+)$/, "Клип скопирован Д$1 С$2 → Д$3 С$4"],
  [/^Clips swapped T(\d+) S(\d+) ↔ T(\d+) S(\d+)$/, "Клипы поменялись Д$1 С$2 ↔ Д$3 С$4"],
  [/^Clip deleted T(\d+) S(\d+)$/, "Клип удалён Д$1 С$2"],
  [/^Clip loaded from file T(\d+) S(\d+)$/, "Клип загружен из файла Д$1 С$2"],
  [/^Pattern generated T(\d+) S(\d+)$/, "Рисунок сгенерирован Д$1 С$2"],
  [/^Key changed to (.+)$/, "Тональность изменена на $1"],
  [/^Tempo changed to (.+) bpm$/, "Темп изменён на $1 bpm"],
  [/^Report saved: (.+) \(on your Desktop\)\. Send this file to the author\.$/, "Отчёт сохранён: $1 (на Рабочем столе). Отправьте этот файл the author."],
  [/^Report saved: (.+) \((.+)\)\. Send this file to the author\.$/, "Отчёт сохранён: $1 ($2). Отправьте этот файл the author."],
  [/^Audio inputs found: (\d+)\. Pick one in the list$/, "Найдено аудиовходов: $1. Выберите нужный в списке"],
  [/^Monitoring: (.+)\. Use headphones to avoid feedback$/, "Слушаю: $1. Наденьте наушники, чтобы не было завязки"],
  [/^No access to the audio input: (.+)$/, "Нет доступа к аудиовходу: $1"],
  [/^Saving a copy of “(.+)” before deleting…$/, "Сохраняю копию «$1» перед удалением…"],
  [/^Saving a copy of "(.+)" before deleting…$/, "Сохраняю копию «$1» перед удалением…"],
  [/^"(.+)" deleted from Move\. A copy is in the "_Deleted" folder on the computer(?:: (.+))?$/, (m, a, b) => `«${a}» удалён с Move. Копия — в папке «_Deleted» на компьютере${b ? ": " + b : ""}`],
  [/^Delete "(.+)" from Move\? A copy is saved first to the "_Deleted" folder on the computer\.$/, "Удалить «$1» с Move? Сначала сохранится копия в папке «_Deleted» на компьютере."],
  [/^Pad (\d+) holds "(.+)"\. Delete it from Move and put "(.+)" in its place\? A copy of "(.+)" is saved first to the "_Deleted" folder on the computer\.$/,
    "На пэде $1 стоит «$2». Удалить его с Move и поставить на его место «$3»? Сначала сохранится копия «$4» в папке «_Deleted» на компьютере."],
  [/^"(.+)" is already on the computer\. Update the project and its audio\? Description and notes are kept\.$/, "«$1» уже есть на компьютере. Обновить проект и его звук? Описание и заметки сохранятся."],
  [/^Move already has a project "(.+)"\. Upload another one with the same name\?$/, "На Move уже есть проект «$1». Загрузить ещё один с тем же именем?"],
  [/^"(.+)" uploaded to Move(.*)$/s, "«$1» загружен на Move$2"],
  [/^Copying "(.+)" to the computer…$/, "Копирую «$1» на компьютер…"],
  [/^"(.+)" saved on the computer(.*)$/s, "«$1» сохранён на компьютере$2"],
  [/^Copying to Move: (\d+)\/(\d+)$/, "Копирую на Move: $1/$2"],
  [/^Copying to the computer: (\d+)\/(\d+)$/, "Копирую на компьютер: $1/$2"],
  [/^Library on Move read again: (\d+) files$/, "Библиотека на Move прочитана заново: файлов $1"],
  [/^Folder read again: (\d+) files$/, "Папка прочитана заново: файлов $1"],
  [/^Search in (.+)$/, "Поиск в $1"],
  [/^Could not save a version to History, nothing was changed: (.+)$/s, "Не удалось сохранить версию в истории, ничего не изменено: $1"],
  [/^Could not save a copy of "(.+)" before deleting it from Move, so nothing was deleted: (.+)$/s, "Не удалось сохранить копию «$1» перед удалением с Move, поэтому ничего не удалено: $2"],
  [/^"(.+)": convert it to WAV first — Move plays only WAV and AIFF in clips$/, "«$1»: сначала переведите в WAV — Move играет в клипах только WAV и AIFF"],
  [/^"(.+)" is not a readable WAV, AIFF, FLAC or MP3 file$/, "«$1» — не читаемый файл WAV, AIFF, FLAC или MP3"],
  [/^"(.+)": only WAV, AIFF, FLAC and MP3 files can be added as loops$/, "«$1»: как лупы можно добавить только WAV, AIFF, FLAC и MP3"],
  [/^"(.+)" could not be converted to WAV$/, "«$1» не удалось перевести в WAV"],
  [/^"(.+)" is empty$/, "«$1» пустой"],
  [/^"(.+)" does not look like a Move project \(\.ablbundle\)$/, "«$1» не похож на проект Move (.ablbundle)"],
  [/^Upload of "(.+)" failed \((.+)\)\. The project was not changed\. Already in Samples\/UPLOAD: (.*)$/s, "Загрузка «$1» не удалась ($2). Проект не изменён. Уже в Samples/UPLOAD: $3"],
  [/^(.+)\. The project was not changed\. Already in Samples\/UPLOAD: (.*)$/s, "$1. Проект не изменён. Уже в Samples/UPLOAD: $2"],
  [/^Invalid track order: the project has (\d+) tracks$/, "Неверный порядок дорожек: в проекте их $1"],
  [/^Internal error: (.+)$/s, "Внутренняя ошибка: $1"],
  [/^Nothing was changed: (.+)$/s, "Ничего не изменено: $1"],
  [/^MIDI file could not be read: (.+)$/s, "MIDI-файл не прочитан: $1"],
  [/^Still used by projects or presets: (.+)$/s, "Ещё используется проектами или пресетами: $1"],
  [/^Move answered (\d+)$/, "Move ответил $1"],
  [/^Could not (delete|rename|download the project|download the recording) \((\d+)\)(.*)$/s, (m, w, c, r) => `Не удалось ${({"delete":"удалить","rename":"переименовать","download the project":"скачать проект","download the recording":"скачать запись"})[w]} (${c})${r}`],
  [/^Move rejected the project \((\d+)\)(.*)$/s, "Move не принял проект ($1)$2"],
  [/^Can't open the folder: (.+)$/s, "Не удалось открыть папку: $1"],
  [/^Cannot use this folder: (.+)$/s, "Эту папку нельзя использовать: $1"],
  [/^Could not create SSH key: (.+)$/s, "Не удалось создать SSH-ключ: $1"],
  [/^Not found: (.+)$/s, "Не найдено: $1"],
  [/^Not a folder: (.+)$/s, "Это не папка: $1"],
  [/^Invalid file name: (.+)$/s, "Недопустимое имя файла: $1"],
  [/^SSH: (.+)$/s, "SSH: $1"],
  [/^build (\d+)$/, "сборка $1"],
  [/^(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d\d:\d\d(?::\d\d)?)$/, (m, d, mo, tm) => `${d} ${({Jan:"янв",Feb:"фев",Mar:"мар",Apr:"апр",May:"мая",Jun:"июн",Jul:"июл",Aug:"авг",Sep:"сен",Oct:"окт",Nov:"ноя",Dec:"дек"})[mo]} ${tm}`],
  [/^(\w+) — projects: (\d+)$/, "$1 — проектов: $2"],
  [/^Compatible: (.+?)(\. .*)?$/s, "Совместимые: $1$2"],
  [/^Key (\w+): (same|adjacent|relative)$/, (m, k, w) => `Тональность ${k}: ${({same:"та же",adjacent:"соседняя",relative:"параллельная"})[w]}`],
  [/^Audio track · effect: (.+?)((?: · clips: \d+)?)$/, (m, e, c) => `Аудиодорожка · эффект: ${e}${c.replace("clips:", "клипов:")}`],
  [/^on Move · pad (\d+)$/, "на Move · пэд $1"],
  [/^pad (\d+): (.+)$/, "пэд $1: $2"],
  [/^Move · (Samples|Presets)$/, (m, s) => `Move · ${s === "Samples" ? "Сэмплы" : "Пресеты"}`],
  [/^used in (\d+)$/, "используется в $1"],
  [/^Patterns: (.+)$/, "Рисунки: $1"],
  [/^([▸▾]) Ungrouped$/, "$1 Без группы"],
  [/^(\d+) of (\d+) used$/, "$1 из $2 используются"],
  [/^empty$/, "пусто"],
  [/^(\d+) projects on Move · 32 pads$/, "Проектов на Move: $1 · 32 пэда"]
],
fragments: [
  // куски составных сообщений: подставляются внутри строки, кроме текста в кавычках
  ["Leave the project on Move and open it again to see the changes", "Выйдите из проекта на Move и откройте его снова, чтобы увидеть изменения"],
  ["If the project is open on Move, leave it and open it again.", "Если проект открыт на Move, выйдите из него и откройте снова."],
  ["The project on Move is backed up first.", "Перед этим проект на Move сохраняется в истории."],
  ["The view was refreshed.", "Вид обновлён."],
  ["Not added (no more cells)", "Не добавлены (нет ячеек)"], ["Skipped (not WAV/AIFF/FLAC/MP3)", "Пропущены (не WAV/AIFF/FLAC/MP3)"],
  ["Leave these projects on Move first — Move saves an open project on its own and would put the old sample paths back.", "Сначала выйдите из этих проектов на Move — Move сам сохраняет открытый проект и вернёт старые пути сэмплов."],
  ["A backup of every changed file is saved on the computer first.", "Копия каждого изменённого файла сначала сохраняется на компьютере."],
  ["References will be rewritten in:", "Ссылки будут переписаны в:"],
  ["They will be missing in the project. Restore anyway?", "В проекте их не будет. Всё равно вернуть?"],
  ["Changes written to the project on Move.", "Изменения записаны в проект на Move."],
  ["Project replaced with the edited version", "Проект заменён исправленной версией"],
  ["Changes saved in the project on the computer", "Изменения сохранены в проекте на компьютере"],
  ["Schwung state copied", "состояние Schwung скопировано"], ["Schwung state restored", "состояние Schwung восстановлено"],
  ["Schwung state not restored", "состояние Schwung не восстановлено"], ["enable pad control (SSH)", "включите управление пэдами (SSH)"],
  ["the new set could not be identified", "новый проект не удалось опознать"],
  ["older backup", "старая копия"], ["The project was not changed.", "Проект не изменён."],
  ["clips:", "клипов:"], ["samples:", "сэмплов:"]
]
}};

/* ───────── механика ───────── */
let LANG = (() => {
  try{ const s = localStorage.getItem("mm-lang"); if(s && (s === "en" || I18N[s])) return s; }catch(e){}
  return /^ru\b/i.test(navigator.language || "") ? "ru" : "en";
})();
document.documentElement.lang = LANG;

function _escRe(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
let _frag = null;
function _fragments(){
  if(_frag) return _frag;
  const d = I18N[LANG]; if(!d) return (_frag = []);
  const auto = Object.entries(d.exact).filter(([en]) => en.length >= 18 && /\s/.test(en));
  _frag = (d.fragments || []).concat(auto).slice().sort((a, b) => b[0].length - a[0].length)
    .map(([en, tr]) => [new RegExp("(^|[^A-Za-z])" + _escRe(en) + "(?![A-Za-z])", "g"), tr]);
  return _frag;
}
/* текст в кавычках — имена проектов и файлов — не трогаем */
function _outsideQuotes(s, fn){
  return s.split(/(“[^”]*”|«[^»]*»|"[^"]*")/).map((p, i) => i % 2 ? p : fn(p)).join("");
}
function tr(s){
  if(LANG === "en" || typeof s !== "string" || !s) return s;
  const d = I18N[LANG]; if(!d) return s;
  const m = s.match(/^(\s*)([\s\S]*?)(\s*)$/), core = m[2];
  if(!core || !/[A-Za-z]/.test(core)) return s;
  let out = d.exact[core];
  if(out === undefined){
    out = null;
    for(const [re, rep] of d.patterns){ re.lastIndex = 0; if(re.test(core)){ re.lastIndex = 0; out = core.replace(re, rep); break; } }
    if(out === null) out = core;
    out = _outsideQuotes(out, part => {
      const ex = d.exact[part.trim()]; if(ex !== undefined && part.trim()) return part.replace(part.trim(), ex);
      let p = part; for(const [re, t] of _fragments()) p = p.replace(re, (x, pre) => pre + t); return p;
    });
  }
  return m[1] + out + m[3];
}
function t(s, vars){ let r = tr(s); if(vars) r = r.replace(/\{(\w+)\}/g, (x, k) => k in vars ? vars[k] : x); return r; }

const _ATTRS = ["title", "placeholder", "aria-label"];
const _seen = new WeakMap();                 // узел/атрибут → уже переведённое значение (чтобы не переводить повторно)
/* данные человека — имена проектов, файлов, пресетов, групп — не переводятся */
const _DATA = '[translate="no"], script, style, textarea, code, .tile .name, .nm, .rn, .ulname, .sub, .trk .t, ' +
              '.ghead:not([data-g=""]) > span:first-child, .sugg button, #nameIn, option[value^="g:"]';
function _skip(el){ return !el || !!el.closest?.(_DATA); }
function _textNode(n){
  if(_skip(n.parentElement)) return;
  const v = n.nodeValue; if(_seen.get(n) === v) return;
  const r = tr(v); _seen.set(n, r); if(r !== v) n.nodeValue = r;
}
function _attrs(el){
  if(_skip(el)) return;
  for(const a of _ATTRS){
    const v = el.getAttribute?.(a); if(!v) continue;
    const key = "a:" + a, memo = _seen.get(el) || {}; if(memo[key] === v) continue;
    const r = tr(v); memo[key] = r; _seen.set(el, memo); if(r !== v) el.setAttribute(a, r);
  }
}
function translateTree(root){
  if(LANG === "en" || !root) return;
  if(root.nodeType === 3){ _textNode(root); return; }
  if(root.nodeType !== 1) return;
  _attrs(root);
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  let n; while((n = w.nextNode())){ if(n.nodeType === 3) _textNode(n); else _attrs(n); }
}
if(LANG !== "en"){
  const _confirm = window.confirm.bind(window), _prompt = window.prompt.bind(window), _alert = window.alert.bind(window);
  window.confirm = m => _confirm(tr(String(m)));
  window.prompt = (m, d) => _prompt(tr(String(m)), d);
  window.alert = m => _alert(tr(String(m)));
  const start = () => {
    translateTree(document.body);
    document.title = tr(document.title);
    new MutationObserver(list => {
      for(const r of list){
        if(r.type === "characterData") _textNode(r.target);
        else if(r.type === "attributes") _attrs(r.target);
        else r.addedNodes.forEach(translateTree);
      }
    }).observe(document.body, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: _ATTRS});
  };
  if(document.body) start(); else document.addEventListener("DOMContentLoaded", start);
}
function setLang(l){ try{ localStorage.setItem("mm-lang", l); }catch(e){} location.reload(); }
