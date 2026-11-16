import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":900}).new_page()
    pg.on("dialog", lambda d: d.accept())
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    pg.locator("#moveGrid .tile").first.click(); pg.wait_for_timeout(600)
    pg.locator("[data-tab=clips]").click(); pg.wait_for_timeout(300)
    pg.locator(".clipcell[data-t='0']").nth(1).click(); pg.wait_for_timeout(300)
    pg.locator("#genOpen").click(); pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelector('#genPut').scrollIntoView({block:'center'})"); pg.wait_for_timeout(200)
    y0 = pg.evaluate("document.querySelector('#insp').scrollTop")
    pg.evaluate("document.querySelector('#genPut').click()"); pg.wait_for_timeout(4000)
    y1 = pg.evaluate("document.querySelector('#insp').scrollTop")
    print("scroll", y0, "->", y1)
    check("Move: Put in cell не сбивает прокрутку", y0 > 50 and abs(y1 - y0) < 40)
    b.close()
sys.exit(0 if ok else 1)
