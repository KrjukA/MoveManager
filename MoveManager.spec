# Сборка «KRJUK Move Manager» для Windows (.exe) и Mac (.app): pyinstaller MoveManager.spec
import re
import sys

_src = open("app.py", encoding="utf-8").read()                      # версия и сборка — из app.py, без ручной правки
VERSION = re.search(r'^VERSION = "([^"]+)"', _src, re.M).group(1)
BUILD = re.search(r'^BUILD = "([^"]+)"', _src, re.M).group(1)

NAME = "KRJUK Move Manager"
ICON = "static/icon.png"        # PyInstaller сам переводит в .ico/.icns (нужен Pillow)

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    datas=[("static", "static"), ("patterns", "patterns")],
    excludes=["tests", "pytest", "numpy", "matplotlib"],
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=NAME, console=False, icon=ICON)
    coll = COLLECT(exe, a.binaries, a.datas, name=NAME)
    app = BUNDLE(coll, name=NAME + ".app", icon=ICON, bundle_identifier="com.krjuka.movemanager",
                 info_plist={"NSHighResolutionCapable": True, "LSMinimumSystemVersion": "11.0",
                             "CFBundleShortVersionString": VERSION, "CFBundleVersion": BUILD,
                             # macOS 15+: без этого текста просьба «Локальная сеть» непонятна, а без разрешения Move не найти
                             "NSLocalNetworkUsageDescription": "KRJUK Move Manager connects to your Ableton Move on the local network."})
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name=NAME, console=False, upx=False, icon=ICON)
