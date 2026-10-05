import asyncio, json, time, pathlib, subprocess, sys
from playwright.async_api import async_playwright
root = pathlib.Path("art").resolve()
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8862", "--bind", "127.0.0.1"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
JS = r"""
() => {
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(",").map(x => parseFloat(x)); return {r:p[0], g:p[1], b:p[2], a: p.length > 3 ? p[3] : 1}; };
  const lin = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const L = c => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const blend = (fg, bg) => ({ r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 });
  function bgOf(el){
    const stack = [];
    for (let n = el; n; n = n.parentElement){ const c = parse(getComputedStyle(n).backgroundColor); if (c && c.a > 0) stack.push(c); if (c && c.a >= 1) break; }
    let bg = {r:14, g:17, b:19, a:1};
    for (let i = stack.length - 1; i >= 0; i--) bg = blend(stack[i], bg);
    return bg;
  }
  const out = [], seen = new Set();
  document.querySelectorAll("body *").forEach(el => {
    if (!el.offsetParent && getComputedStyle(el).position !== "fixed") return;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!own) return;
    const cs = getComputedStyle(el);
    const fg = parse(cs.color); if (!fg) return;
    const bg = bgOf(el);
    const f = blend(fg, bg);
    const l1 = L(f), l2 = L(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700;
    const large = size >= 24 || (bold && size >= 18.66);
    const need = large ? 3 : 4.5;
    const key = cs.color + "|" + [bg.r, bg.g, bg.b].join(",") + "|" + (large ? "L" : "N");
    if (seen.has(key)) return; seen.add(key);
    out.push({ sample: el.textContent.trim().slice(0, 28), color: cs.color, bg: "rgb(" + [bg.r, bg.g, bg.b].map(Math.round).join(",") + ")", size: size, ratio: +ratio.toFixed(2), need: need, pass: ratio >= need });
  });
  const small = [];
  document.querySelectorAll("button, [role=tab], input").forEach(b => {
    const r = b.getBoundingClientRect();
    if (!r.width) return;
    if (r.width < 44 || r.height < 44) small.push({ text: (b.getAttribute("aria-label") || b.textContent).trim().slice(0, 24), w: Math.round(r.width), h: Math.round(r.height) });
  });
  const unnamed = [...document.querySelectorAll("button")].filter(b => b.offsetParent && !(b.getAttribute("aria-label") || b.textContent.trim())).length;
  return { contrast: out, small: small, unnamed: unnamed, lang: document.documentElement.lang, h1: document.querySelectorAll("h1").length };
}
"""
async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await (await b.new_context(viewport={"width": 390, "height": 800})).new_page()
        await pg.goto("http://127.0.0.1:8862/preview.html"); await pg.wait_for_timeout(1200)
        await pg.evaluate("openTopic = 3; renderTopics()"); await pg.wait_for_timeout(200)
        await pg.click('.schip[data-seg="m2"]'); await pg.wait_for_timeout(200)
        rules = await pg.evaluate(JS)
        await pg.click("#evtTog"); await pg.wait_for_timeout(200)
        evt = await pg.evaluate(JS)
        await pg.click('.vchip[data-view="aspects"]'); await pg.wait_for_timeout(1000)
        await pg.click("#aspTog"); await pg.click('.schip[data-seg="al"]'); await pg.wait_for_timeout(200)
        asp = await pg.evaluate(JS)
        await pg.click("#tabDrill"); await pg.wait_for_timeout(150)
        await pg.evaluate("buildMain(); render();"); await pg.wait_for_timeout(150)
        q = await pg.evaluate(JS)
        i = await pg.evaluate("shownOpts.findIndex(o => o !== queue[index].a)")
        await (await pg.query_selector_all("#opts .opt"))[i].click(); await pg.wait_for_timeout(150)
        ans = await pg.evaluate(JS)
        await pg.evaluate("queue = [CARDS.find(c => c.id === 'm-tap-m3')]; index = 0; mode = 'topic'; topicN = 3; render();"); await pg.wait_for_timeout(150)
        tap = await pg.evaluate(JS)
        await pg.evaluate("queue = [CARDS.find(c => c.id === 'r-fig-ba')]; index = 0; render();"); await pg.wait_for_timeout(150)
        fig = await pg.evaluate(JS)
        await b.close()
    res = {"rules": rules, "evt": evt, "aspects": asp, "question": q, "answer": ans, "tap": tap, "fig": fig}
    fails = []
    for k, v in res.items():
        for c in v["contrast"]:
            if not c["pass"]: fails.append((k, c))
    print("contrast checks:", sum(len(v["contrast"]) for v in res.values()), "failures:", len(fails))
    for k, c in fails: print("  FAIL", k, c)
    lowest = sorted([c for v in res.values() for c in v["contrast"]], key=lambda c: c["ratio"])[:6]
    print("lowest ratios:"); [print("  ", c["ratio"], "need", c["need"], c["color"], "on", c["bg"], "|", c["sample"]) for c in lowest]
    for k, v in res.items(): print(k, "small targets:", v["small"], "unnamed buttons:", v["unnamed"], "lang:", v["lang"], "h1:", v["h1"])
try:
    asyncio.run(run())
finally:
    srv.terminate()
