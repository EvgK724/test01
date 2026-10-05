# Проверка «ВИТС после инсульта»: ошибки, калькуляторы на известных входах, карточки, раскладки телефона и iPad.
import asyncio, json, pathlib
from playwright.async_api import async_playwright
here = pathlib.Path(__file__).resolve().parent
URL = "file://" + str(here / "preview.html")

async def set_val(pg, sel, v):
    await pg.eval_on_selector(sel, "(e, v) => { e.value = v; e.dispatchEvent(new Event('input', {bubbles:true})); }", v)

async def texts(pg, sel):
    return await pg.eval_on_selector_all(sel, "els => els.map(e => e.innerText.replace(/\\s+/g, ' ').trim())")

async def main():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, device_scale_factor=2)
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.screenshot(path=str(here / "s-top.png"))
        # калькулятор режима
        R = "#pres .rl > .rk, #pres .rl > .rv, #pres .dzr li, #pres .res-note"
        out["default_68_3.2"] = await texts(pg, R)
        await set_val(pg, "#age", "79")
        out["old_new"] = await texts(pg, R)
        await set_val(pg, "#ldl", "2.4"); await set_val(pg, "#age", "60")
        out["ldl2.4"] = await texts(pg, "#pres .rl > .rv")
        await set_val(pg, "#ldl", "4.5")
        out["ldl4.5"] = await texts(pg, R)
        await set_val(pg, "#ldl", "1.1"); await pg.click('[data-cur="high"]')
        out["high_at_goal"] = await texts(pg, "#pres .rl > .rv")
        await set_val(pg, "#ldl", "2.0")
        out["high_not_goal"] = await texts(pg, R)
        await pg.click('[data-cur="highez"]')
        out["highez"] = await texts(pg, "#pres .rl > .rv")
        await pg.click('[data-cur="none"]'); await set_val(pg, "#kk", "45"); await pg.click('[data-flag="warf"]')
        out["kk45_warf"] = await texts(pg, "#pres .dzr li")
        await set_val(pg, "#kk", "25"); await pg.click('[data-flag="cyclo"]')
        out["kk25_cyclo"] = await texts(pg, "#pres .dzr li")
        await pg.click('[data-flag="extreme"]'); await set_val(pg, "#ldl", "3.0")
        out["extreme"] = await texts(pg, "#pres .rl > .rv")
        await pg.eval_on_selector("#pcalc", "e => e.scrollIntoView()"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=str(here / "s-pcalc.png"))
        # калькулятор дат
        await set_val(pg, "#start", "2026-09-29"); await set_val(pg, "#dis", "2026-10-09")
        out["ctrl"] = await texts(pg, "#mres .rl > .rv, #mres .dzr li")
        await pg.click("#disClear")
        out["ctrl_nodis"] = await texts(pg, "#mres .res-note")
        await set_val(pg, "#dis", "2026-10-09")
        await pg.eval_on_selector("#mcalc", "e => e.scrollIntoView()"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=str(here / "s-mcalc.png"))
        for sec in ["s-safe", "s-red", "s-spec"]:
            await pg.eval_on_selector("#" + sec, "e => e.scrollIntoView()"); await pg.wait_for_timeout(150)
            await pg.screenshot(path=str(here / f"s-{sec}.png"))
        await pg.eval_on_selector("#s-topics", "e => e.scrollIntoView()"); await pg.wait_for_timeout(200)
        await pg.click(".t-head >> nth=0"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(here / "s-topic1.png"))
        out["overflow_x"] = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        # тренировка
        await pg.click("#go"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(here / "s-card.png"))
        n = 0
        for i in range(30):
            loc = pg.locator("#opts:not([hidden]) .opt")
            if not await loc.count(): break
            await loc.first.click(); n += 1
            if i == 0: await pg.screenshot(path=str(here / "s-answer.png"))
            await pg.click("#next")
        out["answered"] = n
        out["saved"] = await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('vits:state')).progress).length")
        out["errors_phone"] = errs[:]
        await ctx.close()
        for name, vp in [("pad-port", {"width": 820, "height": 1180}), ("pad-land", {"width": 1180, "height": 820})]:
            ctx = await b.new_context(viewport=vp, has_touch=True)
            pg = await ctx.new_page(); e2 = []
            pg.on("pageerror", lambda e: e2.append(str(e)))
            await pg.goto(URL); await pg.wait_for_timeout(400)
            await pg.screenshot(path=str(here / f"s-{name}.png"))
            await pg.click("#go"); await pg.wait_for_timeout(200)
            await pg.screenshot(path=str(here / f"s-{name}-card.png"))
            out["errors_" + name] = e2
            await ctx.close()
        await b.close()
    print(json.dumps(out, ensure_ascii=False, indent=1))

asyncio.run(main())
