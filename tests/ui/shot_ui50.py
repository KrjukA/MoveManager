"""Сборка 50: название KRJUK Move Manager, логотип в шапке, значок вкладки. После run_style_env.sh."""
import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in ("dark", "light"):
        pg = b.new_context(viewport={"width":1440,"height":800}).new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(1500)
        pg.evaluate(f"document.documentElement.dataset.theme='{theme}'")
        check(f"{theme}: заголовок вкладки", pg.title() == "KRJUK Move Manager")
        img = pg.evaluate("(() => { const i = document.querySelector('header .logo img'); if(!i) return null; const r = i.getBoundingClientRect(); return [i.naturalWidth, Math.round(r.height), i.alt]; })()")
        check(f"{theme}: логотип в шапке загружен {img}", img and img[0] > 100 and 16 <= img[1] <= 30 and img[2] == "KRJUK")
        check(f"{theme}: рядом надпись Move Manager", "Move Manager" in pg.locator("header .logo").inner_text())
        fav = pg.evaluate("document.querySelector('link[rel=icon]')?.href || ''")
        check(f"{theme}: значок вкладки", fav.endswith("/static/favicon.png"))
        check(f"{theme}: нет ошибок", not errs)
        pg.screenshot(path=f"/mnt/user-data/outputs/brand_{theme}.png", clip={"x":0,"y":0,"width":1440,"height":110})
        pg.close()
    b.close()
sys.exit(0 if ok else 1)
