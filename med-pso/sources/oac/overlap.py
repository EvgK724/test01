# Проверка наслоений: текст на текст, выход содержимого за свой блок и за экран.
# Широкие шрифты (DejaVu) — с запасом против Georgia и SF на iPhone/iPad.
# Состояния: справочник, каждая тема, все сочетания калькулятора дат, наборы калькулятора дозы,
# каждая карточка — вопрос и ответ с ошибкой.
import asyncio, json, pathlib, sys, itertools
from playwright.async_api import async_playwright
here = pathlib.Path(__file__).resolve().parent
URL = "file://" + str(here / "preview.html")
VIEWPORTS = [(320, 568), (375, 667), (390, 844), (430, 932), (820, 1180), (1180, 820)]
WIDE = ':root{--serif:"DejaVu Serif",serif!important;--sans:"DejaVu Sans",sans-serif!important}'

CHECK = r"""
(sel) => {
  const scope = document.querySelector(sel);
  if (!scope) return ['нет ' + sel];
  const out = [];
  const shown = el => { const s = getComputedStyle(el); return s.display !== 'none' && s.visibility !== 'hidden' && el.getClientRects().length > 0; };
  const rects = [];
  const w = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT);
  let n, id = 0;
  while ((n = w.nextNode())){
    if (!n.nodeValue.trim()) continue;
    const p = n.parentElement;
    if (!p || p.closest('.sr,[hidden]') || !shown(p)) continue;
    const r = document.createRange(); r.selectNodeContents(n);
    // ближайший прокручиваемый предок и видимая область всех прокручиваемых предков
    let sc = null, clip = { l: -1e9, r: 1e9, t: -1e9, b: 1e9 };
    for (let a = p; a && a !== document.documentElement; a = a.parentElement){
      const cs = getComputedStyle(a);
      if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible'){
        if (!sc) sc = a;
        const q = a.getBoundingClientRect();
        clip = { l: Math.max(clip.l, q.left), r: Math.min(clip.r, q.right), t: Math.max(clip.t, q.top), b: Math.min(clip.b, q.bottom) };
      }
    }
    for (const b of r.getClientRects()) if (b.width >= 1 && b.height >= 1)
      rects.push({ l: b.left, r: b.right, t: b.top, b: b.bottom, id, sc, clip, txt: n.nodeValue.trim().slice(0, 36) });
    id++;
  }
  rects.sort((a, b) => a.t - b.t);
  for (let i = 0; i < rects.length; i++){
    const A = rects[i];
    for (let j = i + 1; j < rects.length && rects[j].t < A.b - 1; j++){
      const B = rects[j];
      if (A.id === B.id) continue;
      let a = A, c = B;
      if (A.sc !== B.sc){   // разные прокручиваемые блоки: сравниваю только видимые части
        a = { l: Math.max(A.l, A.clip.l), r: Math.min(A.r, A.clip.r), t: Math.max(A.t, A.clip.t), b: Math.min(A.b, A.clip.b) };
        c = { l: Math.max(B.l, B.clip.l), r: Math.min(B.r, B.clip.r), t: Math.max(B.t, B.clip.t), b: Math.min(B.b, B.clip.b) };
        if (a.r <= a.l || a.b <= a.t || c.r <= c.l || c.b <= c.t) continue;
      }
      const ox = Math.min(a.r, c.r) - Math.max(a.l, c.l), oy = Math.min(a.b, c.b) - Math.max(a.t, c.t);
      if (ox > 1.5 && oy > 3) out.push('наслоение: «' + A.txt + '» × «' + B.txt + '»');
    }
  }
  for (const el of scope.querySelectorAll('*')){
    if (el.closest('.sr,[hidden]') || !shown(el)) continue;
    const s = getComputedStyle(el);
    if (s.display !== 'inline' && s.overflowX === 'visible' && el.clientWidth > 0 && el.scrollWidth > el.clientWidth + 1)
      out.push('вылезает: ' + el.tagName.toLowerCase() + '.' + el.className + ' ' + el.scrollWidth + '>' + el.clientWidth + ' «' + el.textContent.trim().slice(0, 36) + '»');
    const rr = el.getBoundingClientRect();
    if (rr.width && rr.right > innerWidth + 1) out.push('за экраном: ' + el.tagName.toLowerCase() + '.' + el.className + ' → ' + Math.round(rr.right) + ' > ' + innerWidth);
  }
  return out;
}
"""

