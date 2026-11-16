"""Сборка 39: счётчик использования у папки, кнопка обновления, шапка без наложений. После run_env.sh."""
import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1226,"height":800}).new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    box = pg.evaluate("""(() => { const pane = document.querySelector('#chooseFolder').closest('.pane').getBoundingClientRect();
        return [...document.querySelectorAll('#chooseFolder,#newGroup,#importBtn')].every(el => { const r = el.getBoundingClientRect(); return r.right <= pane.right + 0.5; }); })()""")
    check("кнопки шапки не вылезают за окно", box)
    pg.locator("[data-view=samples]").click(); pg.wait_for_timeout(1500)
    chip = pg.locator("#moveGrid [data-ulfolder='Samples/Bounces'] .uluse").inner_text()
    check("у папки — сколько используется: " + chip, "1 of 2 used" in chip)
    chip2 = pg.locator("#moveGrid [data-ulfolder='Samples/Drums'] .uluse").inner_text()
    check("и у второй папки", "1 of 2 used" in chip2)
    busy = pg.evaluate("(() => { const b = document.querySelector('.pbar[data-panel=L] [data-act=reload]'); b.click(); return b.disabled && b.classList.contains('busy'); })()")
    pg.wait_for_timeout(1500)
    check("обновление видно, пока идёт", busy)
    check("после обновления — сообщение", "files" in pg.locator("#status").inner_text())
    check("кнопка снова доступна", pg.locator(".pbar[data-panel=L] [data-act=reload]").is_enabled())
    check("нет ошибок", not errs)
    b.close()
sys.exit(0 if ok else 1)
