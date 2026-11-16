import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":1000}).new_page()
    errs, dialogs = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    answer = {"v": False}
    pg.on("dialog", lambda d: (dialogs.append(d.message), d.accept() if answer["v"] else d.dismiss()))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    for side, sel in (("lib", "#libGrid .tile.row"), ("move", "#moveGrid .tile")):
        pg.locator(sel).first.click(); pg.wait_for_timeout(600)
        pg.locator("[data-tab=clips]").click(); pg.wait_for_timeout(300)
        filled = pg.locator(".clipcell.on")
        if not filled.count():
            print("skip", side); continue
        t, s = filled.first.get_attribute("data-t"), filled.first.get_attribute("data-s")
        filled.first.click(); pg.wait_for_timeout(300)
        check(f"{side}: есть кнопка Delete clip", pg.locator("#clipDel").count() == 1)
        answer["v"] = False; pg.locator("#clipDel").click(); pg.wait_for_timeout(800)
        check(f"{side}: спрашивает подтверждение", dialogs and "Delete the clip" in dialogs[-1])
        check(f"{side}: отказ — клип на месте", "on" in pg.locator(f".clipcell[data-t='{t}'][data-s='{s}']").get_attribute("class"))
        answer["v"] = True; pg.locator("#clipDel").click(); pg.wait_for_timeout(3000)
        check(f"{side}: после удаления ячейка пуста", "on" not in pg.locator(f".clipcell[data-t='{t}'][data-s='{s}']").get_attribute("class"))
        pg.locator(f".clipcell[data-t='{t}'][data-s='{s}']").click(); pg.wait_for_timeout(300)
        check(f"{side}: у пустой ячейки кнопки нет", pg.locator("#clipDel").count() == 0)
    check("нет ошибок страницы", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
