"""Сборка 62: проверка новой версии на GitHub и установка поверх старой.

Новая версия — последний релиз KrjukA/MoveManager. Архив для своей системы скачивается самой программой
(без пометки «скачано из интернета», поэтому Mac не спрашивает заново), распаковывается, а замену делает
маленький скрипт уже после выхода программы: старое приложение откладывается, новое встаёт на его место
и запускается. Не получилось заменить — старое возвращается на место.
"""
import os
import platform as _platform
import re
import shlex
import subprocess
import sys
from pathlib import Path

REPO = "KrjukA/MoveManager"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
PAGE_URL = f"https://github.com/{REPO}/releases/latest"


def vtuple(v):
    """«v1.10» → (1, 10). Нечисловые хвосты отбрасываются."""
    return tuple(int(x) for x in re.findall(r"\d+", str(v or "").split("-")[0])[:4])


def is_newer(latest, current):
    return bool(vtuple(latest)) and vtuple(latest) > vtuple(current)


def is_arm_mac(machine=None, sysctl=None):
    """Mac на Apple M: в том числе когда Intel-версия запущена через Rosetta."""
    if (machine or _platform.machine()) == "arm64":
        return True
    try:
        out = (sysctl or (lambda: subprocess.run(["sysctl", "-n", "hw.optional.arm64"], capture_output=True,
                                                 timeout=3).stdout))()
        return out.strip() == b"1"
    except Exception:  # noqa: BLE001
        return False


def asset_suffix(platform, arm):
    if platform == "darwin":
        return "-mac-apple-silicon.zip" if arm else "-mac-intel.zip"
    if platform.startswith("win"):
        return "-windows.zip"
    return None


def parse_release(data, current, suffix):
    tag = str(data.get("tag_name") or "")
    latest = tag.lstrip("vV")
    asset = None
    for a in data.get("assets") or []:
        if suffix and str(a.get("name", "")).endswith(suffix):
            asset = {"name": a["name"], "url": a.get("browser_download_url"), "size": int(a.get("size") or 0)}
            break
    notes = clean_notes(data.get("body"))
    return {"current": current, "latest": latest, "newer": is_newer(latest, current),
            "page": data.get("html_url") or PAGE_URL, "asset": asset,
            "notes": notes[:600] + ("…" if len(notes) > 600 else "")}


def clean_notes(body):
    """Что нового — простым текстом: без инструкции по установке, заголовков, цитат и разметки."""
    text = str(body or "").replace("\r", "")
    text = re.split(r"(?im)^#+\s*how to install", text)[0]
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("#") or s.startswith(">"):
            continue
        s = re.sub(r"\*\*|__|`", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
        out.append("• " + s[2:] if s.startswith(("- ", "* ")) else s)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def fetch_latest(get, current, suffix):
    r = get(API_URL, timeout=6, headers={"Accept": "application/vnd.github+json",
                                         "User-Agent": f"KRJUK-Move-Manager/{current}"})
    if r.status_code != 200:
        raise OSError(f"GitHub answered {r.status_code}")
    return parse_release(r.json(), current, suffix)


def install_target(frozen, platform, executable):
    """Что заменять: .app на Mac, .exe на Windows. Запуск из исходников или из «карантинной» копии — None."""
    if not frozen:
        return None
    exe = Path(executable)
    if platform == "darwin":
        if "AppTranslocation" in str(exe):         # Mac запустил копию из закрытой папки — заменить нельзя
            return None
        app = next((p for p in exe.parents if p.suffix == ".app"), None)
        return app if app and os.access(app.parent, os.W_OK) else None
    if platform.startswith("win"):
        return exe if exe.suffix.lower() == ".exe" and os.access(exe.parent, os.W_OK) else None
    return None


def find_new(extracted, platform):
    pat = "*.app" if platform == "darwin" else "*.exe"
    found = sorted(Path(extracted).rglob(pat), key=lambda p: len(p.parts))
    return found[0] if found else None


def mac_script(old, new, pid):
    o, n, b = shlex.quote(str(old)), shlex.quote(str(new)), shlex.quote(str(old) + ".old-update")
    return f"""#!/bin/sh
# KRJUK Move Manager: replace the app with the new version after it quits
i=0
while kill -0 {int(pid)} 2>/dev/null && [ $i -lt 100 ]; do sleep 0.3; i=$((i+1)); done
rm -rf {b}
if mv {o} {b}; then
  if mv {n} {o}; then rm -rf {b}; else mv {b} {o}; fi
fi
xattr -dr com.apple.quarantine {o} 2>/dev/null
open {o}
case "$0" in *KRJUK-update-install.sh) rm -f "$0";; esac
"""


def win_script(old, new, pid):
    for p in (old, new):
        if any(c in str(p) for c in '%"^&|<>!'):
            raise ValueError("unsafe path")
    return f"""@echo off
rem KRJUK Move Manager: replace the app with the new version after it quits
set n=0
:wait
tasklist /FI "PID eq {int(pid)}" 2>nul | find "{int(pid)}" >nul
if not errorlevel 1 (
  set /a n+=1
  if %n% gtr 60 goto run
  timeout /t 1 /nobreak >nul
  goto wait
)
set n=0
:swap
move /y "{new}" "{old}" >nul 2>&1
if errorlevel 1 (
  set /a n+=1
  if %n% gtr 20 goto run
  timeout /t 1 /nobreak >nul
  goto swap
)
:run
start "" "{old}"
del "%~f0"
"""


def launch_script(path, platform, popen=subprocess.Popen):
    """Запуск скрипта отдельно от программы: он должен пережить её выход."""
    if platform.startswith("win"):
        flags = 0x00000008 | 0x00000200 | 0x08000000      # DETACHED_PROCESS | NEW_PROCESS_GROUP | NO_WINDOW
        return popen(["cmd", "/c", str(path)], creationflags=flags, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return popen(["/bin/sh", str(path)], start_new_session=True, close_fds=True,
                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def unpack(zip_path, dest, platform, run=subprocess.run):
    """Mac — через ditto: обычная распаковка теряет права запуска и ссылки внутри .app."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    if platform == "darwin":
        r = run(["ditto", "-x", "-k", str(zip_path), str(dest)], capture_output=True, timeout=300)
        if r.returncode:
            raise OSError("Couldn't unpack the update")
    else:
        import zipfile
        with zipfile.ZipFile(zip_path) as z:
            for m in z.namelist():
                if m.startswith("/") or ".." in Path(m).parts:
                    raise OSError("Bad archive")
            z.extractall(dest)
    return dest


def current_platform():
    return sys.platform
