"""Проверка оформления «C, гибрид» (+ тёмная тема, английский). Запуск после run_env.sh и импорта проектов."""
import re
import sys
from playwright.sync_api import sync_playwright

ok = True
STAGE = sys.argv[1] if len(sys.argv) > 1 else "light"


def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name)
    ok = ok and bool(cond)


def dark(rgb):
    r, g, b = [int(x) for x in re.findall(r"\d+", rgb)[:3]]
    return r < 40 and g < 40 and b < 40


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    errs, dialogs = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    pg.goto("http://127.0.0.1:8765")
    pg.evaluate("localStorage.removeItem('mm-theme')")
    pg.reload(); pg.wait_for_timeout(2500)
    bg = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    check("светлая: фон страницы #e2e2de", bg == "rgb(226, 226, 222)")
    n_items = pg.evaluate("fetch('/api/library').then(r=>r.json()).then(d=>d.items.length)")
    check("библиотека — строки .tile.row по числу проектов", pg.locator("#libGrid .tile.row").count() == n_items and n_items > 0)
    check("сетка Move в тёмном корпусе #262624", pg.evaluate("getComputedStyle(document.querySelector('#moveGrid')).backgroundColor") == "rgb(38, 38, 36)")
    pg.locator("#libGrid .tile.row").first.click(); pg.wait_for_timeout(400)
    check("панель дорожек тёмная", pg.locator(".trkpanel").count() == 1 and dark(pg.evaluate("getComputedStyle(document.querySelector('.trkpanel')).backgroundColor")))
    check("главная кнопка — стально-синяя", pg.evaluate("getComputedStyle(document.querySelector('button.primary')).backgroundColor") in ("rgb(47, 93, 134)", "rgb(141, 176, 214)"))
    pg.screenshot(path="/tmp/style_light.png")

    if STAGE in ("dark", "english"):
        btn = pg.locator("#themeBtn")
        check("есть переключатель темы", btn.count() == 1)
        if btn.count():
            btn.click(); pg.wait_for_timeout(300)
            check("тёмная: data-theme=dark и тёмный фон", pg.evaluate("document.documentElement.dataset.theme") == "dark"
                  and dark(pg.evaluate("getComputedStyle(document.body).backgroundColor")))
            pg.reload(); pg.wait_for_timeout(2000)
            check("тёмная тема сохранилась после перезагрузки", pg.evaluate("document.documentElement.dataset.theme") == "dark")
            pg.locator("#libGrid .tile.row").first.click(); pg.wait_for_timeout(400)
            pg.screenshot(path="/tmp/style_dark.png")
            pg.locator("#themeBtn").click(); pg.wait_for_timeout(300)
            check("снова светлая", pg.evaluate("document.documentElement.dataset.theme") != "dark"
                  and pg.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(226, 226, 222)")

    if STAGE == "english":
        pg.locator("#libGrid .tile.row").first.click(); pg.wait_for_timeout(400)
        for tab in ("tracks", "clips"):
            pg.locator(f"[data-tab={tab}]").click(); pg.wait_for_timeout(200)
            text = pg.evaluate("document.body.innerText")
            names = pg.evaluate("[...document.querySelectorAll('.tile .name')].map(e=>e.textContent)")
            for nm in names:
                text = text.replace(nm, "")
            cyr = re.findall(r"[А-Яа-яЁё][А-Яа-яЁё ]*", text)
            check(f"нет русского текста на экране (вкладка {tab})", not cyr)
            if cyr:
                print("   ", cyr[:8])
        pg.locator("#actDel").click(); pg.wait_for_timeout(200)
        check("подтверждение удаления на английском", dialogs and not re.search(r"[А-Яа-яЁё]", dialogs[-1].replace(pg.locator("#nameIn").input_value(), "")))

    check("нет ошибок страницы", not errs)
    if errs:
        print(errs)
    b.close()
sys.exit(0 if ok else 1)
