"""Сборка 43: наведение на список проектов ничего не сдвигает. После run_style_env.sh."""
import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":900}).new_page()
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    pg.evaluate("localStorage.removeItem('mm-view')")
    rows = pg.locator("#libGrid .tile.row")
    before = pg.evaluate("[document.querySelector('#libGrid').clientWidth, [...document.querySelectorAll('#libGrid .tile.row')].map(r => r.getBoundingClientRect().height)]")
    for i in range(min(rows.count(), 4)):
        rows.nth(i).hover(); pg.wait_for_timeout(100)
        after = pg.evaluate("[document.querySelector('#libGrid').clientWidth, [...document.querySelectorAll('#libGrid .tile.row')].map(r => r.getBoundingClientRect().height)]")
        check(f"строка {i}: ширина списка и высоты строк те же", after == before)
    check("место под полосу прокрутки занято заранее", pg.evaluate("getComputedStyle(document.querySelector('#libGrid')).scrollbarGutter").startswith("stable"))
    b.close()
sys.exit(0 if ok else 1)
