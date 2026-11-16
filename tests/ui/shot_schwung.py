import json, os, sys, urllib.request
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
sets = json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/move/sets"))["sets"]
src = [s for s in sets if s["name"].startswith("Set 90")][0]
os.makedirs(f"/tmp/fakeschwung/{src['id']}/snapshot", exist_ok=True)
open(f"/tmp/fakeschwung/{src['id']}/slot_0.json", "w").write('{"module_id":"obxd","module_path":"/data/m/obxd"}')
other = [s for s in sets if s["name"].startswith("Set 99")][0]
os.makedirs(f"/tmp/fakeschwung/{other['id']}", exist_ok=True)
open(f"/tmp/fakeschwung/{other['id']}/slot_0.json", "w").write('{}')
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":1000}).new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    check("на Move: S у сета с модулем Schwung", pg.locator("#moveGrid .tile", has_text="Set 90").first.locator(".swb").count() == 1)
    check("на Move: без S у сета с пустыми слотами", pg.locator("#moveGrid .tile", has_text="Set 99").first.locator(".swb").count() == 0)
    pg.locator("#moveGrid .tile", has_text="Set 90").first.click(); pg.wait_for_timeout(500)
    if pg.locator("#withAudio").is_checked(): pg.locator("#withAudio").uncheck(); pg.wait_for_timeout(200)
    pg.locator("#actPull").click(); pg.wait_for_timeout(4000)
    check("на компьютер: сообщение о Schwung", "Schwung state copied" in pg.locator("footer").inner_text())
    check("файл состояния в папке проекта", os.path.exists("/tmp/mmlib/Set 90/schwung_state.tar.gz"))
    row = pg.locator("#libGrid .tile.row", has_text="Set 90").first
    check("в библиотеке отметка S", row.locator(".swb").count() == 1)
    row.click(); pg.wait_for_timeout(400)
    check("в карточке факт SCHWUNG", "SCHWUNG" in pg.locator(".facts").inner_text())
    before = set(os.listdir("/tmp/fakeschwung"))
    pg.locator("#actPush").click(); pg.wait_for_timeout(5000)
    new = set(os.listdir("/tmp/fakeschwung")) - before
    check("на Move: сообщение о восстановлении", "Schwung state restored" in pg.locator("footer").inner_text())
    check("состояние записано в папку нового сета", len(new) == 1 and os.path.exists(f"/tmp/fakeschwung/{list(new)[0]}/slot_0.json")
          and not os.path.exists(f"/tmp/fakeschwung/{list(new)[0]}/snapshot"))
    check("нет ошибок страницы", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
