"""Сборка 48: списки в Samples начинаются вровень, Move в Projects вровень с первой группой, одинаковые команды одного вида. После run_style_env.sh."""
import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
LOOK = "(s => { const e = document.querySelector(s); if(!e) return null; const c = getComputedStyle(e); return [c.backgroundColor, c.color, c.borderTopColor, c.fontWeight].join('|'); })"
with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in ("dark", "light"):
        pg = b.new_context(viewport={"width":1440,"height":900}).new_page()
        pg.request.get("http://127.0.0.1:8765/api/fs?mode=samples&path=/root/mmpc")
        pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(1500)
        pg.evaluate(f"document.documentElement.dataset.theme='{theme}'")
        top = pg.evaluate("[document.querySelector('#moveGrid').getBoundingClientRect().top, document.querySelector('#libGrid .gsec').getBoundingClientRect().top]")
        check(f"{theme}: Move вровень с первой группой {top}", abs(top[0] - top[1]) <= 1)
        pg.locator("#moveGrid .tile").first.click(); pg.wait_for_timeout(800)
        to_pc = pg.evaluate(LOOK + "('#actPull')"); folder = pg.evaluate(LOOK + "('#chooseFolder')"); delp = pg.evaluate(LOOK + "('#actDel')")
        pg.locator("#libGrid .tile").first.click(); pg.wait_for_timeout(800)
        to_move = pg.evaluate(LOOK + "('#actPush')"); reveal = pg.evaluate(LOOK + "('#actReveal')")
        pg.locator("[data-view=samples]").click(); pg.wait_for_timeout(1500)
        rows = pg.evaluate("[document.querySelector('#moveGrid .ulrow').getBoundingClientRect().top, document.querySelector('#libGrid .ulrow').getBoundingClientRect().top]")
        check(f"{theme}: списки слева и справа начинаются вровень {rows}", abs(rows[0] - rows[1]) <= 1)
        check(f"{theme}: Choose… как Folder…", pg.evaluate(LOOK + "('.pbar[data-panel=R] [data-act=choose]')") == folder)
        pg.locator("#moveGrid [data-ulfolder='Samples/Bounces']").dblclick(); pg.wait_for_timeout(400)
        pg.locator("#moveGrid .ulrow").first.click(); pg.wait_for_timeout(400)
        check(f"{theme}: Copy to computer как To computer", pg.evaluate(LOOK + "('#toPc')") == to_pc)
        check(f"{theme}: Delete как в Projects", pg.evaluate(LOOK + "('#ulDelete')").split('|')[1:3] == delp.split('|')[1:3])
        pg.locator(".pbar[data-panel=L] [data-act=up]").click(); pg.wait_for_timeout(300)
        pg.locator("#moveGrid [data-ulfolder='Samples/Bounces']").click(); pg.wait_for_timeout(300)
        check(f"{theme}: Copy to computer у папки как To computer", pg.evaluate(LOOK + "('#toPc')") == to_pc)
        pg.locator("#libGrid [data-pcfolder='/root/mmpc/Kits']").dblclick(); pg.wait_for_timeout(500)
        pg.locator("#libGrid [data-pcfile]").first.click(); pg.wait_for_timeout(400)
        check(f"{theme}: Copy to Move как To Move", pg.evaluate(LOOK + "('#toMove')") == to_move)
        check(f"{theme}: Show in Finder одинаково", pg.evaluate(LOOK + "('#pcReveal')") == reveal)
        pg.close()
    b.close()
sys.exit(0 if ok else 1)
