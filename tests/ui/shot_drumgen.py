"""Генератор барабанов во вкладке Clips (библиотека, имитация). Запуск после run_style_env.sh."""
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
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "404" not in m.text and "409" not in m.text else None)
    pg.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    pg.locator("#libGrid .tile.row", has_text="Demo 1").first.click(); pg.wait_for_timeout(500)
    pg.locator("[data-tab=clips]").click(); pg.wait_for_timeout(300)
    # барабанная дорожка 1, пустая ячейка
    cells = pg.locator(".clipcell[data-t='0']")
    empty = [i for i in range(cells.count()) if "on" not in (cells.nth(i).get_attribute("class") or "")]
    filled = [i for i in range(cells.count()) if "on" in (cells.nth(i).get_attribute("class") or "")]
    cells.nth(empty[0]).click(); pg.wait_for_timeout(300)
    check("кнопка Generate у барабанной дорожки", pg.locator("#genOpen").count() == 1 and pg.locator("#genOpen").is_enabled())
    pg.locator("#genOpen").click(); pg.wait_for_timeout(1500)
    check("панель генератора", pg.locator("#gen").count() == 1)
    check("ручка Mutation по умолчанию 35", pg.locator("#genMut").input_value() == "35")
    check("источник: только жанры", 10 < pg.locator("#genSource option").count() < 60 and pg.locator("#genSource option[value^='p:']").count() == 0)
    check("сетка заполнена", pg.locator("#genGrid .gc.on").count() > 3)
    labels = pg.evaluate("[...document.querySelectorAll('#genGrid .gl')].map(e=>e.textContent)")
    check("строки сетки — роли (kick, snare, hh)", any(l.startswith("kick") for l in labels) and any(l.startswith("snare") for l in labels))
    check("подпись источника Pocket Operations", "Pocket Operations" in pg.locator("#gen").inner_text())
    before = pg.locator("#genGrid").inner_html()
    pg.locator("#genMut").fill("80"); pg.locator("#genMut").dispatch_event("change"); pg.wait_for_timeout(800)
    pg.locator("#genAnother").click(); pg.wait_for_timeout(800)
    check("Another меняет рисунок", pg.locator("#genGrid").inner_html() != before)
    # Another на минимальной мутации: рисунок меняется или есть подсказка
    pg.select_option("#genSource", label="Trap"); pg.wait_for_timeout(800)
    pg.locator("#genMut").fill("1"); pg.locator("#genMut").dispatch_event("change"); pg.wait_for_timeout(800)
    for k in range(8):
        g0 = pg.locator("#genGrid").inner_html()
        pg.locator("#genAnother").click(); pg.wait_for_timeout(1500)
        check(f"Another #{k+1} на Mutation 1 меняет рисунок или объясняет", pg.locator("#genGrid").inner_html() != g0 or "Raise Mutation" in pg.locator("#gen").inner_text())
    one = "Deep House"
    pg.select_option("#genSource", label=one); pg.wait_for_timeout(800)
    pg.locator("summary", has_text="More").click(); pg.wait_for_timeout(200)
    pg.locator("#genDeja").fill("0"); pg.locator("#genDeja").dispatch_event("change"); pg.wait_for_timeout(600)
    pg.locator("#genEuclid").fill("0"); pg.locator("#genEuclid").dispatch_event("change"); pg.wait_for_timeout(500); pg.locator("#genGhost").fill("0"); pg.locator("#genGhost").dispatch_event("change"); pg.wait_for_timeout(500)
    pg.locator("#genMut").fill("0"); pg.locator("#genMut").dispatch_event("change"); pg.wait_for_timeout(800)
    pg.locator("#genAnother").click(); pg.wait_for_timeout(4000)
    check(f"жанр с одним рисунком ({one}) на Mutation 0: Another объясняет", "Raise Mutation" in pg.locator("#gen").inner_text())
    pg.locator("#genEuclid").fill("30"); pg.locator("#genEuclid").dispatch_event("change"); pg.wait_for_timeout(500); pg.locator("#genGhost").fill("30"); pg.locator("#genGhost").dispatch_event("change"); pg.wait_for_timeout(500)
    pg.locator("summary", has_text="More").click(); pg.wait_for_timeout(200)
    # дежавю: 0 — такты одинаковые, 100 — разные
    def halves():
        return pg.evaluate("""(() => { const n = S.gen.result.notes, a = new Set(), b = new Set();
            n.forEach(x => (x.startTime < 4 ? a : b).add(x.role + ':' + Math.round((x.startTime % 4) * 4)));
            return [[...a].sort().join(), [...b].sort().join()]; })()""")
    pg.locator("#genMut").fill("60"); pg.locator("#genMut").dispatch_event("change"); pg.wait_for_timeout(800)
    pg.locator("summary", has_text="More").click(); pg.wait_for_timeout(200)
    pg.locator("#genDeja").fill("0"); pg.locator("#genDeja").dispatch_event("change"); pg.wait_for_timeout(800)
    h = halves(); check("Déjà vu 0 — такты одинаковые", h[0] == h[1])
    pg.locator("#genDeja").fill("100"); pg.locator("#genDeja").dispatch_event("change"); pg.wait_for_timeout(800)
    h = halves(); check("Déjà vu 100 — такты разные", h[0] != h[1])
    pg.locator("summary", has_text="More").click(); pg.wait_for_timeout(200)
    pads_req = []
    pg.on("request", lambda r: pads_req.append(r.url) if "/pad?" in r.url else None)
    pg.evaluate("GENA.played = []")
    pg.locator("#genPlay").click(); pg.wait_for_timeout(1200)
    want = sorted(pg.evaluate("S.gen.result.notes.map(n=>n.role)"))
    got = sorted(pg.evaluate("GENA.played.slice(0, S.gen.result.notes.length)"))
    check("прослушка играет роли рисунка (kick звучит как kick)", got == want and "kick" in got)
    check("сэмплы проекта не запрашиваются", not pads_req)
    check("прослушка идёт", pg.locator("#genPlay").inner_text().strip().startswith("■"))
    pg.locator("#genAnother").click(); pg.locator("#genAnother").click(); pg.wait_for_timeout(600)
    check("один планировщик", pg.evaluate("window.__genSchedulers === 1"))
    pg.locator("#genPlay").click(); pg.wait_for_timeout(300)
    check("стоп", pg.locator("#genPlay").inner_text().strip().startswith("▶"))
    pg.locator("summary", has_text="More").click(); pg.wait_for_timeout(200)
    check("ghost-ноты — ползунок", pg.locator("#genGhost").get_attribute("type") == "range")
    check("подробные ручки", all(pg.locator(s).count() == 1 for s in ("#genBars", "#genSwing", "#genDeja", "#genGhost", "#genEuclid")))
    check("роутинга пэдов в More нет", pg.locator("#gen select[data-padrole]").count() == 0)
    reads = []
    pg.on("request", lambda r: reads.append(r.post_data or "") if r.url.endswith("/api/drumgen") else None)
    pg.locator("#genAnother").click(); pg.wait_for_timeout(600)
    check("Another шлёт известный кит", reads and '"pads"' in reads[-1])
    pg.locator("#genPlay").click(); pg.wait_for_timeout(500)
    n0 = len(dialogs)
    pg.locator("#genPut").click(); pg.wait_for_timeout(1500)
    check("в пустую ячейку — без вопроса", len(dialogs) == n0)
    check("после Put прослушка остановлена", pg.evaluate("!S.gen || !S.gen.playing") and pg.evaluate("GENA.timer === null"))
    check("ячейка занята", "on" in (pg.locator(f".clipcell[data-t='0'][data-s='{empty[0]}']").get_attribute("class") or ""))
    if filled:
        pg.locator(f".clipcell[data-t='0'][data-s='{filled[0]}']").click(); pg.wait_for_timeout(300)
        pg.locator("#genOpen").click(); pg.wait_for_timeout(1200)
        pg.locator("#genPut").click(); pg.wait_for_timeout(1500)
        check("занятая — подтверждение", len(dialogs) > n0 and "Replace" in dialogs[-1])
    # не барабанная дорожка
    pg.locator(".clipcell[data-t='1']").first.click(); pg.wait_for_timeout(300)
    gb = pg.locator("#genOpen")
    check("у не-барабанной дорожки Generate выключен", gb.count() == 1 and not gb.is_enabled())
    err = pg.evaluate("""(() => { try { const c = genCtx(); ["kick","snare","clap","rim","chh","ohh","tom_low","tom_mid","tom_high","crash","ride","shaker","cowbell","perc"]
        .forEach(r => genSynth(r, c.currentTime + 0.05, 100)); return ""; } catch(e) { return String(e); } })()""")
    check("синтез: все 14 ролей без ошибок", err == "")
    # проект на Move: звуки кита из скачанного бандла
    pg.locator("#moveGrid .tile").first.click(); pg.wait_for_timeout(600)
    pg.locator("[data-tab=clips]").click(); pg.wait_for_timeout(300)
    mc = pg.locator(".clipcell[data-t='0']")
    if mc.count():
        mc.first.click(); pg.wait_for_timeout(300)
        if pg.locator("#genOpen").is_enabled():
            pg.locator("#genOpen").click(); pg.wait_for_timeout(2500)
            pg.locator("#genPlay").click(); pg.wait_for_timeout(3000)
            check("Move: прослушка играет", pg.evaluate("GENA.log.length > 0"))
            check("Move: без скачивания проекта", not [u for u in pads_req if "/move/" in u])
            pg.locator("#genPlay").click()
    pg.screenshot(path="/tmp/drumgen.png", full_page=True)
    check("нет ошибок страницы", not errs); print(errs) if errs else None
    b.close()
sys.exit(0 if ok else 1)
