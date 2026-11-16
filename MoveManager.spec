# Сборка «Move Manager» для Windows (.exe) и Mac (.app): pyinstaller MoveManager.spec
import sys

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    datas=[("static", "static"), ("patterns", "patterns")],
    excludes=["tests", "pytest", "numpy", "matplotlib"],
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Move Manager", console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="Move Manager")
    app = BUNDLE(coll, name="Move Manager.app", bundle_identifier="com.krjuka.movemanager",
                 info_plist={"NSHighResolutionCapable": True, "LSMinimumSystemVersion": "11.0",
                             "CFBundleShortVersionString": "1.0"})
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="Move Manager", console=False, upx=False)
