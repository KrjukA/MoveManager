# Сборка «KRJUK Move Manager» для Windows (.exe) и Mac (.app): pyinstaller MoveManager.spec
import sys

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
                             "CFBundleShortVersionString": "1.0"})
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name=NAME, console=False, upx=False, icon=ICON)
