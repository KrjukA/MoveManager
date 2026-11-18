# KRJUK Move Manager — development notes

How the app works inside, running it from source, and releasing versions. The user description is in the [README](../README.md).

The app keeps its settings, Move sign-in and SSH key in the user folder:
Windows — `%APPDATA%\KRJUK Move Manager`, Mac — `~/Library/Application Support/KRJUK Move Manager`.

## Releasing a new version

GitHub → **Releases** → **Draft a new release** → tag like `v1.4` → **Publish**.
In 10–15 minutes three archives are attached to the release automatically (the version in their names comes from `VERSION` in `app.py`).
Without a release: **Actions → Build apps → Run workflow** — the archives appear at the bottom of the run page under *Artifacts*.

## Running from source

    python3 app.py

Opens http://127.0.0.1:8765. Needs the `requests` package (`python3 -m pip install requests`).
On the first connection the app asks for the code from Move's screen and remembers the sign-in.

Tests: `PYTHONHASHSEED=0 python3 -m unittest discover -s tests` (on a Mac, install GNU tools once: `brew install coreutils findutils gnu-tar`).

## Where things are

- `app.py` — the server: talking to Move, reading `Song.abl`, the library on disk.
- `static/index.html` — the interface; `static/i18n.js` — the Russian translation.
- `config.json` — created automatically: library folder, Move sign-in, tile order, notes for projects on Move.
- `cache/` — cache of parsed projects, safe to delete.

Library: one folder per project — `Name.ablbundle`, `Name.wav` (or `.mp3`), `meta.json` with the description and notes.
Projects deleted from the library move into the `_Deleted` subfolder.

## Pads and editing a project in place (SSH)

The Enable button above the Move list creates a separate SSH key (`move_ssh_key`) and asks Move to accept it —
you confirm with the wheel on the device. After that the app:

- shows projects as a 4×8 grid like the pads on Move (pad 1 is bottom left);
- moves projects between pads (the `user.song-index` attribute of the set folder);
- changes track order and pan right in `Song.abl` on the device, keeping the pad and colour.

Before every change to a project (on Move and on the computer) the previous version is saved to History — see below.

## Clips: copy, move, swap

The **Clips** tab in the project panel (on Move and on the computer). Everything works within one project:

- `⌘C` / `⌘X` / `⌘V` — copy, cut, paste the clip of the selected cell (into a filled cell — after asking);
- `⌫` — delete the clip; arrow keys move the selection; `Esc` clears the buffer;
- drag a clip: onto an empty cell — move, onto another clip — swap, with `⌥` — copy.

A drum clip goes only to a Drum Rack track, a melodic clip only to a melodic track.
On Move this needs pad control (SSH); a backup is saved before writing.

## History and undo

The **History** tab in the project panel: versions with date, time and the action that followed
("before: Clip moved T2 S7 → T2 S8"). **Restore** brings the project back to the chosen version; the current version
is saved first, so a restore can be undone. The last 20 versions are kept.

- projects on Move — in the app folder `history/move/<set ID>/` (needs pad control — SSH);
- projects on the computer — in the hidden `.history/` folder inside the project folder.

If samples of the old version are gone, the app lists them and asks whether to restore anyway.

**Important for projects on Move:** leave the project on the device before changing it from the app. Move saves
the open project a few seconds after any action on the device and would write its own version on top.

## Loops into audio cells

For live prep: on the **Clips** tab of a project on Move, drag one or more WAV/AIFF/FLAC/MP3 files from Finder onto a cell
of an audio track (or pick a cell and click **Add loops…**). Files are uploaded to `Samples/UPLOAD/` on Move and the clips
fill the cells of that track to the right in file-name order ("2 …" before "10 …"). The loop tempo comes from the file name
("160bpm"); without it the loop is fitted to whole bars, like Move does. Move doesn't play FLAC and MP3 in clips — on a Mac
the app converts them to WAV (on Windows, convert to WAV first). A version is saved to History before writing.

## Samples when uploading a project

A computer project (`.ablbundle`) carries its own sample copies; `BundleInfo.json` → `originalSampleUris` tells Move where
each sample used to live. If a file is there, Move links to it; otherwise the copy stays inside the set. Before uploading,
the app finds each sample in the Move library by content (MD5) and rewrites these paths, so moved or renamed samples
are found and no hidden duplicate is created. A file with the same name but a different sound is never linked.

## Drum generator patterns (sources)

The generator's patterns come from the book **Pocket Operations** (Paul Wenzel, 2019, https://shittyrecording.studio/)
and the **Basic Drum Patterns** chart (8 genres). The book and the chart are not in the repository — only the patterns
parsed from them (`pocket_operations.json`, `basic_8_genres.json`). To parse the book again, download the PDF from the
author's site and run `python3 tools/parse_pocket.py <path to PDF>`.
