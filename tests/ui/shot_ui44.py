"""Сборка 44: имя меняется двойным щелчком в карточке; «+ Folder» на компьютере; несколько файлов сразу; строка хода не двигает список. После run_env.sh."""
import os, sys, time, json
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
SONG = "/tmp/fakeul/Sets/aaaaaaaa-0000-0000-0000-000000000001/Seed Proj/Song.abl"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width":1440,"height":900}).new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: d.accept("Fresh") if d.type == "prompt" else d.accept())
    pg.add_init_script("""window.__tops=[]; new MutationObserver(() => { const r = document.querySelector('#moveGrid .ulrow'); if(r && document.querySelector('.jobfloat:not([hidden])')) window.__tops.push(Math.round(r.getBoundingClientRect().top)); }).observe(document, {subtree:true, childList:true, attributes:true});""")
    def slow(route):
        time.sleep(1.0); route.continue_()
    pg.route("**/api/userlib/plan", slow)
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(1500)
    pg.request.get("http://127.0.0.1:8765/api/fs?mode=samples&path=/root/mmpc")
    pg.reload(); pg.wait_for_timeout(1500); pg.locator("[data-view=samples]").click(); pg.wait_for_timeout(1800)
    L, R, I = pg.locator("#moveGrid"), pg.locator("#libGrid"), pg.locator("#insp")
    L.locator("[data-ulfolder='Samples/Bounces']").dblclick(); pg.wait_for_timeout(400)
    L.locator("[data-ulfile='Samples/Bounces/Set 93 Bounce 5 - 100 bpm.wav']").click(); pg.wait_for_timeout(300)
    check("в карточке нет Rename и Move to folder", I.locator("#ulName, #ulRename, #ulDest, #ulMoveBtn").count() == 0 and "Move to folder" not in I.inner_text())
    I.locator(".ulname").dblclick(); pg.wait_for_timeout(200)
    check("двойной щелчок по имени — поле ввода", I.locator("#inlName").count() == 1)
    I.locator("#inlName").fill("Pad 5"); I.locator("#inlName").press("Enter"); pg.wait_for_timeout(3000)
    check("файл переименован, расширение сохранено", os.path.exists("/tmp/fakeul/Samples/Bounces/Pad 5.wav"))
    top0 = L.locator(".ulrow").first.bounding_box()["y"]
    check("строка хода не двигала список", len(set(pg.evaluate("window.__tops"))) <= 1)
    I.locator(".ulname").dblclick(); pg.wait_for_timeout(200)
    I.locator("#inlName").press("Escape"); pg.wait_for_timeout(200)
    check("Esc — отмена", I.locator("#inlName").count() == 0 and os.path.exists("/tmp/fakeul/Samples/Bounces/Pad 5.wav"))
    # папка: переименование двойным щелчком
    pg.locator(".pbar[data-panel=L] [data-act=up]").click(); pg.wait_for_timeout(300)
    L.locator("[data-ulfolder='Samples/Bounces']").click(); pg.wait_for_timeout(300)
    check("в карточке папки нет Rename/Move", I.locator("#ulFName, #ulFDest").count() == 0)
    I.locator(".ulname").dblclick(); I.locator("#inlName").fill("Resamples"); I.locator("#inlName").press("Enter"); pg.wait_for_timeout(3500)
    check("папка переименована, ссылки переписаны", os.path.isdir("/tmp/fakeul/Samples/Resamples") and "Samples/Resamples/" in open(SONG).read())
    # компьютер: новая папка и переименование
    check("+ Folder есть на компьютере", pg.locator(".pbar[data-panel=R] [data-act=newfolder]").is_visible())
    pg.locator(".pbar[data-panel=R] [data-act=newfolder]").click(); pg.wait_for_timeout(800)
    check("папка на компьютере создана", os.path.isdir("/root/mmpc/Fresh") and R.locator("[data-pcfolder='/root/mmpc/Fresh']").count() == 1)
    R.locator("[data-pcfolder='/root/mmpc/Kits']").dblclick(); pg.wait_for_timeout(500)
    R.locator("[data-pcfile='/root/mmpc/Kits/snare.wav']").click(); pg.wait_for_timeout(200)
    I.locator(".ulname").dblclick(); I.locator("#inlName").fill("Snare 01"); I.locator("#inlName").press("Enter"); pg.wait_for_timeout(800)
    check("файл на компьютере переименован", os.path.exists("/root/mmpc/Kits/Snare 01.wav"))
    # несколько файлов сразу
    L.locator("[data-ulfolder='Samples/Drums']").dblclick(); pg.wait_for_timeout(400)
    L.locator("[data-ulfile='Samples/Drums/kick.wav']").click()
    L.locator("[data-ulfile='Samples/Drums/old unused.wav']").click(modifiers=["Shift"]); pg.wait_for_timeout(300)
    check("выделено два", L.locator(".ulrow.sel").count() == 2 and "2 selected" in I.inner_text())
    L.locator("[data-ulfile='Samples/Drums/kick.wav']").drag_to(R.locator("[data-pcfile='/root/mmpc/Kits/Snare 01.wav']")); pg.wait_for_timeout(2500)
    check("оба скопированы на компьютер", os.path.exists("/root/mmpc/Kits/kick.wav") and os.path.exists("/root/mmpc/Kits/old unused.wav"))
    pg.locator("[data-rkind=move]").click(); pg.wait_for_timeout(1500)
    L.locator("[data-ulfile='Samples/Drums/kick.wav']").click()
    L.locator("[data-ulfile='Samples/Drums/old unused.wav']").click(modifiers=["Meta"]); pg.wait_for_timeout(300)
    L.locator("[data-ulfile='Samples/Drums/old unused.wav']").drag_to(R.locator("[data-ulfolder='Samples/Resamples']")); pg.wait_for_timeout(4000)
    check("оба перенесены внутри Move, ссылки переписаны", os.path.exists("/tmp/fakeul/Samples/Resamples/kick.wav") and os.path.exists("/tmp/fakeul/Samples/Resamples/old unused.wav") and "Samples/Resamples/kick.wav" in open(SONG).read())
    check("нет ошибок", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
