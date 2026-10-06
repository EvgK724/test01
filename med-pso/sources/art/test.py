import asyncio, json, time, pathlib, subprocess, sys
from playwright.async_api import async_playwright
from PIL import Image
root = pathlib.Path("art").resolve()
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8861", "--bind", "127.0.0.1"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
URL = "http://127.0.0.1:8861/preview.html"
shots = []
async def run():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        errors = []
        async def mk(w, h):
            ctx = await b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append("console:" + m.text) if m.type == "error" else None)
            pg.on("requestfailed", lambda r: errors.append("reqfail:" + r.url))
            await pg.goto(URL); await pg.wait_for_timeout(900)
            return ctx, pg
        async def shot(pg, name):
            path = root / f"s-{name}.png"; await pg.screenshot(path=str(path)); shots.append(path)
        ctx, pg = await mk(390, 844)
        await shot(pg, "rule")
        out["hscroll"] = await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        out["views"] = await pg.evaluate("[...document.querySelectorAll('.vchip')].map(b => b.textContent)")
        # каждая схема: снимок, число кнопок сосудов
        info = {}
        for vid in ["willis", "ica", "mca", "vb", "terr", "aspects"]:
            await pg.click(f'.vchip[data-view="{vid}"]'); await pg.wait_for_timeout(1000)
            await pg.evaluate("document.getElementById('atlas').scrollIntoView()"); await pg.wait_for_timeout(100)
            await shot(pg, "v-" + vid)
            info[vid] = await pg.evaluate("({chips: document.querySelectorAll('.schip').length, segs: new Set([...document.querySelectorAll('#stage .seg:not(.a-off)')].map(g => g.dataset.seg)).size, tools: !document.getElementById('tools').hidden})")
        out["view_info"] = info
        # Виллизиев круг: нажатие на M1 по схеме, окраска ВСТЭ
        await pg.click('.vchip[data-view="willis"]'); await pg.wait_for_timeout(900)
        await pg.evaluate("document.getElementById('atlas').scrollIntoView()")
        box = await pg.evaluate("(() => { const r = document.querySelector('#stage .seg[data-seg=\"m1\"] .ln').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
        await pg.mouse.click(box[0], box[1]); await pg.wait_for_timeout(200)
        out["tap_m1"] = await pg.evaluate("[atlasSel, document.querySelectorAll('#stage .seg.on').length, document.querySelector('.i-name') && document.querySelector('.i-name').textContent]")
        await pg.click("#evtTog"); await pg.wait_for_timeout(250)
        out["evt_on"] = await pg.evaluate("[document.getElementById('stage').classList.contains('evt'), !document.getElementById('evtLegend').hidden, getComputedStyle(document.querySelector('#stage .seg[data-seg=\"ba\"] .ln')).stroke]")
        await shot(pg, "evt")
        await pg.evaluate("document.getElementById('info').scrollIntoView({block:'start'})"); await pg.wait_for_timeout(100)
        await shot(pg, "info-m1")
        # ЗМА — расхождение рекомендаций
        await pg.click('.schip[data-seg="p1"]'); await pg.wait_for_timeout(250)
        await pg.evaluate("document.getElementById('info').scrollIntoView({block:'start'})"); await pg.wait_for_timeout(100)
        await shot(pg, "info-p1")
        out["p1_badge"] = await pg.inner_text(".badge")
        # ASPECTS: счёт баллов
        await pg.click('.vchip[data-view="aspects"]'); await pg.wait_for_timeout(900)
        await pg.click("#aspTog"); await pg.wait_for_timeout(100)
        for k in ["al", "ai", "am2"]:
            box = await pg.evaluate(f"(() => {{ const r = document.querySelector('#stage .seg[data-seg=\"{k}\"] .area').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }})()")
            await pg.mouse.click(box[0], box[1]); await pg.wait_for_timeout(120)
        out["aspects_score"] = await pg.inner_text("#aspScore")
        out["aspects_x"] = await pg.evaluate("[...document.querySelectorAll('#stage .reg.x')].map(g => g.dataset.seg)")
        await pg.evaluate("document.getElementById('atlas').scrollIntoView()"); await pg.wait_for_timeout(100)
        await shot(pg, "aspects-score")
        await pg.click("#aspReset"); await pg.wait_for_timeout(100)
        out["aspects_reset"] = await pg.inner_text("#aspScore")
        # правая колонка
        for sel, name in [(".sg", "segtab"), (".crit", "crit"), (".errs", "errs")]:
            await pg.evaluate(f"document.querySelector('{sel}').scrollIntoView({{block:'start'}})"); await pg.wait_for_timeout(100)
            await shot(pg, name)
        out["overflow_rule"] = await pg.evaluate("[...document.querySelectorAll('.cr, .cr-v, .sg td, .sg th, .err, .algo, .steps li, .info, .schips, .vchips, .tools, .legend-e li')].filter(n => n.scrollWidth > n.clientWidth + 1).map(n => n.className)")
        for n in [1, 5, 8]:
            await pg.evaluate(f"openTopic = {n}; renderTopics(); document.querySelector('.t-head[aria-expanded=\"true\"]').scrollIntoView()"); await pg.wait_for_timeout(150)
            await shot(pg, f"topic{n}")
        out["groups"] = await pg.evaluate("[...document.querySelectorAll('.t-group')].map(g => g.textContent)")
        out["first_session"] = await pg.evaluate("""(() => { buildMain(); const n = {}; queue.forEach(c => n['t' + c.t] = (n['t' + c.t] || 0) + 1); return n; })()""")
        out["order"] = await pg.evaluate("FRESH_ORDER.slice(0, 30).map(c => c.t).join(',')")
        # тренировка: обычный проход с одной ошибкой
        await pg.evaluate("buildMain(); render();")
        await pg.click("#tabDrill"); await pg.wait_for_timeout(200)
        await shot(pg, "q")
        n = 0
        while n < 40:
            if not await pg.evaluate("!!queue[index]"): break
            card = await pg.evaluate("({tap: !!queue[index].tap, a: queue[index].a})")
            if card["tap"]:
                box = await pg.evaluate("(() => { const n = document.querySelector('#fig .seg[data-seg=\"' + queue[index].a + '\"] .ln, #fig .seg[data-seg=\"' + queue[index].a + '\"] .area'); const r = n.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
                await pg.evaluate("document.querySelector('#fig .seg[data-seg=\"' + queue[index].a + '\"]').dispatchEvent(new MouseEvent('click', {bubbles: true}))")
                await pg.click("#check")
            else:
                i = await pg.evaluate("shownOpts.indexOf(queue[index].a)")
                if n == 0:
                    i = await pg.evaluate("shownOpts.findIndex(o => o !== queue[index].a)")
                await (await pg.query_selector_all("#opts .opt"))[i].click()
            await pg.wait_for_timeout(60)
            if n == 0:
                out["verdict_wrong"] = await pg.inner_text("#verdict"); await shot(pg, "wrong")
            await pg.click("#next"); await pg.wait_for_timeout(50)
            n += 1
        out["answered"] = n
        out["done"] = await pg.inner_text("#hint")
        # карточка «покажи на схеме»: неверный выбор, затем верный
        await pg.evaluate("queue = [CARDS.find(c => c.id === 'm-tap-m3')]; index = 0; mode = 'topic'; topicN = 3; render();"); await pg.wait_for_timeout(150)
        await shot(pg, "tap-q")
        out["tap_hint"] = await pg.inner_text("#hint")
        out["tap_check_disabled"] = await pg.evaluate("document.getElementById('check').disabled")
        out["tap_labels_hidden"] = await pg.evaluate("[...document.querySelectorAll('#fig .vl:not(.dim)')].every(t => getComputedStyle(t).display === 'none')")
        box = await pg.evaluate("(() => { const r = document.querySelector('#fig .seg[data-seg=\"m1\"] .ln').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
        await pg.mouse.click(box[0], box[1]); await pg.wait_for_timeout(120)
        out["tap_pick"] = await pg.evaluate("tapPick")
        await shot(pg, "tap-pick")
        await pg.click("#check"); await pg.wait_for_timeout(150)
        out["tap_verdict"] = await pg.inner_text("#verdict")
        out["tap_marks"] = await pg.evaluate("[document.querySelectorAll('#fig .seg.ok').length, document.querySelectorAll('#fig .seg.bad').length, [...document.querySelectorAll('#fig .vl:not(.dim)')].some(t => getComputedStyle(t).display !== 'none')]")
        await shot(pg, "tap-wrong")
        # «что выделено»: схема и ответ
        await pg.evaluate("queue = [CARDS.find(c => c.id === 'r-fig-ba')]; index = 0; mode = 'topic'; topicN = 8; render();"); await pg.wait_for_timeout(150)
        await shot(pg, "fig-q")
        ci = await pg.evaluate("shownOpts.indexOf(queue[index].a)")
        await (await pg.query_selector_all("#opts .opt"))[ci].click(); await pg.wait_for_timeout(150)
        out["fig_verdict"] = await pg.inner_text("#verdict"); out["fig_q"] = await pg.inner_text("#q")
        await shot(pg, "fig-a")
        # все карточки: варианты не вылезают; карточка после ответа — влезает ли без прокрутки
        out["opt_overflow"] = await pg.evaluate("""(() => { const bad = []; CARDS.forEach(c => { queue = [c]; index = 0; render();
            if ([...document.querySelectorAll('#opts .opt')].some(b => b.scrollWidth > b.clientWidth + 1)) bad.push(c.id); }); return bad; })()""")
        out["card_scroll_after"] = await pg.evaluate("""(() => { const bad = []; CARDS.forEach(c => { queue = [c]; index = 0; render();
            choose(c.a); const k = document.getElementById('card'); if (k.scrollHeight > k.clientHeight + 2) bad.push(c.id + ':' + (k.scrollHeight - k.clientHeight)); }); return bad; })()""")
        out["mixed_size"] = await pg.evaluate("buildTopic(MIXED_TOPIC), queue.length")
        await ctx.close()
        for (w, h, name) in [(1180, 760, "pad-land"), (820, 1130, "pad-port"), (360, 740, "small")]:
            ctx, pg = await mk(w, h)
            await pg.click('.vchip[data-view="willis"]'); await pg.wait_for_timeout(900)
            await pg.click('.schip[data-seg="m2"]'); await pg.wait_for_timeout(200)
            await pg.evaluate("document.getElementById('rule').scrollTop = 0"); await pg.wait_for_timeout(100)
            await shot(pg, name + "-rule")
            await pg.click("#tabDrill"); await pg.wait_for_timeout(150)
            await pg.evaluate("queue = [CARDS.find(c => c.id === 'v-fig-pica')]; index = 0; mode = 'topic'; topicN = 5; render();"); await pg.wait_for_timeout(150)
            await shot(pg, name + "-fig")
            out[name + "_hscroll"] = await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            out[name + "_card_scroll"] = await pg.evaluate("""(() => { const bad = []; CARDS.filter(c => c.fig || c.tap).forEach(c => { queue = [c]; index = 0; render();
                choose(c.a); const k = document.getElementById('card'); if (k.scrollHeight > k.clientHeight + 2) bad.push(c.id + ':' + (k.scrollHeight - k.clientHeight)); }); return bad; })()""")
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
phone = [p for p in shots if "pad" not in p.name and "small" not in p.name]
third = (len(phone) + 2) // 3
sheet(phone[:third], "sheet1.png"); sheet(phone[third:2 * third], "sheet2.png"); sheet(phone[2 * third:], "sheet3.png")
sheet([p for p in shots if "pad" in p.name or "small" in p.name], "sheet4.png", 420)
