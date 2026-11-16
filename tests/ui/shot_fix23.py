"""Сборка 23: счётчик пэдов, без всплывашек на пэдах, крупные факты, узкие поля тональности."""
import re, sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":900}).new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    cnt = pg.locator("#moveCount")
    n = pg.locator("#moveGrid .tile").count()
    check("счётчик Move: занято/32", cnt.inner_text().strip() == f"{n}/32")
    check("у счётчика есть пояснение", "pad" in (cnt.get_attribute("title") or ""))
    check("у пэдов нет всплывающей подсказки", pg.evaluate("[...document.querySelectorAll('#moveGrid .tile')].every(t=>!t.title)"))
    pg.locator("#libGrid .tile.row").first.click(); pg.wait_for_timeout(400)
    fs = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.facts .fact')).fontSize)")
    check("факты (тональность/темп/размер) средние: 12–14px", 12 <= fs <= 14)
    pg.locator(".facts").dblclick(); pg.wait_for_timeout(300)
    w = pg.evaluate("document.querySelector('#keyTempo').getBoundingClientRect().width")
    h = pg.evaluate("document.querySelector('#keyScale').getBoundingClientRect().height")
    check("поле темпа узкое (≤64px)", w <= 64)
    check("поля тональности низкие (≤26px)", h <= 26)
    check("вкладки Pan нет", pg.locator("[data-tab=pan]").count() == 0 and pg.locator("input[data-pan]").count() == 0)
    pg.screenshot(path="/tmp/fix23.png")
    check("нет ошибок страницы", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
