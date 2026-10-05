import asyncio, json, pathlib, subprocess, sys, time
from playwright.async_api import async_playwright
root = pathlib.Path("art/site").resolve()
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8864", "--bind", "127.0.0.1"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
URL = "http://127.0.0.1:8864/"
async def run():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        errors = []
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append("console:" + m.text) if m.type == "error" else None)
        pg.on("requestfailed", lambda r: errors.append("reqfail:" + r.url))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        out["compat_mode"] = await pg.evaluate("document.compatMode")
        out["sw"] = await pg.evaluate("navigator.serviceWorker.getRegistration().then(r => !!(r && (r.active || r.installing || r.waiting)))")
        out["manifest"] = await pg.evaluate("fetch('manifest.webmanifest').then(r => r.json()).then(j => j.short_name + ' ' + j.display)")
        out["hscroll"] = await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        out["claude_runtime"] = await pg.evaluate("!!window.claude")
        await pg.click('.schip[data-seg="m2"]'); await pg.wait_for_timeout(200)
        out["info"] = await pg.inner_text(".i-name")
        await pg.screenshot(path=str(root.parent / "site-rule.png"))
        await pg.click("#tabDrill"); await pg.wait_for_timeout(200)
        i = await pg.evaluate("shownOpts.indexOf(queue[index].a)")
        if i >= 0: await (await pg.query_selector_all("#opts .opt"))[i].click()
        else:
            await pg.evaluate("document.querySelector('#fig .seg[data-seg=\"' + queue[index].a + '\"]').dispatchEvent(new MouseEvent('click', {bubbles: true}))")
            await pg.click("#check")
        await pg.wait_for_timeout(200)
        out["saved_local"] = await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('art:state') || '{}').progress || {}).length")
        await pg.screenshot(path=str(root.parent / "site-q.png"))
        # офлайн: перезагрузка без сети
        await pg.wait_for_timeout(800)
        await ctx.set_offline(True)
        await pg.reload(); await pg.wait_for_timeout(1200)
        out["offline_title"] = await pg.title()
        out["offline_cards"] = await pg.evaluate("typeof CARDS !== 'undefined' ? CARDS.length : 0")
        out["offline_progress_kept"] = await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('art:state') || '{}').progress || {}).length")
        await ctx.set_offline(False)
        await ctx.close()
        for w, h in [(360, 740), (390, 844), (1180, 760), (820, 1130)]:
            c2 = await b.new_context(viewport={"width": w, "height": h})
            p2 = await c2.new_page()
            p2.on("pageerror", lambda e: errors.append(str(e)))
            await p2.goto(URL); await p2.wait_for_timeout(800)
            await p2.click("#tabDrill"); await p2.wait_for_timeout(100)
            out[f"cards_{w}x{h}"] = await p2.evaluate("""(() => { const bad = []; CARDS.forEach(c => { queue = [c]; index = 0; render();
                choose(c.a); const k = document.getElementById('card'); if (k.scrollHeight > k.clientHeight + 2) bad.push(c.id + ':' + (k.scrollHeight - k.clientHeight)); }); return bad; })()""")
            out[f"hscroll_{w}x{h}"] = await p2.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            await c2.close()
        await b.close()
    out["errors"] = errors
    print(json.dumps(out, ensure_ascii=False, indent=1))
try:
    asyncio.run(run())
finally:
    srv.terminate()
