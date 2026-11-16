import json, sys, urllib.request
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"])
    ctx = b.new_context(viewport={"width":1440,"height":1000}); ctx.grant_permissions(["microphone"])
    pg = ctx.new_page(); errs, dialogs = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: (dialogs.append(d.message), d.accept("/tmp/midisrc")))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    # мониторинг: выбор входа виден сразу
    check("выбор входа мониторинга виден до включения", pg.locator("header #monInput").is_visible())
    # тональность: факты + Edit
    pg.locator("#libGrid .tile.row", has_text="Demo 1").first.click(); pg.wait_for_timeout(500)
    check("строка изменения тональности скрыта", pg.locator("#keyRoot").count() == 0)
    check("кнопки Edit нет", pg.locator("#keyEdit").count() == 0)
    pg.locator(".facts").dblclick(); pg.wait_for_timeout(300)
    check("двойной щелчок по параметрам — поля тональности и темпа", pg.locator("#keyRoot").is_visible() and pg.locator("#keyTempo").is_visible())
    check("заголовок Key and tempo не дублируется", pg.locator("#insp").inner_text().count("KEY AND TEMPO") <= 1)
    # генератор
    # первый запуск: пока свои проекты читаются, видно, что идёт работа
    state = {"n": 0}
    def slow_mine(route):
        r = route.fetch(); d = r.json(); state["n"] += 1
        if state["n"] == 1:
            d["mine"] = {"ready": False, "done": 3, "total": 10}
        route.fulfill(response=r, json=d)
    pg.route("**/api/drumgen/patterns", slow_mine)
    pg.locator("[data-tab=clips]").click(); pg.wait_for_timeout(300)
    pg.locator(".clipcell[data-t='0']").nth(1).click(); pg.wait_for_timeout(300)
    pg.locator("#genOpen").click(); pg.wait_for_timeout(700)
    check("ход чтения своих проектов виден", "Reading your projects 3/10" in pg.locator("#gen").inner_text())
    check("встроенные жанры доступны сразу", pg.locator("#genSource option").count() > 10)
    pg.wait_for_timeout(3000)
    check("после чтения подсказка исчезает", "Reading your projects" not in pg.locator("#gen").inner_text())
    pg.unroute("**/api/drumgen/patterns")
    labels = pg.locator("#genSource option").all_inner_texts()
    check("у жанров нет цифр", labels and not any("(" in l and l.rstrip().endswith(")") and l.rstrip(")").split("(")[-1].isdigit() for l in labels))
    groups = pg.evaluate("[...document.querySelectorAll('#genSource optgroup')].map(g=>g.label)")
    check("свои проекты отдельной группой", "My projects" in groups and groups.index("My projects") > 0)
    pg.locator("summary", has_text="More").click(); pg.wait_for_timeout(200)
    check("Euclid — ползунок", pg.locator("#genEuclid").get_attribute("type") == "range")
    # прокрутка панели не прыгает при движении ручек и Put in cell
    pg.evaluate("(() => { const el = document.querySelector('#insp'); el.scrollTop = el.scrollHeight - el.clientHeight - 300; el.dispatchEvent(new Event('scroll')); })()"); pg.wait_for_timeout(200)
    y0 = pg.evaluate("document.querySelector('#insp').scrollTop")
    pg.evaluate("(() => { const r = document.querySelector('#genMut'); r.value = 60; r.dispatchEvent(new Event('change', {bubbles:true})); })()"); pg.wait_for_timeout(900)
    y1 = pg.evaluate("document.querySelector('#insp').scrollTop")
    check("ручка генератора не сдвигает прокрутку", y0 > 50 and abs(y1 - y0) < 5)
    opts = pg.locator("#genHalf option").all_inner_texts()
    check("½ time: всё / бочка / бочка + малый", len(opts) == 4)
    pg.select_option("#genHalf", value="kick"); pg.wait_for_timeout(900)
    check("½ time только для бочки", pg.evaluate("S.gen.result.half === 'kick'"))
    pg.select_option("#genHalf", value="all"); pg.wait_for_timeout(900)
    check("половинный темп растягивает рисунок", pg.evaluate("S.gen.result.half === true && S.gen.result.notes.every(n => Math.round(n.startTime*4) % 2 === 0)"))
    pg.evaluate("document.querySelector('#insp').scrollTop = 99999"); y0 = pg.evaluate("document.querySelector('#insp').scrollTop")
    pg.evaluate("document.querySelector('#genPut').click()"); pg.wait_for_timeout(1500)
    y1 = pg.evaluate("document.querySelector('#insp').scrollTop")
    check("Put in cell не сдвигает прокрутку", abs(y1 - y0) < 40)
    pg.locator("#midiFolderBtn").click(); pg.wait_for_timeout(2000)
    groups = pg.evaluate("[...document.querySelectorAll('#genSource optgroup')].map(g=>g.label)")
    check("папка MIDI даёт свою группу", "MIDI folder" in groups)
    check("жанр из подпапки MIDI", "Jungle (MIDI folder)" in pg.locator("#genSource").inner_text() or "Jungle" in pg.evaluate("[...document.querySelectorAll('#genSource optgroup[label=\"MIDI folder\"] option')].map(o=>o.textContent).join()"))
    check("нет ошибок страницы", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
