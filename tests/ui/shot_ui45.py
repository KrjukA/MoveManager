"""Сборка 45: открывается Projects; удаление папок, пресетов и нескольких файлов на Move. После run_env.sh."""
import os, sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":900}).new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); dialogs = []
    pg.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(1500)
    pg.locator("[data-view=presets]").click(); pg.wait_for_timeout(1200)
    pg.reload(); pg.wait_for_timeout(1500)
    check("после перезагрузки — Projects", pg.locator("header [data-view=projects].on").count() == 1)
    pg.locator("[data-view=samples]").click(); pg.wait_for_timeout(1800)
    L, I = pg.locator("#moveGrid"), pg.locator("#insp")
    L.locator("[data-ulfolder='Samples/Bounces']").click(); pg.wait_for_timeout(300)
    check("папку с используемым удалить нельзя", I.locator("#ulFDelete").is_disabled())
    os.makedirs("/tmp/fakeul/Samples/Junk/inner", exist_ok=True)
    open("/tmp/fakeul/Samples/Junk/inner/a.wav", "wb").write(b"RIFF")
    pg.locator(".pbar[data-panel=L] [data-act=reload]").click(); pg.wait_for_timeout(1500)
    L.locator("[data-ulfolder='Samples/Junk']").click(); pg.wait_for_timeout(300)
    I.locator("#ulFDelete").click(); pg.wait_for_timeout(1500)
    check("свободная папка удалена целиком", not os.path.exists("/tmp/fakeul/Samples/Junk") and "Delete" in dialogs[-1])
    L.locator("[data-ulfolder='Samples/Drums']").dblclick(); pg.wait_for_timeout(400)
    open("/tmp/fakeul/Samples/Drums/b.wav", "wb").write(b"RIFF")
    pg.locator(".pbar[data-panel=L] [data-act=reload]").click(); pg.wait_for_timeout(1500)
    L.locator("[data-ulfile='Samples/Drums/old unused.wav']").click()
    L.locator("[data-ulfile='Samples/Drums/b.wav']").click(modifiers=["Meta"]); pg.wait_for_timeout(300)
    pg.keyboard.press("Delete"); pg.wait_for_timeout(1500)
    check("несколько свободных удалены клавишей Delete", not os.path.exists("/tmp/fakeul/Samples/Drums/old unused.wav") and not os.path.exists("/tmp/fakeul/Samples/Drums/b.wav") and os.path.exists("/tmp/fakeul/Samples/Drums/kick.wav"))
    pg.locator("[data-view=presets]").click(); pg.wait_for_timeout(1500)
    L.locator("[data-ulfolder='Track Presets/Drums']").dblclick(); pg.wait_for_timeout(400)
    L.locator("[data-ulfile='Track Presets/Drums/Kit.ablpreset']").click(); pg.wait_for_timeout(300)
    I.locator("#ulDelete").click(); pg.wait_for_timeout(1500)
    check("пресет удалён", not os.path.exists("/tmp/fakeul/Track Presets/Drums/Kit.ablpreset"))
    check("нет ошибок", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
