"""Гонка прослушки: медленная загрузка сэмплов + Play/Stop/Play → играет ровно один цикл."""
import sys, time
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"]); pg = b.new_context(viewport={"width":1440,"height":1000}).new_page()
    pg.add_init_script("""const _f = window.fetch; window.fetch = (u, o) => String(u).includes('/pad?')
        ? new Promise(r => setTimeout(r, 400)).then(() => _f(u, o)) : _f(u, o);""")
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    pg.locator("#libGrid .tile.row", has_text="Demo 1").first.click(); pg.wait_for_timeout(400)
    pg.locator("[data-tab=clips]").click(); pg.wait_for_timeout(300)
    pg.locator(".clipcell[data-t='0']").nth(1).click(); pg.wait_for_timeout(300)
    pg.locator("#genOpen").click(); pg.wait_for_timeout(1500)
    pg.evaluate("GENA.log = []")
    pg.locator("#genPlay").click(); pg.wait_for_timeout(100)
    pg.locator("#genPlay").click(); pg.wait_for_timeout(50)
    mark = pg.evaluate("GENA.log.length")                # всё, что запланировано после Stop
    pg.locator("#genPlay").click(); pg.wait_for_timeout(9000)
    runs = pg.evaluate(f"[...new Set(GENA.log.slice({mark}).map(x=>x.run))]")
    starts = pg.evaluate(f"GENA.log.slice({mark}).map(x=>x.start)")
    check("циклы планирует один запуск", len(runs) == 1)
    check("начала циклов идут вперёд без повторов", all(b2 > a2 for a2, b2 in zip(starts, starts[1:])))
    # смена рисунка во время прослушки — новый звучит сразу, а не после конца цикла
    t_click = pg.evaluate("genCtx().currentTime"); end_old = pg.evaluate("GENA.loopStart")
    pg.locator("#genAnother").click(); pg.wait_for_timeout(700)
    sw = pg.evaluate("GENA.log.filter(x => x.switch)")
    check("Another во время прослушки переключает сразу", bool(sw) and sw[-1]["first"] - t_click < 0.6 and sw[-1]["first"] < end_old)
    pg.locator("#genPlay").click(); pg.wait_for_timeout(300)
    n = pg.evaluate("GENA.log.length"); pg.wait_for_timeout(2500)
    check("после стопа ничего не планируется", pg.evaluate("GENA.log.length") == n)
    b.close()
sys.exit(0 if ok else 1)