async def run_vp(b, vw, vh, report):
    ctx = await b.new_context(viewport={"width": vw, "height": vh}, has_touch=True)
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(300)
    await pg.add_style_tag(content=WIDE); await pg.wait_for_timeout(100)
    issues = {}
    async def check(where, sel):
        res = await pg.evaluate(CHECK, sel)
        for r in res: issues.setdefault(r, where)
    await pg.evaluate("setTab('rule')")
    await check("справочник", "#rule")
    # темы
    nt = await pg.locator(".t-head").count()
    for i in range(nt):
        await pg.locator(".t-head").nth(i).evaluate("e => e.click()")
        await check(f"тема {i+1}", "#topics")
    await pg.locator('.t-head[aria-expanded="true"]').first.evaluate("e => e.click()")
    # калькулятор дат: все сочетания
    await pg.evaluate("document.getElementById('onset').value = '2026-09-27T08:00'")
    for size, ht, nihss, ivt in itertools.product(["tia", "minor", "moderate", "major"], ["none", "hi", "ph"], ["", "12", "20"], ["", "2026-09-27T09:00"]):
        await pg.evaluate("""([s, h, n, i]) => {
            document.querySelector('[data-size="' + s + '"]').click();
            document.querySelector('[data-ht="' + h + '"]').click();
            document.getElementById('nihss').value = n; document.getElementById('ivt').value = i;
            renderTiming(); }""", [size, ht, nihss, ivt])
        await check(f"даты {size}/{ht}/NIHSS {nihss or '—'}/ТЛТ {'да' if ivt else 'нет'}", "#tcalc")
    # калькулятор дозы
    cases = [("78", "62", "105"), ("82", "58", "100"), ("90", "45", "300"), ("50", "80", "70"), ("77", "55", "140"), ("30", "120", "50"), ("", "", "")]
    for (age, kg, cr), sex, fl in itertools.product(cases, ["f", "m"], [(), ("verap", "pgp", "gi")]):
        await pg.evaluate("""([a, k, c, sx, fl]) => {
            document.getElementById('age').value = a; document.getElementById('wt').value = k; document.getElementById('cr').value = c;
            document.querySelector('[data-sex="' + sx + '"]').click();
            for (const f of ['verap', 'pgp', 'gi']){ const want = fl.includes(f); if (calc[f] !== want) document.querySelector('[data-flag="' + f + '"]').click(); }
            renderDose(); }""", [age, kg, cr, sex, list(fl)])
        await check(f"доза {age}/{kg}/{cr}/{sex}/{'+'.join(fl) or '-'}", "#dcalc")
    # карточки: вопрос и ответ с ошибкой
    await pg.evaluate("setTab('drill')")
    ncards = await pg.evaluate("CARDS.length")
    for i in range(ncards):
        cid = await pg.evaluate(f"(() => {{ queue = CARDS.slice(); index = {i}; render(); return queue[index].id; }})()")
        await check(f"карточка {cid}", "#drill")
        await pg.evaluate("(() => { const c = queue[index]; choose(c.opts.find(o => o !== c.a)); })()")
        await check(f"карточка {cid}, ответ", "#drill")
        await pg.evaluate("(() => { const c = queue[index]; progress = {}; })()")
    await pg.evaluate("renderDone()")
    await check("итог тренировки", "#drill")
    await ctx.close()
    report[f"{vw}x{vh}"] = {"issues": [f"{v}: {k}" for k, v in issues.items()], "errors": errs}

async def main():
    report = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for vw, vh in VIEWPORTS:
            await run_vp(b, vw, vh, report)
            r = report[f"{vw}x{vh}"]
            print(f"{vw}x{vh}: {len(r['issues'])} проблем, {len(r['errors'])} ошибок JS", flush=True)
            for x in r["issues"][:12]: print("   ", x, flush=True)
        await b.close()
    (here / "overlap-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))

asyncio.run(main())
