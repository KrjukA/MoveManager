"""Проверка вкладки «Клипы» против имитации Move. Запуск: python3 test/shot_clips.py (сервер и имитация уже подняты)."""
import sys, tempfile, os
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from midi import clip_to_midi, midi_to_notes
from playwright.sync_api import sync_playwright

mid = os.path.join(tempfile.mkdtemp(), "in.mid")
open(mid, "wb").write(clip_to_midi({"timeSignature": {"upper": 4, "lower": 4},
    "region": {"start": 0, "end": 8, "loop": {"start": 0, "end": 8, "isEnabled": True}},
    "notes": [{"noteNumber": 60, "startTime": 0.0, "duration": 1.0, "velocity": 90.0},
              {"noteNumber": 64, "startTime": 5.0, "duration": 1.0, "velocity": 90.0}]}, 120.0))
ok = True
def load_via_button(pg):
    with pg.expect_file_chooser() as fc:
        pg.locator("#clipLoad").click()
    fc.value.set_files(mid)
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and cond

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    errs, dialogs = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
    pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(2500)
    for side in ("lib", "move"):
        grid = "#libGrid" if side == "lib" else "#moveGrid"
        pg.locator(grid + " .tile", has_text="BGDN LV").first.click(); pg.wait_for_timeout(600)
        tab = pg.locator("[data-tab=clips]")
        check(f"{side}: вкладка «Клипы» есть", tab.count() == 1)
        if not tab.count(): continue
        tab.click(); pg.wait_for_timeout(300)
        check(f"{side}: 32 ячейки", pg.locator(".clipcell").count() == 32)
        check(f"{side}: 4 занятые", pg.locator(".clipcell.on").count() == 4)
        pg.locator(".clipcell[data-t='0'][data-s='0']").click(); pg.wait_for_timeout(200)
        check(f"{side}: у занятой есть «Сохранить .mid» и «Загрузить .mid»", pg.locator("#clipSave").count() == 1 and pg.locator("#clipLoad").count() == 1)
        with pg.expect_download() as dl:
            pg.locator("#clipSave").click()
        path = dl.value.path()
        check(f"{side}: скачанный .mid читается (4 ноты)", len(midi_to_notes(open(path, "rb").read())[0]) == 4)
        pg.locator(".clipcell[data-t='1'][data-s='3']").click(); pg.wait_for_timeout(200)
        check(f"{side}: у пустой только «Загрузить .mid»", pg.locator("#clipSave").count() == 0 and pg.locator("#clipLoad").count() == 1)
        load_via_button(pg); pg.wait_for_timeout(2500)
        check(f"{side}: после загрузки ячейка занята", pg.locator(".clipcell.on[data-t='1'][data-s='3']").count() == 1)
        n0 = len(dialogs)
        pg.locator(".clipcell[data-t='0'][data-s='0']").click(); pg.wait_for_timeout(200)
        load_via_button(pg); pg.wait_for_timeout(2500)
        check(f"{side}: замена занятой спрашивает подтверждение", any("Replace" in d for d in dialogs[n0:]))
        check(f"{side}: после замены в ячейке 2 ноты", "2" in pg.locator(".clipcell[data-t='0'][data-s='0']").inner_text())
        # M6: ошибка сервера при сохранении — сообщение в программе, а не битый файл
        pg.route("**/clip.mid*", lambda r: r.fulfill(status=503, content_type="application/json",
                 body='{"error":"offline","message":"Move недоступен"}'))
        got = []
        pg.on("download", lambda d: got.append(d))
        pg.locator(".clipcell[data-t='0'][data-s='0']").click(); pg.wait_for_timeout(200)
        pg.locator("#clipSave").click(); pg.wait_for_timeout(800)
        check(f"{side}: ошибка при сохранении видна, файл не скачан", not got and "недоступен" in pg.locator("#status").inner_text())
        pg.unroute("**/clip.mid*")
        pg.screenshot(path=f"/tmp/clips_{side}.png")
    check("нет ошибок страницы", not errs); print(errs)
    b.close()
sys.exit(0 if ok else 1)
