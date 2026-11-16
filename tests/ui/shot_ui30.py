import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":1000}).new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    check("в шапке нет формата и галочки аудио", pg.locator("header #fmt, header #withAudio").count() == 0)
    pg.locator("#moveGrid .tile").first.click(); pg.wait_for_timeout(600)
    acts = pg.locator("#actPull").locator("xpath=..")
    check("галочка «with audio» рядом с кнопкой переноса", acts.locator("#withAudio").count() == 1 or pg.locator("#actPull ~ label #withAudio, #pullBox #withAudio").count() == 1)
    wa = pg.locator("#withAudio")
    if not wa.is_checked(): wa.check(); pg.wait_for_timeout(300)
    check("при «with audio» виден выбор формата", pg.locator("#fmt").count() == 1 and pg.locator("#fmt").is_visible())
    pg.locator("#withAudio").uncheck(); pg.wait_for_timeout(300)
    check("без аудио формат скрыт", pg.locator("#fmt").count() == 0 or not pg.locator("#fmt").is_visible())
    pg.locator("#withAudio").check(); pg.wait_for_timeout(300)
    # тональность ↔ Камелот
    pg.locator(".facts").dblclick(); pg.wait_for_timeout(300)
    cam = pg.locator("#keyCam")
    check("рядом с тональностью — код Камелота", cam.count() == 1 and cam.inner_text().strip()[:-1].isdigit())
    before = cam.inner_text()
    pg.select_option("#keyRoot", index=(int(pg.locator("#keyRoot").input_value()) + 7) % 12); pg.wait_for_timeout(300)
    check("код Камелота меняется вместе с тоникой", pg.locator("#keyCam").inner_text() != before)
    pg.locator("svg [data-cam='5A']").click(); pg.wait_for_timeout(400)
    check("щелчок по сектору 5A ставит тональность 5A", pg.locator("#keyCam").inner_text().strip() == "5A")
    check("после щелчка можно применить", pg.locator("#applyOrder").is_enabled())
    pg.locator("#resetOrder").click(); pg.wait_for_timeout(300)
    # цвета совместимости = цвета колеса
    tiles = pg.evaluate("""[...document.querySelectorAll('.tile')].filter(t=>t.querySelector('.cbar i')).map(t=>[
        getComputedStyle(t.querySelector('.cbar i')).backgroundColor, getComputedStyle(t.querySelector('.keyb')).backgroundColor])""")
    check("метка совместимости в цвете ключа по колесу", tiles and all(a == b for a, b in tiles))
    check("легенда без отдельных цветов", "adjacent ±1" not in pg.locator("#insp").inner_text())
    check("нет ошибок страницы", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
