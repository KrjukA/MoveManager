"""Сборка 49: Refresh показывает, что идёт обновление; в генераторе кик внизу, строки по номеру ноты как в Ableton. После run_style_env.sh."""
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
    busy = pg.evaluate("(() => { const r = document.querySelector('#refresh'); r.click(); return [r.disabled, r.textContent]; })()")
    check(f"Refresh сразу показывает работу {busy}", busy[0] and "…" in busy[1])
    pg.wait_for_timeout(2500)
    check("потом — готово и кнопка снова доступна", pg.locator("#refresh").is_enabled() and pg.locator("#refresh").inner_text().strip() == "Refresh" and "Updated" in pg.locator("#status").inner_text())
    pg.locator("#libGrid .tile.row", has_text="Demo 1").first.click(); pg.wait_for_timeout(500)
    pg.locator("[data-tab=clips]").click(); pg.wait_for_timeout(300)
    cells = pg.locator(".clipcell[data-t='0']")
    empty = [i for i in range(cells.count()) if "on" not in (cells.nth(i).get_attribute("class") or "")]
    cells.nth(empty[0]).click(); pg.wait_for_timeout(300)
    pg.locator("#genOpen").click(); pg.wait_for_timeout(1800)
    labels = pg.evaluate("[...document.querySelectorAll('#genGrid .gl')].map(e => e.textContent)")
    notes = pg.evaluate("[...document.querySelectorAll('#genGrid .gl')].map(e => +e.dataset.note)")
    check(f"кик — нижняя строка {labels}", labels and labels[-1] == "kick")
    check(f"строки по убыванию номера ноты {notes}", notes == sorted(notes, reverse=True))
    check("нет ошибок", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
