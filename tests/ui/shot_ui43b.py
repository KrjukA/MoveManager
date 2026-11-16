"""Сборка 43: пока идёт перенос или копирование — в панелях видно, что происходит. После run_env.sh."""
import os, sys, time
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":900}).new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    def slow(route):
        time.sleep(1.2); route.continue_()
    pg.route("**/api/userlib/plan", slow)
    pg.route("**/api/xfer/to-move", slow)
    pg.add_init_script("window.__jl=[]; new MutationObserver(() => document.querySelectorAll('.jobfloat:not([hidden])').forEach(x => window.__jl.push(x.textContent))).observe(document, {subtree:true, childList:true});")
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(1500)
    pg.request.get("http://127.0.0.1:8765/api/fs?mode=samples&path=/root/mmpc")
    pg.reload(); pg.wait_for_timeout(1500); pg.locator("[data-view=samples]").click(); pg.wait_for_timeout(1800)
    L, R = pg.locator("#moveGrid"), pg.locator("#libGrid")
    L.locator("[data-ulfolder='Samples/Bounces']").dblclick(); pg.wait_for_timeout(400)
    L.locator("[data-ulfile='Samples/Bounces/Set 93 Bounce 5 - 100 bpm.wav']").drag_to(L.locator("[data-ulfolder]").first if L.locator("[data-ulfolder]").count() else pg.locator(".pbar[data-panel=L] [data-act=up]"), timeout=5000, no_wait_after=True)
    pg.wait_for_timeout(300)
    check("пока считается план — видно", pg.evaluate("window.__jl.some(t => t.includes('Checking'))"))
    pg.wait_for_timeout(2500)
    check("после — строка исчезла", pg.locator(".jobfloat:not([hidden])").count() == 0)
    check("перенос сделан", os.path.exists("/tmp/fakeul/Samples/Set 93 Bounce 5 - 100 bpm.wav"))
    R.locator("[data-pcfolder='/root/mmpc/Kits']").drag_to(L, no_wait_after=True); pg.wait_for_timeout(400)
    check("копирование — видно", "Copying" in pg.locator(".jobfloat:not([hidden])").first.inner_text() if pg.locator(".jobfloat:not([hidden])").count() else False)
    pg.wait_for_timeout(3000)
    check("копирование готово и строка исчезла", bool(__import__("glob").glob("/tmp/fakeul/Samples/**/Kits/snare.wav", recursive=True)) and pg.locator(".jobfloat:not([hidden])").count() == 0)
    check("итог в строке состояния", "Copied" in pg.locator("#status").inner_text())
    check("нет ошибок", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
