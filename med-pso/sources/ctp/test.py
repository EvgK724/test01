import asyncio, json, time, pathlib, subprocess, sys
from playwright.async_api import async_playwright
from PIL import Image
root = pathlib.Path("ctp").resolve()
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8855", "--bind", "127.0.0.1"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
URL = "http://127.0.0.1:8855/preview.html"
shots = []
async def run():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        errors = []
        async def mk(w, h):
            ctx = await b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append("console:" + m.text) if m.type == "error" else None)
            pg.on("requestfailed", lambda r: errors.append("reqfail:" + r.url))
            await pg.goto(URL); await pg.wait_for_timeout(400)
            return ctx, pg
        async def shot(pg, name):
            path = root / f"s-{name}.png"; await pg.screenshot(path=str(path)); shots.append(path)
        ctx, pg = await mk(390, 800)
        await shot(pg, "rule")
        H = await pg.evaluate("document.getElementById('rule').scrollHeight")
        out["rule_height"] = H
        for k, y in enumerate([700, 1400, 2100, 2800, 3500]):
            if y > H - 400: break
            await pg.evaluate(f"document.getElementById('rule').scrollTop = {y}"); await pg.wait_for_timeout(120)
            await shot(pg, f"rule{k+2}")
        out["hscroll"] = await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        # ситуации: первая строка
        await pg.evaluate("document.querySelector('.md').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(100)
        await shot(pg, "memo")
        out["no_audio_ui"] = await pg.evaluate("!document.getElementById('sound') && !document.getElementById('say') && !document.querySelector('.mm-play, .ex-play')")
        out["memo_grid_overflow"] = await pg.evaluate("[...document.querySelectorAll('.md, .err, .algo, .vt, .mt, .mt td, .mt th, .steps li')].some(n => n.scrollWidth > n.clientWidth + 1)")
        # тема с примерами
        await pg.evaluate("openTopic = 1; renderTopics(); document.querySelector('.t-head[aria-expanded=\"true\"]').scrollIntoView()"); await pg.wait_for_timeout(150)
        await shot(pg, "topic1")
        await pg.evaluate("openTopic = 4; renderTopics(); document.querySelector('.t-head[aria-expanded=\"true\"]').scrollIntoView()"); await pg.wait_for_timeout(150)
        await shot(pg, "topic4")
        await pg.evaluate("openTopic = 7; renderTopics(); document.querySelector('.t-head[aria-expanded=\"true\"]').scrollIntoView()"); await pg.wait_for_timeout(150)
        await shot(pg, "topic7")
        out["marks7"] = await pg.evaluate("[...document.querySelectorAll('.t-body .ex-en span')].map(s => s.className + ':' + s.textContent)")
        out["groups"] = await pg.evaluate("[...document.querySelectorAll('.t-group')].map(g => g.textContent)")
        # состав первой сессии
        out["first_session"] = await pg.evaluate("""(() => { buildMain(); const n = {}; queue.forEach(c => n['t' + c.t] = (n['t' + c.t] || 0) + 1); return n; })()""")
        out["order"] = await pg.evaluate("FRESH_ORDER.map(c => c.t).join(',')")
        await pg.evaluate("buildMain(); render();")
        await pg.click("#tabDrill"); await pg.wait_for_timeout(150)
        await shot(pg, "q")
        wrong = await pg.evaluate("shownOpts.findIndex(o => o !== queue[index].a && !(queue[index].also && queue[index].also[o]))")
        await (await pg.query_selector_all("#opts .opt"))[wrong].click(); await pg.wait_for_timeout(200)
        out["verdict"] = await pg.inner_text("#verdict")
        out["audio"] = await pg.evaluate("typeof player === 'undefined' && typeof speechSynthesis !== 'undefined' ? 'нет озвучки' : 'есть код озвучки'")
        out["q_lang"] = await pg.evaluate("document.getElementById('q').lang || document.documentElement.lang")
        await shot(pg, "wrong")
        n = 0
        while n < 60:
            await pg.click("#next"); await pg.wait_for_timeout(40)
            if not await pg.evaluate("!!queue[index]"): break
            if n == 4: await shot(pg, "q2")
            i = await pg.evaluate("shownOpts.indexOf(queue[index].a)")
            await (await pg.query_selector_all("#opts .opt"))[i].click(); await pg.wait_for_timeout(40)
            if n == 4: await shot(pg, "right2")
            n += 1
        out["answered"] = n
        out["done"] = await pg.inner_text("#hint")
        out["mixed_size"] = await pg.evaluate("buildTopic(MIXED_TOPIC), queue.length")
        # ловушка: complained about — тоже верно
        await pg.evaluate("queue = [CARDS.find(c => c.id === 'p3-cbv-pen')]; index = 0; mode = 'topic'; topicN = 3; render();"); await pg.wait_for_timeout(100)
        ci = await pg.evaluate("shownOpts.indexOf(queue[index].a)")
        await (await pg.query_selector_all("#opts .opt"))[ci].click(); await pg.wait_for_timeout(150)
        out["trap_verdict"] = await pg.inner_text("#verdict")
        out["trap_q"] = await pg.inner_text("#q")
        await shot(pg, "trap")
        # карточка с двумя вариантами
        await pg.evaluate("queue = [CARDS.find(c => c.id === 'p1-formula')]; index = 0; mode = 'topic'; topicN = 1; render();"); await pg.wait_for_timeout(100)
        await shot(pg, "two")
        out["two_opts"] = await pg.evaluate("[...document.querySelectorAll('#opts .opt')].map(b => b.textContent)")
        ci = await pg.evaluate("shownOpts.indexOf(queue[index].a)")
        await (await pg.query_selector_all("#opts .opt"))[ci].click(); await pg.wait_for_timeout(150)
        out["two_verdict"] = await pg.inner_text("#verdict"); out["two_q"] = await pg.inner_text("#q")
        # самые длинные варианты
        out["long_id"] = await pg.evaluate("(() => { const m = c => Math.max(...c.opts.map(o => o.length)); const c = CARDS.reduce((a, c) => m(c) > m(a) ? c : a); queue = [c]; index = 0; mode = 'topic'; topicN = c.t; render(); return c.id; })()"); await pg.wait_for_timeout(100)
        await shot(pg, "long")
        out["long_overflow"] = await pg.evaluate("[...document.querySelectorAll('#opts .opt')].some(b => b.scrollWidth > b.clientWidth + 1)")
        # все карточки: ни один вариант не вылезает за кнопку
        out["any_overflow"] = await pg.evaluate("""(() => { const bad = []; CARDS.forEach(c => { queue = [c]; index = 0; render();
            if ([...document.querySelectorAll('#opts .opt')].some(b => b.scrollWidth > b.clientWidth + 1)) bad.push(c.id); }); return bad; })()""")
        await ctx.close()
        for (w, h, name) in [(1180, 760, "pad-land"), (820, 1130, "pad-port")]:
            ctx, pg = await mk(w, h)
            await shot(pg, name + "-rule")
            await pg.click("#go"); await pg.wait_for_timeout(200)
            await shot(pg, name + "-q")
            out[name + "_hscroll"] = await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            await ctx.close()
        await b.close()
    out["errors"] = errors
    print(json.dumps(out, ensure_ascii=False, indent=1))
try:
    asyncio.run(run())
finally:
    srv.terminate()
def sheet(paths, name, h=560):
    ims = [Image.open(p) for p in paths]
    ims = [im.resize((int(im.width * h / im.height), h)) for im in ims]
    W = sum(im.width for im in ims) + 10 * (len(ims) + 1)
    s = Image.new("RGB", (W, h + 20), (60, 60, 60)); x = 10
    for im in ims: s.paste(im, (x, 10)); x += im.width + 10
    s.save(root / name)
phone = [p for p in shots if "pad" not in p.name]
half = (len(phone) + 1) // 2
sheet(phone[:half], "sheet1.png"); sheet(phone[half:], "sheet2.png")
sheet([p for p in shots if "pad" in p.name], "sheet3.png", 420)
