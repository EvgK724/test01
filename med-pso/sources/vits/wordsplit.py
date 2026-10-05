# Слова, разорванные переносом посреди слова (без дефиса): карточки после ответа и весь справочник
import asyncio, pathlib, sys
from playwright.async_api import async_playwright
here = pathlib.Path(__file__).resolve().parent
JS = r"""
(sel) => {
  const out = []; const scope = document.querySelector(sel);
  const w = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT); let n;
  while ((n = w.nextNode())){
    const p = n.parentElement; if (!p || p.closest('.sr,[hidden]') || !p.getClientRects().length) continue;
    const re = /[A-Za-zА-Яа-яЁё0-9,.%]{6,}/g; let m;
    while ((m = re.exec(n.nodeValue))){
      const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
      const rs = [...r.getClientRects()].filter(b => b.width > 1);
      if (rs.length > 1 && Math.abs(rs[0].top - rs[rs.length-1].top) > 4){
        const hy = getComputedStyle(p).hyphens === 'auto';
        out.push((hy ? '(перенос) ' : '') + m[0]);
      }
    }
  }
  return out;
}
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for vw, vh in [(320, 568), (390, 844), (1180, 820)]:
            pg = await b.new_page(viewport={"width": vw, "height": vh})
            await pg.goto("file://" + str(here / "preview.html")); await pg.wait_for_timeout(300)
            await pg.add_style_tag(content=':root{--serif:"DejaVu Serif",serif!important;--sans:"DejaVu Sans",sans-serif!important}')
            found = set()
            await pg.evaluate("setTab('rule')")
            nt = await pg.locator(".t-head").count()
            for i in range(nt):
                await pg.locator(".t-head").nth(i).evaluate("e => e.click()")
            found |= set(await pg.evaluate(JS, "#rule"))
            await pg.evaluate("setTab('drill')")
            nc = await pg.evaluate("CARDS.length")
            for i in range(nc):
                await pg.evaluate(f"(() => {{ queue = CARDS.slice(); index = {i}; render(); }})()")
                found |= {"вопрос: " + x for x in await pg.evaluate(JS, "#drill")}
                await pg.evaluate("(() => { const c = queue[index]; choose(c.a); })()")
                found |= {"ответ: " + x for x in await pg.evaluate(JS, "#drill")}
            print(f"{vw}x{vh}:", len(found), sorted(found)[:25])
            await pg.close()
        await b.close()
asyncio.run(main())
