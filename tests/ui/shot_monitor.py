import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", "--autoplay-policy=no-user-gesture-required"])
    ctx = b.new_context(viewport={"width":1440,"height":1000}); ctx.grant_permissions(["microphone"])
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    check("кнопка мониторинга в шапке, без выбора проекта", pg.locator("header #monBtn").count() == 1)
    pg.locator("#monBtn").click(); pg.wait_for_timeout(1500)
    check("мониторинг включён", pg.evaluate("!!(S.mon && S.mon.ctx && S.mon.ctx.state !== 'closed')"))
    check("выбор входа виден", pg.locator("header #monInput").is_visible())
    check("индикатор уровня рисуется", pg.evaluate("S.mon && S.mon.frames > 5"))
    check("запись не открыта", pg.evaluate("!S.rec"))
    pg.locator("#libGrid .tile.row").first.click(); pg.wait_for_timeout(500)
    check("выбор проекта не выключает мониторинг", pg.evaluate("!!S.mon"))
    pg.locator("#monBtn").click(); pg.wait_for_timeout(500)
    check("мониторинг выключается", pg.evaluate("!S.mon"))
    check("нет ошибок страницы", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
