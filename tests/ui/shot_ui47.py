"""Сборка 47: оранжевого нет нигде в интерфейсе (кроме колеса Камелота). После run_style_env.sh."""
import sys
from playwright.sync_api import sync_playwright
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
JS = """(() => { const bad = [];
  for(const el of document.querySelectorAll('body *')){
    if(el.closest('svg')) continue;                       // колесо Камелота — своя шкала
    const cs = getComputedStyle(el);
    for(const k of ['color','backgroundColor','borderTopColor','borderLeftColor','outlineColor','boxShadow']){
      const m = (cs[k]||'').match(/rgba?\\((\\d+), (\\d+), (\\d+)/g) || [];
      for(const c of m){ const [r,g,b] = c.match(/\\d+/g).map(Number); if(r>200 && g>60 && g<170 && b<90 && cs.display!=='none') bad.push(el.tagName+'.'+el.className+' '+k+' '+c); }
    } }
  return bad.slice(0,5); })()"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in ("dark", "light"):
        pg = b.new_context(viewport={"width":1440,"height":900}).new_page()
        pg.goto("http://127.0.0.1:8765"); pg.wait_for_timeout(1500)
        pg.evaluate(f"document.documentElement.dataset.theme='{theme}'")
        pg.locator("#libGrid .tile").first.click(); pg.wait_for_timeout(800)
        check(f"{theme}: Projects без оранжевого {pg.evaluate(JS)}", not pg.evaluate(JS))
        pg.locator("[data-view=samples]").click(); pg.wait_for_timeout(1500)
        pg.locator("#moveGrid [data-ulfolder]").first.dblclick(); pg.wait_for_timeout(400)
        pg.locator("#moveGrid .ulrow").first.click(); pg.wait_for_timeout(400)
        check(f"{theme}: Samples без оранжевого {pg.evaluate(JS)}", not pg.evaluate(JS))
        bg = pg.evaluate("getComputedStyle(document.querySelector('button.primary, #toPc')).backgroundColor")
        check(f"{theme}: кнопки To computer / главные — синие ({bg})", "255, 91, 0" not in bg)
        pg.close()
    b.close()
sys.exit(0 if ok else 1)
