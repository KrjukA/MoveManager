/* Языки интерфейса (сборка 56). Английский текст — ключ: в коде строки английские, здесь — переводы.
   Переводчик сам следит за страницей (MutationObserver): тексты, title/placeholder/aria-label, confirm/prompt.
   Нет перевода — остаётся английский. Данные (имена проектов, Samples, Presets) помечены translate="no"
   и не трогаются; в составных сообщениях не переводится текст в кавычках “…” "…" «…».
   Добавить язык = добавить ещё один словарь в I18N и кнопку. */
"use strict";
const I18N = {ru: {
exact: {
  "Save the changes (tracks, key, tempo) into the project": "Записать изменения (треки, тональность, темп) в проект",
  "Not saved yet": "Ещё не сохранено",
  "Copying on Move": "Копирую на Move",
  "The copy was uploaded but could not be identified": "Копия загружена, но её не удалось опознать",
  "Drag the pad onto another pad to move the project; hold ⌥ Option (Alt on Windows) while dropping to make a copy.":
    "Перетащите пэд на другой пэд, чтобы перенести проект; удерживайте ⌥ Option (Alt на Windows), когда отпускаете, — получится копия.",
  "Camelot code: pick one and the root and scale follow": "Код Камелота: выберите — тоника и лад подставятся сами",
  "Camelot code": "Код Камелота",
  "Pick a Camelot code — root and scale follow it (A — minor, B — major). Or set root and scale directly. They set the pad layout; recorded notes stay where they are. ≈ means the scale is neither major nor minor.":
    "Выберите код Камелота — тоника и лад подставятся сами (A — минор, B — мажор). Или задайте тонику и лад напрямую. Они определяют раскладку пэдов; записанные ноты остаются на месте. ≈ — лад не мажор и не минор.",
  "Duplicate": "Дублировать",
  "Replace it with the copy from Move, or keep it and add a duplicate? The replaced version is saved to History.":
    "Заменить его копией с Move или оставить и добавить дубликат? Заменённая версия сохранится в истории.",
  "Support the project — opens Ko-fi in your browser": "Поддержать проект — откроется Ko-fi в браузере",
  "Send report": "Отправить отчёт", "Sending…": "Отправляю…", "Send error reports automatically": "Отправлять отчёты об ошибках автоматически",
  "Report sent to the developer. Thank you!": "Отчёт отправлен разработчику. Спасибо!",
  "Send error reports to the developer automatically?": "Отправлять отчёты об ошибках разработчику автоматически?",
  "When something goes wrong, the app sends a short report: version, system and the error. No passwords, keys or Move sign-in. You can turn this off in Report.":
    "Когда что-то пойдёт не так, программа отправит короткий отчёт: версию, систему и ошибку. Без паролей, ключей и входа на Move. Выключить можно в окне Report.",
  "Send automatically": "Отправлять", "Don't send": "Не отправлять",
  "Where should projects from Move go on this computer?": "Куда складывать проекты с Move на этом компьютере?",
  "Use this folder": "Оставить эту папку", "Choose folder…": "Выбрать папку…",
  "Replace": "Заменить", "Update": "Обновить", "Upload": "Загрузить", "Rearrange": "Расставить", "Move here": "Перенести",
  "Restore without the missing samples?": "Вернуть без недостающих сэмплов?",
  "The project on Move is backed up first.": "Сначала сохраняется копия проекта на Move.",
  "The generated pattern goes in its place.": "На его место встанет сгенерированный Pattern.",
  "The project and its audio are replaced; description and notes are kept.": "Проект и его звук заменятся; описание и заметки останутся.",
  "The projects move to the _Deleted folder.": "Проекты переедут в папку _Deleted.",
  "Move already has a project with this name.": "На Move уже есть проект с таким именем.",
  "They move to the _Deleted folder.": "Они переедут в папку _Deleted.",
  "A copy is saved first to the _Deleted folder on the computer.": "Сначала копия сохранится в папке _Deleted на компьютере.",
  "The project moves to the _Deleted folder.": "Проект переедет в папку _Deleted.",
  "The old version is deleted and the project lands on another pad.": "Старая версия удалится, а проект встанет на другой Pad.",
  "Rearrange pads by Camelot?": "Расставить Pads по Camelot?",
  "Nothing uses it. The file is removed from the device for good.": "Им ничего не пользуется. Файл удалится с девайса навсегда.",
  "Leave these projects on Move first, or Move will save the old links back.": "Сначала выйдите из этих проектов на Move, иначе Move вернёт старые ссылки.",
  "Nothing uses it.": "Этим ничего не пользуется.",
  // шапка и разделы
  "Switch theme": "Сменить тему",
  "Show all inputs… (allow access)": "Показать все входы… (разрешить доступ)", "Input to monitor (e.g. Move over USB)": "Какой вход слушать (например, Move по USB)",
  "Listen to the chosen input through the computer — independent of recording": "Слушать выбранный вход через компьютер — независимо от записи", "App build number": "Номер сборки программы", "App version": "Версия программы",
  "Something went wrong? Send a short report to the developer": "Что-то не так? Отправьте короткий отчёт разработчику",
  // колонки
  "Add .ablbundle projects that are already on this computer": "Добавить проекты .ablbundle, которые уже есть на этом компьютере",
  "Create a project group": "Создать группу проектов",
  "Click to collapse or expand": "Нажмите, чтобы свернуть или развернуть",
  "The group is removed; its projects move to Ungrouped": "Группа удаляется, её проекты переходят в «Без группы»", "New group name": "Название новой группы",
  "Looking for Move on the network…": "Ищу Move в сети…", "No projects on Move.": "На Move нет проектов.",
  "Folder is empty. Drag a project here from Move.": "Папка пуста. Перетащите сюда проект с Move.",
  "Move the notes into the new key?": "Сдвинуть ноты в новую тональность?",
  "Melodic clips and audio loops shift together. Drum Rack stays as it is.": "Мелодические Clips и Loops сдвигаются вместе. Drum Rack остаётся как есть.",
  "Don't move notes": "Не сдвигать ноты",
  "Move's SSH key has changed. This happens after a Move update.": "У Move сменился ключ SSH. Так бывает после обновления Move.",
  "Trust new key": "Доверять новому ключу", "Trust": "Доверять",
  "Trust Move's new SSH key?": "Доверять новому ключу SSH у Move?",
  "Move gets a new key after a system update or reset. Do this only if that happened to your Move.": "Move получает новый ключ после обновления системы или сброса. Нажимайте, только если с вашим Move было именно это.",
  "Could not connect to Move over SSH": "Не удалось подключиться к Move по SSH",
  "Wait: the previous clip change is still being saved": "Подождите: предыдущая правка Clip ещё сохраняется",
  "Connect it and press Refresh, or choose another folder.": "Подключите его и обновите список или выберите другую папку.",
  "move.local or 192.168.1.23": "move.local или 192.168.1.23",
  "A newer version is available — click to install it": "Вышла новая версия — нажмите, чтобы установить",
  "The app downloads it, closes, replaces itself and opens again. Your projects and settings stay.": "Программа скачает её, закроется, заменит себя и откроется снова. Проекты и настройки сохранятся.",
  "The app downloads it to your Downloads folder. Then quit this app and replace it with the new one.": "Программа скачает её в папку «Загрузки». Потом закройте программу и замените её новой.",
  "You run the app from source code. The download page opens in your browser.": "Программа запущена из исходников. Страница загрузки откроется в браузере.",
  "Install": "Установить", "Download": "Скачать", "Open page": "Открыть страницу", "Later": "Позже", "Unpacking…": "Распаковываю…",
  "The app is restarting. The new version opens in a new browser tab — you can close this one.": "Программа перезапускается. Новая версия откроется в новой вкладке — эту можно закрыть.",
  "It is in your Downloads folder. Quit this app and replace it with the new one.": "Она в папке «Загрузки». Закройте программу и замените её новой.",
  "There is no newer version for this computer": "Для этого компьютера новой версии нет",
  "The download is incomplete — try again": "Файл скачался не полностью — попробуйте ещё раз",
  "The update archive has no app inside": "В архиве обновления нет программы",
  "The app's folder name has symbols the installer can't handle — install it by hand": "В пути к программе есть символы, с которыми установка не справится, — установите вручную",
  "Connect to Move at this address": "Подключиться к Move по этому адресу", "Connect": "Подключить",
  "If Move isn't found by name, type its IP address — on Move: Settings → Wi-Fi.": "Если Move не находится по имени, введите его IP-адрес — на Move: Settings → Wi-Fi.",
  "On a Mac also allow the app in System Settings → Privacy & Security → Local Network.": "На Mac также разрешите программе доступ: Системные настройки → Конфиденциальность и безопасность → Локальная сеть.",
  "Move is unreachable. Check that it is on and on the same Wi-Fi network.": "Move недоступен. Проверьте, что он включён и в той же сети Wi-Fi.",
  "Move is unreachable. Check that it is on and on the same network.": "Move недоступен. Проверьте, что он включён и в той же сети.",
  "Enter the confirmation code from the Move screen.": "Введите код подтверждения с экрана Move.",
  "No pad": "Без Pad", "This pad is taken": "Этот Pad занят", "Projects on Move and on this computer": "Проекты на Move и на этом компьютере",
  // окна
  "Move shows a code on its screen. Enter it to connect.": "Move показывает код на экране. Введите его, чтобы подключиться.",
  "Code from the Move screen": "Код с экрана Move", "Move is not responding": "Move не отвечает",
  "Move did not show a code. Make sure it is on and not booting.": "Move не показал код. Убедитесь, что он включён и не загружается.",
  "What did you do, and what went wrong? The report goes to the developer: this text, the app version, your system and recent errors. No passwords or keys. Without internet it is saved to your Desktop.":
    "Что вы делали и что пошло не так? Отчёт уйдёт разработчику: этот текст, версия программы, система и последние ошибки. Без паролей и ключей. Без интернета он сохранится на Рабочий стол.",
  "E.g. I dragged two loops onto track 2 of “My Song” and got an error…": "Например: перетащил два Loops на Track 2 в «Моей песне» и получил ошибку…",
  "Could not save the report": "Не удалось сохранить отчёт",
  // правая панель проекта
  "Pick a project on the left or right. Drag within a pane to reorder, between panes to copy. On Move, hold ⌥ Option (Alt on Windows) while dropping to make a copy of the project.":
    "Выберите проект слева или справа. Перетаскивание внутри колонки меняет порядок, между колонками — копирует. На Move удерживайте ⌥ Option (Alt на Windows), когда отпускаете проект, — получится его копия.", "In short: what this project is": "Коротко: что это за проект",
  "Ideas, to-dos, where it was played…": "Идеи, что доделать, где играл…", "Notes saved": "Заметки сохранены",
  "Saved in meta.json in the project folder.": "Хранится в meta.json в папке проекта.",
  "Descriptions and notes for projects on Move are stored on the computer in the app's config.json, not on the device. They move into the project folder when you copy it.":
    "Описания и заметки проектов на Move хранятся на компьютере в config.json программы, а не на девайсе. При копировании они переходят в папку проекта.", "Camelot code of this key": "Код Camelot этой тональности",
  "Compatible keys light up in their wheel colour — on the wheel and as the mark on each project. Click a sector to set that key.":
    "Совместимые тональности подсвечиваются цветом колеса — на колесе и меткой на каждом проекте. Нажмите на сектор, чтобы поставить эту тональность.",
  "Double-click to change key, scale and tempo": "Двойной щелчок — изменить тональность, лад и темп",
  "Double-click to rename": "Двойной щелчок — переименовать", "Drag to reorder": "Перетащите, чтобы изменить порядок",
  "Reading project…": "Читаю проект…",
  "Leave this project on Move before sending changes — Move saves the open project on its own and would overwrite them.":
    "Выйдите из этого проекта на Move, прежде чем отправлять изменения: Move сам сохраняет открытый проект и перезапишет их.",
  "edit the project on Move in place — pad and color are kept (otherwise a \"_edit\" copy is made)": "править проект на Move на месте — Pad и цвет сохраняются (иначе создаётся копия «_edit»)",
  "replace the original — the project moves to another pad (otherwise a \"_edit\" copy is made)": "заменить оригинал — проект переедет на другой Pad (иначе создаётся копия «_edit»)",
  // Clips
  "The project has no clip cells.": "В проекте нет ячеек для Clips.",
  "Pick a cell: a filled one can be saved as .mid, any can take a .mid. The cell shows the notes; an audio cell shows the loop tempo.":
    "Выберите ячейку: заполненную можно сохранить как .mid, в любую можно загрузить .mid. В ячейке видны ноты, в аудиоячейке — темп лупа.", "Remove the clip from this cell": "Убрать Clip из этой ячейки",
  "Notes from the MIDI file become the clip in this cell": "Ноты из MIDI-файла станут Clip в этой ячейке",
  "Generate a drum pattern for this cell": "Сгенерировать барабанный Pattern для этой ячейки",
  "The generator works on Drum Rack tracks": "Генератор работает на Track с Drum Rack",
  "This is an audio track; MIDI cannot go into it": "Это audio Track, MIDI сюда не положить",
  "Import to Move needs pad control enabled": "Для загрузки на Move включите Pad control",
  "Deleting a clip on Move needs pad control enabled": "Для удаления Clip на Move включите Pad control",
  "Adding loops on Move needs pad control enabled": "Для добавления Loops на Move включите Pad control",
  "Editing clips on Move needs pad control enabled": "Для правки Clips на Move включите Pad control",
  "Restoring on Move needs pad control enabled": "Для отката на Move включите Pad control",
  "Adding loops works for projects on Move": "Loops добавляются только в проекты на Move",
  "Only notes are taken from the file; clip length is rounded up to whole bars.": "Из файла берутся только ноты; длина Clip округляется вверх до целых тактов.",
  "The project is backed up before writing.": "Перед записью сохраняется версия проекта.",
  "Several files fill the track to the right, in file-name order. Loop tempo comes from the file name (\"160bpm\"); without it the loop is fitted to whole bars, like Move does.":
    "Несколько файлов ложатся вправо по Track в порядке имён. Темп Loop берётся из имени файла («160bpm»), без него Loop подгоняется под целые такты, как это делает Move.",
  "Pick WAV, AIFF, FLAC or MP3 files: they go to Samples/UPLOAD on Move and fill this track from this cell to the right":
    "Выберите файлы WAV, AIFF, FLAC или MP3: они попадут в Samples/UPLOAD на Move и заполнят Track от этой ячейки вправо",
  "Drop loops on a cell of an audio track": "Перетащите Loops на ячейку audio Track", "Loops can only go into an audio track": "Loops можно положить только на audio Track",
  "Cell is empty": "Ячейка пуста", "Cell is occupied": "Ячейка занята", "Pick a different cell": "Выберите другую ячейку",
  "Pick a different cell to paste into": "Выберите другую ячейку для вставки", "Could not change the clips": "Не удалось изменить Clips",
  "Could not delete the clip": "Не удалось удалить Clip", "Could not save the clip": "Не удалось сохранить Clip", "Could not load the clip": "Не удалось загрузить Clip",
  "Could not write the clip": "Не удалось записать Clip", "Could not add the loops": "Не удалось добавить Loops",
  "A MIDI clip can only go into a MIDI track": "MIDI Clip можно положить только на MIDI Track",
  "Only WAV, AIFF, FLAC and MP3 files can be added as loops": "Как Loops можно добавить только файлы WAV, AIFF, FLAC и MP3",
  "The project on Move was changed on the device (Move saves an open project on its own), so this cell no longer matches. The view was refreshed — check it and try again. Leave the project on Move while editing it here.":
    "Проект на Move изменился на самом девайсе (Move сам сохраняет открытый проект), поэтому ячейка уже не совпадает. Вид обновлён — проверьте и попробуйте ещё раз. Пока правите проект здесь, выйдите из него на Move.",
  // генератор
  "Loading genres…": "Загружаю жанры…", "Could not load genres": "Не удалось загрузить жанры",
  "Read Move and the computer folder again": "Перечитать Move и папку на компьютере",
  "Copy this project from Move to the computer": "Скопировать проект с Move на компьютер",
  "Upload this project to a free pad on Move": "Загрузить проект на свободный Pad на Move",
  "Open the project folder in Finder": "Открыть папку проекта в Finder",
  "Tracks: instruments, presets, pan and order": "Треки: инструменты, пресеты, панорама и порядок",
  "Clips: copy, move, load .mid, generate drums": "Клипы: копирование, перенос, загрузка .mid, генерация барабанов",
  "Saved versions of the project — restore an earlier one": "Сохранённые версии проекта — можно вернуть прежнюю",
  "Write the track changes into the project": "Записать изменения треков в проект",
  "Save this clip as a .mid file": "Сохранить этот Clip как файл .mid",
  "Choose a folder with drum .mid files to learn from": "Выбрать папку с барабанными .mid, на которых учится генератор",
  "Record the input chosen at the top as the project audio": "Записать вход, выбранный вверху, как звук проекта",
  "Delete this project from Move; a copy is saved on the computer first": "Удалить проект с Move; сначала копия сохраняется на компьютере",
  "Move the project to the _Deleted folder": "Перенести проект в папку _Deleted",
  "Attach an audio file from the computer as the project audio": "Прикрепить аудиофайл с компьютера как звук проекта",
  "Genre: the pattern starts from drum patterns of this style": "Жанр: ритм строится из барабанных рисунков этого стиля",
  "How far the pattern moves from the reference: 0 — the reference as is, 100 — new hits from the whole genre and other pads of the kit": "Насколько ритм уходит от образца: 0 — образец как есть, 100 — новые удары из всего жанра и другие Pad набора",
  "Take another reference pattern of this genre": "Взять другой образец этого жанра",
  "Write the pattern into the selected cell": "Записать ритм в выбранную ячейку",
  "More settings: length, half time, swing, déjà vu, ghosts, euclid": "Ещё настройки: длина, Half time, Swing, Déjà vu, Ghosts, Euclid",
  "Clip length in bars": "Длина Clip в тактах",
  "Delays every second 16th note: 50 — straight, 75 — strong shuffle": "Сдвигает каждую вторую шестнадцатую: 50 — ровно, 75 — сильная раскачка",
  "How different the bars are: 0 — every bar repeats the first one, 100 — each bar is a new variation": "Насколько такты разные: 0 — все такты повторяют первый, 100 — каждый такт — новая вариация",
  "Quiet snare hits around the backbeat (snare or clap): 0 — none, 100 — many": "Тихие удары малого вокруг сильных долей (малый или клэп): 0 — нет, 100 — много",
  "Evenly spread hits on a free hat or percussion pad (euclidean rhythm): 0 — off, 100 — 10 hits per bar": "Равномерные удары на свободном Pad хэта или перкуссии (евклидов ритм): 0 — выкл., 100 — 10 ударов на такт",
  "Half time: the rhythm plays at half speed — at 140 bpm it feels like 70": "Half time: ритм идёт вдвое медленнее — при 140 bpm ощущается как 70",
  "At this Mutation the genre's patterns sound the same. Raise Mutation for new variations.": "При такой мутации Patterns жанра звучат одинаково. Поднимите мутацию для новых вариантов.",
  "Reading the project's kit…": "Читаю Kit проекта…", "Learning from MIDI folder": "Учусь на папке MIDI", "MIDI folder": "Папка MIDI",
  "Path to a folder with drum .mid files": "Путь к папке с барабанными .mid", "MIDI folder removed": "Папка MIDI отключена",
  // история
  "No saved versions yet. A version is saved before every change made here.": "Сохранённых версий пока нет. Версия сохраняется перед каждой правкой из программы.",
  "A version is saved before every change made here (up to 20). Restore puts the project back; the current version is saved first, so a restore can be undone.":
    "Перед каждой правкой из программы сохраняется версия (до 20). «Вернуть» возвращает проект к ней; текущая версия сохраняется заранее, поэтому откат можно отменить.", "Put the project back to this version": "Вернуть проект к этой версии",
  "Reading history…": "Читаю историю…", "Could not read history": "Не удалось прочитать историю", "Could not restore the version": "Не удалось вернуть версию",
  "Restoring on Move needs pad control enabled.": "Для отката на Move включите Pad control.",
  "This version is no longer in History": "Этой версии больше нет в истории", "This version is damaged and can't be restored": "Эта версия повреждена, вернуть её нельзя",
  // Pads и SSH
  "Enabling pad control…": "Включаю Pad control…",
  "Pad layout and editing a project without moving it off its pad need SSH access to Move. The app creates its own key and asks you to confirm it with the wheel on the device.":
    "Раскладка Pads и правка проекта без переноса с Pad требуют SSH-доступа к Move. Программа создаёт свой ключ и просит подтвердить его колесом на девайсе.",
  "Confirm the key with the wheel on Move": "Подтвердите ключ колесом на Move",
  "Move did not add the key. Confirm the request with the wheel on the device and try again.": "Move не добавил ключ. Подтвердите запрос колесом на девайсе и попробуйте снова.",
  "Enable pad control first": "Сначала включите Pad control", "Move did not answer over SSH": "Move не ответил по SSH",
  "Two projects cannot share one pad": "Два проекта не могут быть на одном Pad", "Pad number must be between 1 and 32": "Номер Pad — от 1 до 32",
  // Samples и Presets
  "Samples: Move library and folders on this computer": "Samples: библиотека Move и папки этого компьютера",
  "Track presets: Move library and folders on this computer": "Track Presets: библиотека Move и папки этого компьютера",
  "Left: the library on Move. Right: a folder on this computer, or a second view of Move.": "Слева — библиотека на Move. Справа — папка на этом компьютере или вторая панель Move.",
  "Reading the library on Move…": "Читаю библиотеку на Move…", "Opening the folder…": "Открываю папку…",
  "Show only files no project, preset or Schwung slot uses": "Показывать только файлы, которыми не пользуется ни проект, ни Preset, ни слот Schwung",
  "Files inside, including subfolders, that a project, preset or Schwung slot uses": "Файлы внутри (и в подпапках), которыми пользуется проект, Preset или слот Schwung",
  "Create a folder here": "Создать здесь папку", "New folder name": "Название новой папки", "New name": "Новое имя",
  "Up one folder. Drop a file here to put it one level up": "На уровень выше. Перетащите сюда файл, чтобы переложить его на уровень выше",
  "Click a file or folder for details, double-click to open or play.": "Щелчок — подробности, двойной щелчок — открыть или прослушать.",
  "Double-click to open": "Двойной щелчок — открыть", "Double-click to open. Drop here to put files into this folder.": "Двойной щелчок — открыть. Перетащите сюда файлы, чтобы положить их в эту папку.",
  "Copy into the folder open on the right": "Скопировать в папку, открытую справа", "Copy into the folder open on the left": "Скопировать в папку, открытую слева", "Pick a folder on this computer": "Выберите папку на этом компьютере", "Folders on this computer": "Папки этого компьютера", "Stop using this folder": "Не использовать эту папку", "A second view of the Move library, to move things between its folders": "Вторая панель библиотеки Move — чтобы переносить файлы между её папками",
  "Choose a folder in the Finder window…": "Выберите папку в окне Finder…", "Path to the projects folder": "Путь к папке проектов",
  "Drag between computer and Move to copy. Drag inside Move to move — every project, preset and Schwung slot that uses the file is updated, and you see the list first. Inside the computer, dragging moves the file.":
    "Перетаскивание между компьютером и Move копирует. Внутри Move — переносит: все проекты, Presets и слоты Schwung с этим файлом обновляются, список покажется заранее. Внутри компьютера перетаскивание переносит файл.",
  "Double-click the name to rename. To move, drag the file onto a folder. Either way every project, preset and Schwung slot that uses it is updated; you see the list first, and a backup of each changed file is saved on the computer.":
    "Двойной щелчок по имени — переименовать. Чтобы перенести, перетащите файл на папку. В любом случае все проекты, Presets и слоты Schwung с этим файлом обновятся; список покажется заранее, а копия каждого изменённого файла сохранится на компьютере.",
  "Drag any of them to move or copy them all. Cmd-click adds or removes one, Shift-click selects a range.": "Перетащите любой, чтобы перенести или скопировать все. Cmd-щелчок добавляет или убирает один, Shift-щелчок выделяет диапазон.",
  "Nothing found.": "Ничего не найдено.", "No unused files here.": "Здесь нет неиспользуемых файлов.", "Empty folder. Drag files here.": "Пустая папка. Перетащите сюда файлы.",
  "The file is no longer there.": "Этого файла уже нет.", "The folder is no longer there.": "Этой папки уже нет.",
  "Checking which projects use it…": "Проверяю, какие проекты им пользуются…", "Wait — the previous operation is still running": "Подождите — предыдущая операция ещё идёт",
  "The sample library on Move needs pad control enabled (SSH)": "Для библиотеки Samples на Move включите Pad control (SSH)",
  "Copying to and from Move needs pad control enabled (SSH)": "Для копирования с Move и на Move включите Pad control (SSH)",
  "Moving files": "Переношу файлы", "Updating references": "Обновляю ссылки", "Reading affected files": "Читаю затронутые файлы", "Rolling back": "Откатываю",
  "Nothing to move": "Нечего переносить", "A folder can't be moved into itself": "Папку нельзя перенести саму в себя",
  "The section folder itself can't be deleted": "Саму папку раздела удалить нельзя", "This folder can't be renamed here": "Эту папку здесь переименовать нельзя",
  "Move has no find/stat commands, so the library can't be read safely": "На Move нет команд find/stat, поэтому библиотеку нельзя прочитать безопасно",
  "Supported: WAV, AIFF, FLAC, MP3 (and presets)": "Поддерживаются WAV, AIFF, FLAC, MP3 (и Presets)",
  "Supported files: WAV, MP3, M4A, WebM and OGG": "Поддерживаются WAV, MP3, M4A, WebM и OGG",
  "This folder is outside your home folder and external drives": "Эта папка вне домашней папки и внешних дисков",
  "The system folder picker isn't available on this system — type the path": "Системное окно выбора папки недоступно — введите путь",
  // запись и звук
  "Recording cancelled": "Запись отменена",
  "Recording saved as project audio": "Запись сохранена как звук проекта", "Project audio updated": "Звук проекта обновлён",
  "File attached as project audio": "Файл прикреплён как звук проекта", "Could not save the audio": "Не удалось сохранить звук", "Could not play": "Не удалось воспроизвести", "Audio export skipped": "Экспорт звука пропущен",
  "Stop waiting for the export: the project stays without audio": "Не ждать экспорт: проект останется без звука",
  "Move reported that the export failed": "Move сообщил, что экспорт не удался", "Move started the export but stopped responding": "Move начал экспорт и перестал отвечать",
  "Move did not return an audio link": "Move не дал ссылку на звук", "Move is building the file": "Move собирает файл", "Waiting in the export queue": "Жду в очереди экспорта",
  "To choose an audio input, allow microphone access for this page (the browser asks once)": "Чтобы выбрать аудиовход, разрешите этой странице доступ к микрофону (браузер спросит один раз)",
  "No other audio inputs found": "Других аудиовходов не найдено",
  // общие и сервер
  "Working…": "Выполняю…", "Reading…": "Читаю…", "Applying changes…": "Применяю изменения…", "Something went wrong": "Что-то пошло не так",
  "Did not work": "Не получилось",
  "Reading project on Move": "Читаю проект на Move", "Writing changes": "Записываю изменения", "Writing clip": "Записываю Clip", "Writing clips": "Записываю Clips",
  "Removing clip": "Убираю Clip", "Downloading project": "Скачиваю проект", "Uploading to Move": "Загружаю на Move", "Looking for the project's samples on Move": "Ищу сэмплы проекта на Move", "Applying changes": "Применяю изменения",
  "Replacing the original": "Заменяю оригинал", "Saving a copy of the original": "Сохраняю копию оригинала", "Saving a copy of the previous project": "Сохраняю копию прежнего проекта",
  "Saving a copy to the computer before deleting": "Сохраняю копию на компьютер перед удалением", "Deleting from Move": "Удаляю с Move",
  "Removing the previous project from the pad": "Убираю прежний проект с Pad", "Copying Schwung state": "Копирую состояние Schwung",
  "Restoring Schwung state": "Восстанавливаю состояние Schwung", "Downloading recording from Move": "Скачиваю запись с Move", "Preparing key": "Готовлю ключ",
  "Checking connection": "Проверяю подключение", "Checking": "Проверяю", "Project saved": "Проект сохранён", "Writing the saved version": "Записываю сохранённую версию",
  "Waiting for another edit of this project to finish": "Жду окончания другой правки этого проекта",
  "Invalid request": "Неверный запрос", "Invalid identifier": "Неверный идентификатор", "Invalid name": "Недопустимое имя", "Empty name": "Пустое имя",
  "Invalid file name": "Недопустимое имя файла", "Invalid path": "Неверный путь", "Invalid key": "Неверная тональность", "Invalid tempo": "Неверный темп",
  "Tempo must be between 40 and 300 bpm": "Темп — от 40 до 300 bpm", "Invalid track number": "Неверный номер Track", "Invalid notes": "Неверные ноты",
  "Invalid clip length": "Неверная длина Clip", "Invalid kit": "Неверный набор", "Invalid recording name": "Неверное имя записи",
  "No cell given": "Не указана ячейка", "No cells given": "Не указаны ячейки", "No files given": "Нет файлов", "No such track in the project": "В проекте нет такого Track",
  "No such scene in the project": "В проекте нет такой Scene", "Unknown clip operation": "Неизвестное действие с Clip", "Unknown library section": "Неизвестный раздел библиотеки",
  "The file is too large": "Файл слишком большой", "The file is empty": "Файл пустой", "Not a file": "Это не файл", "Song.abl not found in the bundle": "В файле проекта нет Song.abl",
  "No .ablbundle in the project folder": "В папке проекта нет .ablbundle", "Project not found in the folder": "Проект не найден в папке", "Project not found on Move": "Проект не найден на Move",
  "A project with this name already exists in the folder": "Проект с таким именем уже есть в папке", "MIDI folder not found": "Папка MIDI не найдена",
  "This track has no Drum Rack": "На этом Track нет Drum Rack", "Unsafe Schwung archive": "Небезопасный архив Schwung",
  "The project to replace is no longer on Move": "Проекта, который нужно заменить, уже нет на Move",
  "This project is no longer on Move (it was replaced or deleted). The list has been refreshed.": "Этого проекта уже нет на Move (его заменили или удалили). Список обновлён.",
  "This project is not on Move now. Upload it to Move and export again.": "Этого проекта сейчас нет на Move. Загрузите его на Move и повторите экспорт.",
  "The new project was uploaded but could not be identified — the old one was kept": "Новый проект загружен, но его не удалось опознать — старый оставлен",
  "The new version was uploaded but could not be identified — the original was kept": "Новая версия загружена, но её не удалось опознать — оригинал оставлен",
  "Enter Move's address like 192.168.1.23 or move.local": "Введите адрес Move, например 192.168.1.23 или move.local",
  "Audio clips can't be moved yet": "Audio Clips пока нельзя переносить",
  "Some samples of this version are gone": "Некоторых Samples этой версии уже нет",
  ".ablbundle files needed": "Нужны файлы .ablbundle",
  "No audio for this project yet.": "У этого проекта пока нет звука.", "Copy exists on the computer": "Копия есть на компьютере",
  "Move exports the project audio again": "Move заново экспортирует звук проекта",
  "Move exports the project audio; if the export fails, the longest recording of this set from Recordings is used": "Move экспортирует звук проекта; если экспорт не удался, берётся самая длинная запись этого проекта из Recordings",
  "Uses Schwung": "Использует Schwung", "Uses Schwung · Schwung state saved with the project": "Использует Schwung · состояние Schwung сохранено с проектом",
  "Uses Schwung; its state is copied when you move the project to the computer (pad control on)": "Использует Schwung; его состояние копируется при переносе проекта на компьютер (при включённом Pad control)",
  "Uses Schwung presets; no Schwung state saved": "Использует Presets из Schwung; состояние Schwung не сохранено",
  "Schwung state is saved with this project and restored when uploading to Move": "Состояние Schwung сохранено с этим проектом и восстанавливается при загрузке на Move",
  "Upload files from this computer into this folder on Move (or drag them here from Finder)": "Загрузить файлы с этого компьютера в эту папку на Move (или перетащите их сюда из Finder)",
  "Approximate: from the scale's note set": "Приблизительно: по нотам лада",
  "Approximate code: the scale is mapped to the major/minor with the same notes.": "Код приблизительный: лад сопоставлен с мажором или минором из тех же нот.",
  "⌘C copy · ⌘X cut · ⌘V paste · ⌫ delete · arrows move · drag: move, onto a clip: swap, ⌥ drag: copy": "⌘C копировать · ⌘X вырезать · ⌘V вставить · ⌫ удалить · стрелки — перемещение · перетащить: перенос, на Clip — обмен, с ⌥ — копия",
  "drop WAV, AIFF, FLAC or MP3 files on an audio track cell to add loops": "перетащите WAV, AIFF, FLAC или MP3 на ячейку audio Track, чтобы добавить Loops",
  "Esc: clear clipboard": "Esc — очистить буфер",
  "A folder with drum .mid files to learn from; its subfolders become genres": "Папка с барабанными .mid для обучения; её подпапки становятся жанрами",
  "Choose your folder with MIDI clips": "Добавьте свою папку с MIDI",
  "Add projects or choose the library folder": "Добавить проекты или выбрать папку библиотеки",
  "Add projects (.ablbundle)…": "Добавить проекты (.ablbundle)…", "New group…": "Новая группа…", "Add projects, a group, or choose the library folder": "Добавить проекты, группу или выбрать папку библиотеки", "Choose library folder…": "Выбрать папку библиотеки…",
  "Pick which folder on this computer holds your Move projects": "Выберите, в какой папке на этом компьютере лежат ваши проекты Move", "unused": "не используется", "Stop the recording first": "Сначала остановите запись", "New group name:": "Название новой группы:", "New folder name:": "Название новой папки:",
  "New name:": "Новое имя:", "Folder:": "Папка:", "Pads rearranged by Camelot": "Pads расставлены по Camelot",
  "Reading Move and the computer folder…": "Читаю Move и папку компьютера…", "A file name can't contain / or \\": "В имени файла не может быть / или \\",
  "A folder name can't contain / or \\": "В имени папки не может быть / или \\", "Could not play:": "Не удалось воспроизвести:",
  "No access to the audio input:": "Нет доступа к аудиовходу:", "Key added, but pads could not be read": "Ключ добавлен, но Pads прочитать не удалось",
  "The app was updated on disk. Restart it in Terminal: Ctrl+C, then python3 app.py again": "Программа обновилась на диске. Перезапустите её в Терминале: Ctrl+C, затем снова python3 app.py",
  "Wrong code": "Неверный код", "Job not found": "Задача не найдена", "Failed to fetch": "Программа не отвечает — она запущена?", "Load failed": "Программа не отвечает — она запущена?",
  "monitor input — use headphones": "слушать вход — в наушниках",
  "Project audio:": "Звук проекта:", "Last export failed:": "Последний экспорт не удался:", "The project must be on Move": "Проект должен быть на Move",
  "Nothing uses this file": "Этим файлом ничего не пользуется", "(MIDI folder)": "(папка MIDI)",
  "Double-click the name to rename. Drag the folder onto another folder to move it with everything inside; every project, preset and Schwung slot that uses its files is updated.":
    "Двойной щелчок по имени — переименовать. Перетащите папку на другую папку, чтобы перенести её со всем содержимым; все проекты, Presets и слоты Schwung с её файлами обновятся.",
  "No project, preset or Schwung slot uses this file — it can be deleted.": "Этим файлом не пользуется ни проект, ни Preset, ни слот Schwung — его можно удалить.",
  "Projects upload one by one in this order and fill free pads from the first. Cmd-click to add or remove projects.":
    "Проекты загружаются по одному в этом порядке и занимают свободные Pads с первого. Cmd-щелчок добавляет или убирает проект.",
  "Root and scale set the pad layout; recorded notes stay where they are. ≈ after a Camelot code means it is approximate: the scale is neither major nor minor.":
    "Тоника и лад задают раскладку Pads; записанные ноты остаются на месте. ≈ после кода Camelot значит, что он приблизительный: лад не мажор и не минор.",
  "Delete this file from Move": "Удалить этот файл с Move", "Delete this folder and everything inside from Move": "Удалить эту папку со всем содержимым с Move",
  "Something inside is used — delete works only when nothing inside is used": "Что-то внутри используется — удалить можно, только если внутри ничего не используется",
  // правая панель: кнопки и заголовки (17.11: переводить; кроме .mid и Generate)
  "on computer": "на компьютере", "on Move": "на Move", "To computer →": "На компьютер →", "← To Move": "← На Move", "with audio": "со звуком",
  "Show in File Explorer": "Показать в Проводнике", "Open the project folder in File Explorer": "Открыть папку проекта в Проводнике",
  "Choose a folder in the File Explorer window…": "Выберите папку в окне Проводника…",
  "Upload files from this computer into this folder on Move (or drag them here from File Explorer)": "Загрузить файлы с этого компьютера в эту папку на Move (или перетащите их сюда из Проводника)",
  "Empty folder. Drag files here from the other panel or from File Explorer.": "Пустая папка. Перетащите сюда файлы из другой панели или из Проводника.",
  "Show in Finder": "Показать в Finder", "Move to the Trash — you can restore it from there": "Переместить в Корзину — оттуда можно вернуть",
  "This folder can't be deleted here": "Эту папку здесь удалить нельзя", "Couldn't move it to the Recycle Bin": "Не удалось переместить в Корзину", "Delete": "Удалить", "Group": "Группа", "Description": "Описание", "Notes": "Заметки",
  "Tracks": "Треки", "Clips": "Клипы", "History": "История", "Apply changes": "Применить", "Reset": "Сбросить", "Restore": "Вернуть", "Add loops…": "Добавить Loops…", "Export from Move": "Экспорт с Move", "Record input": "Записать вход",
  "● Record input": "● Записать вход", "File…": "Файл…", "Sound": "Звук", "Project": "Проект", "Open": "Открыть",
  "Copy to computer →": "Копировать на компьютер →", "← Copy to Move": "← Копировать на Move", "Copy to Move": "Копировать на Move",
  "Name by project": "Назвать по проекту", "Used in": "Где используется", "Root": "Тоника", "Scale": "Лад", "Done": "Готово",
  "Click to jump to this place": "Нажмите, чтобы перейти к этому месту",
  "Tempo, bpm": "Темп, bpm", "▶ Play": "▶ Слушать", "❚❚ Pause": "❚❚ Пауза", "Play": "Слушать", "No audio": "Без звука",
  "● Start recording": "● Начать запись", "Start recording": "Начать запись", "■ Stop and save": "■ Остановить и сохранить", "Stop": "Стоп",
  "Cancel": "Отмена", "Clear selection": "Снять выделение", "Choose…": "Выбрать…", "Change…": "Изменить…",
  "Stop using this folder": "Не использовать эту папку", "Project group": "Группа проекта", "Audio format": "Формат звука", "Rename": "Переименовать",
  // генератор: кнопки и ручки переводятся
  "Genre": "Жанр", "Genres": "Жанры", "Bars": "Такты", "Mutation": "Мутация",
  "Another": "Ещё вариант", "Put in cell": "В ячейку", "More": "Ещё", "on this computer": "на этом компьютере", "■ Stop": "■ Стоп", "▶ Play pattern": "▶ Слушать паттерн",
  "Empty folder. Drag files here from the other panel or from Finder.": "Пустая папка. Перетащите сюда файлы из другой панели или из Finder."
},
patterns: [
  [/^Update to (\S+)$/, "Обновить до $1"],
  [/^Version (\S+) is available$/, "Вышла версия $1"],
  [/^You have (\S+)\.$/, "У вас $1."],
  [/^What's new:\n([\s\S]*)$/, "Что нового (на английском):\n$1"],
  [/^Version (\S+) is installed$/, "Версия $1 установлена"],
  [/^Version (\S+) is downloaded$/, "Версия $1 скачана"],
  [/^Downloading (\S+)…$/, "Скачиваю $1…"],
  [/^Download failed: (.+)$/s, "Не удалось скачать: $1"],
  [/^Download failed \((\d+)\)$/, "Не удалось скачать (код $1)"],
  [/^Couldn't unpack the update: (.+)$/s, "Не удалось распаковать обновление: $1"],
  [/^Move the (folder|file) “(.+)” to the (Trash|Recycle Bin)\?$/, (m, k, n, b) => `Переместить ${k==="folder" ? "папку" : "файл"} «${n}» в Корзину?`],
  [/^You can restore it from the (Trash|Recycle Bin)\.$/, "Вернуть можно будет из Корзины."],
  [/^Moved to the (Trash|Recycle Bin): (.+)$/, "Перемещено в Корзину: $2"],
  [/^Couldn't move it to the Trash: (.+)$/s, "Не удалось переместить в Корзину: $1"],
  [/^Copying "(.+)" on Move…$/, "Копирую «$1» на Move…"],
  [/^Copy created on Move: "(.+)"( · pad (\d+))?(.*)$/s, (m, n, p, pad, rest) => `Копия создана на Move: «${n}»${pad ? " · Pad " + pad : ""}${rest}`],
  [/^“(.+)” is already on the computer\.$/, "«$1» уже есть на компьютере."],
  [/^Now: (.+)\nYou can change it later: \+ at the top of the Computer column → Choose library folder…$/,
    "Сейчас: $1\nПоменять можно позже: + вверху колонки Computer → «Выбрать папку библиотеки…»"],
  [/^Folder: (\/.*|[A-Za-z]:\\.*)$/, "Папка: $1"],
  // окна-подтверждения сборки 59: первый абзац — вопрос, дальше — подробности (каждый абзац переводится отдельно)
  [/^Replace the clip in track (\d+), scene (\d+)\?$/, "Заменить Clip (Track $1, Scene $2)?"],
  [/^Restore the version from (.+)\?$/, "Вернуть версию от $1?"],
  [/^The current version is saved to History first\.( If the project is open on Move, leave it and open it again\.)?$/,
    (m, a) => "Текущая версия сначала сохранится в истории." + (a ? " Если проект открыт на Move, выйдите из него и откройте снова." : "")],
  [/^These samples of the (.+) version are no longer (on Move|in the project):\n([\s\S]*)$/,
    (m, w, where, l) => `Этих сэмплов версии от ${w} больше нет ${where === "on Move" ? "на Move" : "в проекте"}:\n${l}`],
  [/^Replace clips in track (\d+)\?$/, "Заменить Clips на Track $1?"],
  [/^Scenes with clips: ([\d, ]+)\.$/, "Занятые Scenes: $1."],
  [/^Cells with clips: (\d+)\.$/, "Занятых ячеек: $1."],
  [/^The new notes come from “(.+)”\.$/, "Новые ноты — из «$1»."],
  [/^Update “(.+)” on the computer\?$/, "Обновить «$1» на компьютере?"],
  [/^Delete group “(.+)” with its projects \((\d+)\)\?$/, "Удалить группу «$1» вместе с проектами ($2)?"],
  [/^Delete group “(.+)”\?$/, "Удалить группу «$1»?"],
  [/^Its projects \((\d+)\) are kept and move to Ungrouped\.$/, "Её проекты ($1) останутся и перейдут в «Без группы»."],
  [/^Upload another “(.+)”\?$/, "Загрузить ещё один «$1»?"],
  [/^Replace “(.+)” on pad (\d+) with “(.+)”\?$/, "Заменить «$1» на Pad $2 проектом «$3»?"],
  [/^“(.+)” is deleted from Move; a copy is saved first to the _Deleted folder on the computer\.$/,
    "«$1» удалится с Move; сначала копия сохранится в папке _Deleted на компьютере."],
  [/^Remove the selected projects \((\d+)\)\?$/, "Убрать выбранные проекты ($1)?"],
  [/^Delete “(.+)” from Move\?$/, "Удалить «$1» с Move?"],
  [/^Remove “(.+)”\?$/, "Убрать «$1»?"],
  [/^Upload only the first (\d+)\?$/, "Загрузить только первые $1?"],
  [/^Move has (\d+) free pads, (\d+) projects are selected\.$/, "На Move свободных Pads: $1, выбрано проектов: $2."],
  [/^Replace “(.+)” on Move with the edited version\?$/, "Заменить «$1» на Move исправленной версией?"],
  [/^(\d+) projects, starting from “(.+)”\.$/, "Проектов: $1, начиная с «$2»."],
  [/^Delete "(.+)" and everything inside \((\d+) files?\) from Move\?$/, "Удалить «$1» со всем содержимым (файлов: $2) с Move?"],
  [/^Delete (\d+) items \((\d+) files?\) from Move\?$/, "Удалить $1 шт. (файлов: $2) с Move?"],
  [/^Delete "(.+)" from Move\?$/, "Удалить «$1» с Move?"],
  [/^Delete (.+) from Move\?$/, "Удалить $1 с Move?"],
  [/^Nothing uses (it|them)\. Removed from the device for good\.$/,
    (m, w) => w === "it" ? "Этим ничего не пользуется. Удалится с девайса навсегда." : "Ими ничего не пользуется. Удалятся с девайса навсегда."],
  [/^Rename "(.+)" → "(.+)"\?$/, "Переименовать «$1» → «$2»?"],
  [/^Rename folder "(.+)" → "(.+)"\?(?: \((\d+) files\))?$/, (m, a, b, n) => `Переименовать папку «${a}» → «${b}»?${n ? ` (файлов: ${n})` : ""}`],
  [/^Move "(.+)" to (.+?)\?(?: \((\d+) files\))?$/, (m, a, b, n) => `Перенести «${a}» в ${b}?${n ? ` (файлов: ${n})` : ""}`],
  [/^Move (\d+) items to (.+?)\?(?: \((\d+) files\))?$/, (m, a, b, n) => `Перенести ${a} шт. в ${b}?${n ? ` (файлов: ${n})` : ""}`],
  [/^Links are updated in:\n([\s\S]*)$/, (m, l) => "Ссылки обновятся в:\n" + l.replace(/^• Schwung state$/m, "• состояние Schwung")],
  // сообщения с именами и числами (группы $1… переносятся как есть)
  [/^Clip deleted: track (\d+), scene (\d+)(.*)$/s, "Clip удалён: Track $1, Scene $2$3"],
  [/^Clip saved: (.*)$/s, "Clip сохранён: $1"],
  [/^Clip from “(.+)” loaded: track (\d+), scene (\d+)(.*)$/s, "Clip из «$1» загружен: Track $2, Scene $3$4"],
  [/^Clip from "(.+)" loaded: track (\d+), scene (\d+)(.*)$/s, "Clip из «$1» загружен: Track $2, Scene $3$4"],
  [/^(Clip copied|Clip moved|Clips swapped): track (\d+), scene (\d+) → track (\d+), scene (\d+)(.*)$/s, (m, v, a, b, c, d, rest) => `${{"Clip copied":"Clip скопирован","Clip moved":"Clip перенесён","Clips swapped":"Clips поменялись местами"}[v]}: Track ${a}, Scene ${b} → Track ${c}, Scene ${d}${rest}`],
  [/^(Copied|Cut): track (\d+), scene (\d+)\. Pick a cell and press ⌘V$/, (m, v, a, b) => `${v==="Cut"?"Вырезано":"Скопировано"}: Track ${a}, Scene ${b}. Выберите ячейку и нажмите ⌘V`],
  [/^Generated pattern written: track (\d+), scene (\d+)(.*)$/s, "Сгенерированный Pattern записан: Track $1, Scene $2$3"],
  [/^Track (\d+), scene (\d+):$/, "Track $1, Scene $2:"],
  [/^Track (\d+), scene (\d+): (\d+) notes, ([\d.]+) bars$/, "Track $1, Scene $2: нот: $3, тактов: $4"],
  [/^Track (\d+), scene (\d+): empty$/, "Track $1, Scene $2: пусто"],
  [/^Track (\d+), scene (\d+): (.+) · ([\d.]+) bars · loop ([\d.]+) bpm(.*)$/s, "Track $1, Scene $2: $3 · тактов $4 · Loop $5 bpm$6"],
  [/^Delete the clip in track (\d+), scene (\d+)\?(.*)$/s, "Удалить Clip (Track $1, Scene $2)?$3"],
  [/^The cell \(track (\d+), scene (\d+)\) already has a clip\. Replace it\?$/, "В ячейке (Track $1, Scene $2) уже есть Clip. Заменить?"],
  [/^The cell \(track (\d+), scene (\d+)\) already has a clip\. Replace it with the generated pattern\?$/, "В ячейке (Track $1, Scene $2) уже есть Clip. Заменить его сгенерированным Pattern?"],
  [/^The cell \(track (\d+), scene (\d+)\) already has a clip\. Replace it with notes from “(.+)”\?$/, "В ячейке (Track $1, Scene $2) уже есть Clip. Заменить его нотами из «$3»?"],
  [/^The cell \(track (\d+), scene (\d+)\) already has a clip\. Replace it with notes from "(.+)"\?$/, "В ячейке (Track $1, Scene $2) уже есть Clip. Заменить его нотами из «$3»?"],
  [/^Replace (\d+) clips? in track (\d+), scenes? ([\d, ]+)\?$/, (m, n, t2, s) => n === "1" ? `Заменить Clip на Track ${t2}, Scene ${s}?` : `Заменить Clips (${n} шт.) на Track ${t2}, Scene ${s}?`],
  [/^Replace (\d+) clip\(s\) in track (\d+)\?$/, "Заменить Clips ($1) на Track $2?"],
  [/^Uploading (\d+) loops?…$/, "Загружаю Loops: $1…"],
  [/^Loops added: (\d+) to track (\d+)(?:, scenes? ([\d–]+))?(.*)$/s, (m, n, t2, s, rest) => `Добавлено Loops: ${n} на Track ${t2}${s ? (s.includes("–") ? `, Scene ${s}` : `, Scene ${s}`) : ""}${rest}`],
  [/^Loop added T(\d+) S(\d+)$/, "Loop добавлен: Track $1, Scene $2"],
  [/^Loops added T(\d+) S(\d+)–S(\d+)$/, "Loops добавлены: Track $1, Scene $2–$3"],
  [/^Uploading (\d+) file\(s\) to Samples\/UPLOAD$/, "Загружаю файлы в Samples/UPLOAD: $1"],
  [/^(\d+) cell\(s\) already have a clip$/, "Уже заняты ячеек: $1"],
  [/^A clip from (a Drum Rack track|a melodic track|an audio track) can only go to (a Drum Rack track|a melodic track|an audio track)$/,
    (m, a) => ({"a Drum Rack track":"Clip с Drum Rack Track можно положить только на Drum Rack Track","a melodic track":"Clip с melodic Track можно положить только на melodic Track","an audio track":"Clip с audio Track можно положить только на audio Track"})[a]],
  [/^Restore the project to (.+)\? The current version is saved to History first\.(.*)$/s, "Вернуть проект к версии $1? Текущая версия сначала сохранится в истории.$2"],
  [/^Restored to (\d{1,2} \w{3} [\d:]+)(.*)$/s, (m, w, rest) => "Проект возвращён к версии " + tr(w) + rest],
  [/^Restoring (.+)…$/, "Возвращаю $1…"],
  [/^before: (.+)$/, (m, a) => "до: " + tr(a)],
  [/^Restore of (.+)$/, (m, a) => "Откат к версии " + tr(a)],
  [/^Clip moved T(\d+) S(\d+) → T(\d+) S(\d+)$/, "Clip перенесён: Track $1, Scene $2 → Track $3, Scene $4"],
  [/^Clip copied T(\d+) S(\d+) → T(\d+) S(\d+)$/, "Clip скопирован: Track $1, Scene $2 → Track $3, Scene $4"],
  [/^Clips swapped T(\d+) S(\d+) ↔ T(\d+) S(\d+)$/, "Clips поменялись: Track $1, Scene $2 ↔ Track $3, Scene $4"],
  [/^Clip deleted T(\d+) S(\d+)$/, "Clip удалён: Track $1, Scene $2"],
  [/^Clip loaded from file T(\d+) S(\d+)$/, "Clip загружен из файла: Track $1, Scene $2"],
  [/^Pattern generated T(\d+) S(\d+)$/, "Pattern сгенерирован: Track $1, Scene $2"],
  [/^Key changed to (.+), notes ([+-]\d+)$/, "Тональность изменена на $1, ноты $2"],
  [/^Down (\d+)$/, "Вниз на $1"], [/^Up (\d+)$/, "Вверх на $1"],
  [/^Key changed to (.+)$/, "Тональность изменена на $1"],
  [/^Tempo changed to (.+) bpm$/, "Темп изменён на $1 bpm"],
  [/^No internet — report saved: (.+) \(on your Desktop\)\. Send this file to the developer\.$/, "Нет интернета — отчёт сохранён: $1 (на Рабочем столе). Отправьте этот файл разработчику."],
  [/^No internet — report saved: (.+) \((.+)\)\. Send this file to the developer\.$/, "Нет интернета — отчёт сохранён: $1 ($2). Отправьте этот файл разработчику."],
  [/^Audio inputs found: (\d+)\. Pick one in the list$/, "Найдено аудиовходов: $1. Выберите нужный в списке"],
  [/^Monitoring: (.+)\. Use headphones to avoid feedback$/, "Слушаю: $1. Наденьте наушники, чтобы не было фидбэка"],
  [/^No access to the audio input: (.+)$/, "Нет доступа к аудиовходу: $1"],
  [/^Saving a copy of “(.+)” before deleting…$/, "Сохраняю копию «$1» перед удалением…"],
  [/^Saving a copy of "(.+)" before deleting…$/, "Сохраняю копию «$1» перед удалением…"],
  [/^"(.+)" deleted from Move\. A copy is in the "_Deleted" folder on the computer(?:: (.+))?$/, (m, a, b) => `«${a}» удалён с Move. Копия — в папке «_Deleted» на компьютере${b ? ": " + b : ""}`],
  [/^Delete "(.+)" from Move\? A copy is saved first to the "_Deleted" folder on the computer\.$/, "Удалить «$1» с Move? Сначала сохранится копия в папке «_Deleted» на компьютере."],
  [/^Pad (\d+) holds "(.+)"\. Delete it from Move and put "(.+)" in its place\? A copy of "(.+)" is saved first to the "_Deleted" folder on the computer\.$/,
    "На Pad $1 стоит «$2». Удалить его с Move и поставить на его место «$3»? Сначала сохранится копия «$4» в папке «_Deleted» на компьютере."],
  [/^"(.+)" is already on the computer\. Update the project and its audio\? Description and notes are kept\.$/, "«$1» уже есть на компьютере. Обновить проект и его звук? Описание и заметки сохранятся."],
  [/^Move already has a project "(.+)"\. Upload another one with the same name\?$/, "На Move уже есть проект «$1». Загрузить ещё один с тем же именем?"],
  [/^"(.+)" uploaded to Move(.*)$/s, "«$1» загружен на Move$2"],
  [/^Copying "(.+)" to the computer…$/, "Копирую «$1» на компьютер…"],
  [/^"(.+)" saved on the computer(.*)$/s, "«$1» сохранён на компьютере$2"],
  [/^Copying to Move: (\d+)\/(\d+)$/, "Копирую на Move: $1/$2"],
  [/^Copying to the computer: (\d+)\/(\d+)$/, "Копирую на компьютер: $1/$2"],
  [/^Library on Move read again: (\d+) files$/, "Библиотека на Move прочитана заново, файлов: $1"],
  [/^Folder read again: (\d+) files$/, "Папка прочитана заново, файлов: $1"],
  [/^Search in (.+)$/, "Поиск в $1"],
  [/^Could not save a version to History, nothing was changed: (.+)$/s, "Не удалось сохранить версию в истории, ничего не изменено: $1"],
  [/^Could not save a copy of "(.+)" before deleting it from Move, so nothing was deleted: (.+)$/s, "Не удалось сохранить копию «$1» перед удалением с Move, поэтому ничего не удалено: $2"],
  [/^"(.+)": convert it to WAV first — Move plays only WAV and AIFF in clips$/, "«$1»: сначала переведите в WAV — Move играет в клипах только WAV и AIFF"],
  [/^"(.+)" is not a readable WAV, AIFF, FLAC or MP3 file$/, "«$1» — не читаемый файл WAV, AIFF, FLAC или MP3"],
  [/^"(.+)": only WAV, AIFF, FLAC and MP3 files can be added as loops$/, "«$1»: как Loops можно добавить только WAV, AIFF, FLAC и MP3"],
  [/^"(.+)" could not be converted to WAV$/, "«$1» не удалось перевести в WAV"],
  [/^"(.+)" is empty$/, "«$1» пустой"],
  [/^"(.+)" does not look like a Move project \(\.ablbundle\)$/, "«$1» не похож на проект Move (.ablbundle)"],
  [/^Upload of "(.+)" failed \((.+)\)\. The project was not changed\. Already in Samples\/UPLOAD: (.*)$/s, "Загрузка «$1» не удалась ($2). Проект не изменён. Уже в Samples/UPLOAD: $3"],
  [/^(.+)\. The project was not changed\. Already in Samples\/UPLOAD: (.*)$/s, "$1. Проект не изменён. Уже в Samples/UPLOAD: $2"],
  [/^Invalid track order: the project has (\d+) tracks$/, "Неверный порядок дорожек: в проекте их $1"],
  [/^Internal error: (.+)$/s, "Внутренняя ошибка: $1"],
  [/^Nothing was changed: (.+)$/s, "Ничего не изменено: $1"],
  [/^MIDI file could not be read: (.+)$/s, "MIDI-файл не прочитан: $1"],
  [/^Still used by projects or presets: (.+)$/s, "Ещё используется проектами или Presets: $1"],
  [/^Move answered (\d+)$/, "Move ответил $1"],
  [/^Could not (delete|rename|download the project|download the recording) \((\d+)\)(.*)$/s, (m, w, c, r) => `Не удалось ${({"delete":"удалить","rename":"переименовать","download the project":"скачать проект","download the recording":"скачать запись"})[w]} (${c})${r}`],
  [/^Move rejected the project \((\d+)\)(.*)$/s, "Move не принял проект ($1)$2"],
  [/^Can't open the folder: (.+)$/s, "Не удалось открыть папку: $1"],
  [/^Cannot use this folder: (.+)$/s, "Эту папку нельзя использовать: $1"],
  [/^The drive “(.+)” with the projects folder is not connected$/, "Диск “$1” с папкой проектов не подключён"],
  [/^Cannot open the projects folder: (.+)$/s, "Не удаётся открыть папку проектов: $1"],
  [/^Could not create SSH key: (.+)$/s, "Не удалось создать SSH-ключ: $1"],
  [/^Not found: (.+)$/s, "Не найдено: $1"],
  [/^Not a folder: (.+)$/s, "Это не папка: $1"],
  [/^Invalid file name: (.+)$/s, "Недопустимое имя файла: $1"],
  [/^SSH: (.+)$/s, "SSH: $1"],
  [/^(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d\d:\d\d(?::\d\d)?)$/, (m, d, mo, tm) => `${d} ${({Jan:"янв",Feb:"фев",Mar:"мар",Apr:"апр",May:"мая",Jun:"июн",Jul:"июл",Aug:"авг",Sep:"сен",Oct:"окт",Nov:"ноя",Dec:"дек"})[mo]} ${tm}`],
  [/^(\w+) — projects: (\d+)$/, "$1 — проектов: $2"],
  [/^Compatible: (.+?)(\. .*)?$/s, "Совместимые: $1$2"],
  [/^Key (\w+): (same|adjacent|relative)$/, (m, k, w) => `Тональность ${k}: ${({same:"та же",adjacent:"соседняя",relative:"параллельная"})[w]}`],
  [/^Audio track · effect: (.+?)((?: · clips: \d+)?)$/, (m, e, c) => `Audio Track · эффект: ${e}${c.replace("clips:", "Clips:")}`],
  [/^on Move · pad (\d+)$/, "на Move · Pad $1"],
  [/^pad (\d+): (.+)$/, "Pad $1: $2"],
  [/^on Move · (.+)$/, "на Move · $1"], [/^Library folder: (.+)$/, "Папка библиотеки: $1"], [/^on this computer · (.+)$/, "на этом компьютере · $1"],
  [/^Copies into (.+) on Move\. Nothing on Move is overwritten: a file with the same name gets “2” added\.$/,
    "Копируется в $1 на Move. На Move ничего не перезаписывается: к файлу с таким же именем добавится «2»."],
  [/^Project audio: (.+)$/, "Звук проекта: $1"], [/^Last export failed: (.+)$/s, "Последний экспорт не удался: $1"], [/^on computer · (.+)$/, "на компьютере · $1"],
  [/^(\d+) files$/, "файлов: $1"], [/^(\d+) used$/, "используется: $1"], [/^(\d+) projects?$/, "проектов: $1"],
  [/^Reading your projects (\d+)\/(\d+)… their genres appear when done\.$/, "Читаю ваши проекты $1/$2… их жанры появятся, когда закончу."],
  [/^Loading "(.+)"…$/, "Загружаю «$1»…"], [/^Adding "(.+)"…$/, "Добавляю «$1»…"],
  [/^Move is exporting audio for "(.+)"…$/, "Move экспортирует звук «$1»…"],
  [/^Group renamed to "(.+)"$/, "Группа переименована в «$1»"], [/^Group "(.+)" deleted, projects moved to Ungrouped$/, "Группа «$1» удалена, проекты перешли в «Без группы»"],
  [/^Group "(.+)" deleted$/, "Группа «$1» удалена"], [/^Group "(.+)" created — drag projects into it$/, "Группа «$1» создана — перетащите в неё проекты"],
  [/^Uploading "(.+)" to Move…$/, "Загружаю «$1» на Move…"], [/^Downloading "(.+)" from Move…$/, "Скачиваю «$1» с Move…"],
  [/^"(.+)" moved to "_Deleted"$/, "«$1» перемещён в «_Deleted»"], [/^"(.+)" deleted from Move$/, "«$1» удалён с Move"],
  [/^Uploaded to Move: (\d+) of (\d+)$/, "Загружено на Move: $1 из $2"], [/^Uploaded to (.+): (\d+)$/, "Загружено в $1: $2"],
  [/^Input: (.+)\. Check the level and press Start recording$/, "Вход: $1. Проверьте уровень и нажмите «Начать запись»"],
  [/^● Recording \((.+)\) — (.+)$/, "● Запись ($1) — $2"], [/^Projects added: (\d+)$/, "Добавлено проектов: $1"],
  [/^Can't do that: "(.+)" already exists there or the name is not allowed$/, "Нельзя: «$1» там уже есть или имя недопустимо"],
  [/^(.+) — done(?:, (\d+) projects? updated)?$/, (m, w, n) => `${w} — готово${n ? `, обновлено проектов: ${n}` : ""}`],
  [/^Copying (.+) to Move…$/, "Копирую $1 на Move…"], [/^Copying (.+) to the computer…$/, "Копирую $1 на компьютер…"],
  [/^Copied to (.+?) on Move: (\d+) files?(?: · skipped (\d+) that aren't (presets|audio))?$/, (m, d, n, s, k) => `Скопировано в ${d} на Move: ${n}${s ? ` · пропущено ${s} (не ${k === "presets" ? "Presets" : "звук"})` : ""}`],
  [/^Copied to (.+): (\d+) files?$/, "Скопировано в $1: $2"], [/^Folder "(.+)" created$/, "Папка «$1» создана"],
  [/^Renamed to "(.+)"$/, "Переименовано в «$1»"], [/^"(.+)" is used — delete works only for things nothing uses$/, "«$1» используется — удалить можно только то, чем ничего не пользуется"],
  [/^Deleted from Move: (.+)$/, "Удалено с Move: $1"], [/^Updated (\d.*)$/, "Обновлено в $1"],
  [/^Delete group "(.+)"\? Its projects \((\d+)\) are not deleted — they move to Ungrouped\.$/, "Удалить группу «$1»? Её проекты ($2) не удаляются — они перейдут в «Без группы»."],
  [/^Delete group "(.+)" with its projects \((\d+)\)\? The projects move to the "_Deleted" subfolder\.$/, "Удалить группу «$1» вместе с проектами ($2)? Проекты переедут в подпапку «_Deleted»."],
  [/^Remove the selected projects \((\d+)\) from the folder\? They move to the "_Deleted" subfolder\.$/, "Убрать выбранные проекты ($1) из папки? Они переедут в подпапку «_Deleted»."],
  [/^Remove "(.+)" from the folder\? The project moves to the "_Deleted" subfolder\.$/, "Убрать «$1» из папки? Проект переедет в подпапку «_Deleted»."],
  [/^Move has (\d+) free pads but (\d+) projects are selected\. Upload only the first (\d+)\?$/, "На Move свободных Pads: $1, а выбрано проектов: $2. Загрузить только первые $3?"],
  [/^Rearrange (\d+) projects on Move pads by Camelot, starting from "(.+)"\?$/, "Расставить проекты ($1) на Pads Move по Camelot, начиная с «$2»?"],
  [/^Ordered by Camelot, starting from "(.+)"$/, "Упорядочено по Camelot, начиная с «$1»"],
  [/^Replace "(.+)" on Move with the edited version\? The old version is deleted and the project lands on another pad\.$/, "Заменить «$1» на Move исправленной версией? Старая версия удалится, а проект встанет на другой Pad."],
  [/^Copy created: "(.+)"$/, "Создана копия: «$1»"],
  [/^"(.+)" swapped pads$/, "Поменялись Pads: $1"], [/^"(.+)" moved to pad (\d+)$/, "«$1» перенесён на Pad $2"],
  [/^Delete "(.+)" from Move\?\n\nNothing uses it\. The file is removed from the device and can't be restored from Move\.$/s, "Удалить «$1» с Move?\n\nИм ничего не пользуется. Файл удалится с девайса, восстановить его с Move будет нельзя."],
  [/^Delete (.+) from Move\?\n\nNothing uses (it|them)\. Removed from the device; can't be restored from Move\.$/s, "Удалить $1 с Move?\n\nИми ничего не пользуется. Удалятся с девайса, восстановить с Move будет нельзя."],
  [/^These samples of the (.+) version are no longer (on Move|in the project):\n\n([\s\S]*?)\n\nThey will be missing in the project\. Restore anyway\?$/,
    (m, w, where, list) => `Этих Samples версии ${tr(w)} уже нет ${where === "on Move" ? "на Move" : "в проекте"}:\n\n${list}\n\nВ проекте их не будет. Всё равно вернуть?`],
  [/^Too many attempts, wait (\d+) s$/, "Слишком много попыток, подождите $1 с"], [/^Authorization error \((\d+)\)$/, "Ошибка входа ($1)"],
  [/^Error (\d+)$/, "Ошибка $1"],
  [/^Used in: (.+)$/s, "Где используется: $1"], [/^Used in (\d+) projects — pick the one this sample belongs to\.$/, "Используется в проектах: $1 — выберите тот, к которому относится Sample."],
  [/^(\d+) selected$/, "Выбрано: $1"], [/^Projects selected: (\d+)$/, "Выбрано проектов: $1"], [/^← To Move \((\d+)\)$/, "← На Move ($1)"],
  [/^Move · (Samples|Presets)$/, (m, s) => `Move · ${s === "Samples" ? "Samples" : "Presets"}`],
  [/^used in (\d+)$/, "в проектах: $1"],
  [/^Patterns: (.+)$/, "Patterns: $1"],
  [/^(\d+) of (\d+) used$/, "используется: $1 из $2"],
  [/^empty$/, "пусто"],
  [/^(\d+) projects on Move · 32 pads$/, "Проектов на Move: $1 · 32 Pads"]
],
fragments: [
  // куски составных сообщений: подставляются внутри строки, кроме текста в кавычках
  ["Leave the project on Move and open it again to see the changes", "Выйдите из проекта на Move и откройте его снова, чтобы увидеть изменения"],
  ["If the project is open on Move, leave it and open it again.", "Если проект открыт на Move, выйдите из него и откройте снова."],
  ["The project on Move is backed up first.", "Перед этим проект на Move сохраняется в истории."],
  ["The view was refreshed.", "Вид обновлён."],
  ["Not added (no more cells)", "Не добавлены (нет ячеек)"], ["Skipped (not WAV/AIFF/FLAC/MP3)", "Пропущены (не WAV/AIFF/FLAC/MP3)"],
  ["Leave these projects on Move first — Move saves an open project on its own and would put the old sample paths back.", "Сначала выйдите из этих проектов на Move — Move сам сохраняет открытый проект и вернёт старые пути Samples."],
  ["A backup of every changed file is saved on the computer first.", "Копия каждого изменённого файла сначала сохраняется на компьютере."],
  ["References will be rewritten in:", "Ссылки будут переписаны в:"],
  ["They will be missing in the project. Restore anyway?", "В проекте их не будет. Всё равно вернуть?"],
  ["Changes written to the project on Move.", "Изменения записаны в проект на Move."],
  ["Project replaced with the edited version", "Проект заменён исправленной версией"],
  ["Changes saved in the project on the computer", "Изменения сохранены в проекте на компьютере"],
  ["Schwung state copied", "состояние Schwung скопировано"], ["Schwung state restored", "состояние Schwung восстановлено"],
  ["Schwung state not restored", "состояние Schwung не восстановлено"], ["enable pad control (SSH)", "включите Pad control (SSH)"],
  ["the new set could not be identified", "новый проект не удалось опознать"],
  ["The project was not changed.", "Проект не изменён."],
  ["samples found in the Move library:", "сэмплы найдены в библиотеке Move:"],
  ["samples kept inside the project:", "сэмплы оставлены внутри проекта:"],
  ["clips:", "Clips:"], ["samples:", "Samples:"]
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
const _MONTHS = {Jan:"янв",Feb:"фев",Mar:"мар",Apr:"апр",May:"мая",Jun:"июн",Jul:"июл",Aug:"авг",Sep:"сен",Oct:"окт",Nov:"ноя",Dec:"дек"};
const _cache = new Map();                      // строка → перевод: страница перерисовывается часто
function tr(s){
  if(LANG === "en" || typeof s !== "string" || !s) return s;
  if(_cache.has(s)) return _cache.get(s);
  const r = _tr(s);
  if(_cache.size > 20000) _cache.clear();
  _cache.set(s, r);
  return r;
}
function _tr(s){
  const d = I18N[LANG]; if(!d) return s;
  const m = s.match(/^(\s*)([\s\S]*?)(\s*)$/), core = m[2];
  if(!core || !/[A-Za-z]/.test(core)) return s;
  let out = d.exact[core];
  if(out === undefined){
    out = null;
    for(const [re, rep] of d.patterns){ re.lastIndex = 0; if(re.test(core)){ re.lastIndex = 0; out = core.replace(re, rep); break; } }
    if(out === null && core.includes("\n\n")) return m[1] + core.split("\n\n").map(tr).join("\n\n") + m[3];   // по абзацам
    if(out === null) out = core;
    out = _outsideQuotes(out, part => {
      const ex = d.exact[part.trim()]; if(ex !== undefined && part.trim()) return part.replace(part.trim(), ex);
      let p = part;
      if(p.length > 12) for(const [re, t] of _fragments()) p = p.replace(re, (x, pre) => pre + t);
      return p.replace(/\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b/g, (x, dd, mo) => `${dd} ${_MONTHS[mo]}`);
    });
  }
  return m[1] + out + m[3];
}
function t(s, vars){ let r = tr(s); if(vars) r = r.replace(/\{(\w+)\}/g, (x, k) => k in vars ? vars[k] : x); return r; }

const _ATTRS = ["title", "placeholder", "aria-label"];
const _seen = new WeakMap();                 // узел/атрибут → уже переведённое значение (чтобы не переводить повторно)
/* данные человека — имена проектов, файлов, пресетов, групп — не переводятся */
const _DATA = '[translate="no"], script, style, textarea, code, .tile .name, .nm, .rn, .ulname, .sub, .trk .t, .trk .p, ' +
              '.ghead:not([data-g=""]) > span:first-child, .sugg button, #nameIn, option[value^="g:"], .crumb';
const _DATA_ATTR = '[translate="no"], option[value^="g:"], .crumb, .tile, .trk';   // подсказки с именами
function _skip(el){ return !el || !!el.closest?.(_DATA); }
function _skipAttr(el){ return !el || !!el.closest?.(_DATA_ATTR); }
function _textNode(n){
  if(_skip(n.parentElement)) return;
  const v = n.nodeValue; if(_seen.get(n) === v) return;
  const r = tr(v); _seen.set(n, r); if(r !== v) n.nodeValue = r;
}
function _attrs(el){
  if(_skipAttr(el)) return;
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
function setLang(l){
  if(typeof S !== "undefined" && S.rec && S.rec.state === "rec"){ const msg = l === "ru" ? "Stop the recording first" : "Сначала остановите запись";
    window.ask ? window.ask(msg, {cancel: false}) : alert(msg); return; }
  try{ localStorage.setItem("mm-lang", l); }catch(e){}
  location.reload();
}
