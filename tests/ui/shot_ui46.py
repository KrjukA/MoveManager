"""Сборка 46: шапки окон на одном уровне, панель инструментов в одну строку, выделение не оранжевое. После run_env.sh."""
import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
ORANGE = "rgb(255, 91, 0)"
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (1440, 1280):
        pg = b.new_context(viewport={"width":w,"height":900}).new_page()
        pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(1500)
        pg.evaluate("document.documentElement.dataset.theme='dark'")
        for view in ("projects", "samples"):
            pg.locator(f"[data-view={view}]").click(); pg.wait_for_timeout(1500)
            if view == "samples":
                pg.locator("[data-rkind=move]").click(); pg.wait_for_timeout(1200)
            heads = pg.evaluate("[...document.querySelectorAll('.pane-head')].map(h => [Math.round(h.getBoundingClientRect().top), Math.round(h.getBoundingClientRect().height)])")
            check(f"{w} {view}: шапки панелей одной высоты {heads}", len(set(map(tuple, heads))) == 1)
            insp = pg.evaluate("Math.round(document.querySelector('#insp').firstElementChild.getBoundingClientRect().top + document.querySelector('#insp').firstElementChild.getBoundingClientRect().height/2)")
            h2 = pg.evaluate("Math.round(document.querySelector('.pane-head h2').getBoundingClientRect().top + document.querySelector('.pane-head h2').getBoundingClientRect().height/2)")
            check(f"{w} {view}: заголовок карточки на уровне шапок ({insp} vs {h2})", abs(insp - h2) <= 3)
            if view == "samples":
                bars = pg.evaluate("[...document.querySelectorAll('.pbar')].map(b => [Math.round(b.getBoundingClientRect().top), Math.round(b.getBoundingClientRect().height)])")
                check(f"{w}: панели инструментов в одну строку и вровень {bars}", len(set(map(tuple, bars))) == 1 and bars[0][1] < 44)
        pg.locator("#moveGrid [data-ulfolder]").first.click(); pg.wait_for_timeout(300)
        sel = pg.evaluate("getComputedStyle(document.querySelector('#moveGrid .ulrow.sel')).boxShadow + '|' + getComputedStyle(document.querySelector('header [data-view].on')).borderColor")
        check(f"{w}: выделение не оранжевое ({sel})", ORANGE not in sel and "255, 91, 0" not in sel)
        pg.close()
    b.close()
sys.exit(0 if ok else 1)
