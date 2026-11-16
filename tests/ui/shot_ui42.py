"""Сборка 42: панели сами обновляются с Move; раздел помнится после перезагрузки; в Projects нет переключателя Computer/Move. После run_env.sh."""
import json, os, sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
SONG = "/tmp/fakeul/Sets/aaaaaaaa-0000-0000-0000-000000000001/Seed Proj/Song.abl"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":900}).new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2000)
    check("в Projects нет переключателя Computer/Move", not pg.locator("[data-rkind=pc]").is_visible())
    pg.locator("[data-view=samples]").click(); pg.wait_for_timeout(1800)
    check("в Samples переключатель есть", pg.locator("[data-rkind=pc]").is_visible())
    L = pg.locator("#moveGrid")
    L.locator("[data-ulfolder='Samples/Drums']").dblclick(); pg.wait_for_timeout(500)
    row = L.locator("[data-ulfile='Samples/Drums/old unused.wav'] .uluse")
    check("сначала не используется", row.inner_text().strip() == "unused")
    # на Move проект начал использовать сэмпл (например, его сохранили на девайсе)
    d = json.load(open(SONG)); d["extra"] = "ableton:/user-library/Samples/Drums/old%20unused.wav"
    json.dump(d, open(SONG, "w")); os.utime(SONG, (2000000000, 2000000000))
    pg.evaluate("S.pollMs = 400"); pg.wait_for_timeout(2500)
    check("статус обновился сам", "used in" in row.inner_text())
    check("без мигания «Reading…»", pg.locator("#moveGrid .hint").count() == 0)
    # новый файл появился на Move
    open("/tmp/fakeul/Samples/Drums/fresh.wav", "wb").write(b"RIFF")
    pg.evaluate("window.dispatchEvent(new Event('focus'))"); pg.wait_for_timeout(1500)
    check("новый файл виден после возврата в окно", L.locator("[data-ulfile='Samples/Drums/fresh.wav']").count() == 1)
    pg.locator("[data-view=presets]").click(); pg.wait_for_timeout(1500)
    pg.reload(); pg.wait_for_timeout(2500)
    check("после перезагрузки открывается Projects", pg.locator("header [data-view=projects].on").count() == 1 and pg.locator("#libGrid .tile").count() > 0)
    pg.locator("[data-view=projects]").click(); pg.wait_for_timeout(600)
    check("и снова Projects без переключателя", not pg.locator("[data-rkind=pc]").is_visible())
    check("нет ошибок", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
