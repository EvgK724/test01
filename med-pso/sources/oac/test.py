# Проверка «Ранней антикоагуляции»: ошибки, калькуляторы на известных входах, карточки, раскладки телефона и iPad.
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
        # ——— телефон
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, device_scale_factor=2)
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.screenshot(path=str(here / "s-top.png"))
        # калькулятор дат
        await set_val(pg, "#onset", "2026-09-27T08:00")
        await set_val(pg, "#nihss", "5")
        out["minor"] = await texts(pg, "#tres .rl, #tres .res-note")
        await pg.click('[data-size="major"]'); await set_val(pg, "#nihss", "12")
        out["major"] = await texts(pg, "#tres .rl")
        await set_val(pg, "#nihss", "20")
        out["major20"] = await texts(pg, "#tres .rl")
        await pg.click('[data-size="moderate"]'); await set_val(pg, "#ivt", "2026-09-27T09:00")
        out["moderate_ivt"] = await texts(pg, "#tres .rl")
        await pg.click('[data-ht="ph"]')
        out["ph"] = await texts(pg, "#tres .rl")
        await pg.click('[data-ht="hi"]')
        out["hi"] = await texts(pg, "#tres .rl")
        await pg.click('[data-size="tia"]'); await pg.click('[data-ht="none"]'); await pg.click("#ivtClear")
        out["tia"] = await texts(pg, "#tres .rl")
        await pg.click('[data-size="minor"]')
        await pg.eval_on_selector("#tcalc", "e => e.scrollIntoView()"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=str(here / "s-tcalc.png"))
        # калькулятор дозы
        out["dose_default"] = await texts(pg, "#dres .crcl, #dres li")
        for age, kg, cr, key in [("82", "58", "100", "dose_82_58"), ("82", "70", "100", "dose_82_70"), ("90", "45", "300", "dose_ckd5"), ("50", "80", "70", "dose_young")]:
            await set_val(pg, "#age", age); await set_val(pg, "#wt", kg); await set_val(pg, "#cr", cr)
            out[key] = await texts(pg, "#dres .crcl, #dres li")
        await pg.click('[data-sex="m"]'); await pg.click('[data-flag="verap"]'); await pg.click('[data-flag="pgp"]')
        out["dose_young_m_flags"] = await texts(pg, "#dres .crcl, #dres li, #dres .res-note")
        await pg.eval_on_selector("#dcalc", "e => e.scrollIntoView()"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=str(here / "s-dcalc.png"))
        # переходы по разделам
        await pg.click('.jump button[data-to="s-anti"]'); await pg.wait_for_timeout(700)
        await pg.screenshot(path=str(here / "s-anti.png"))
        await pg.click('.jump button[data-to="s-ivt"]') if await pg.locator('.jump button[data-to="s-ivt"]').is_visible() else None
        await pg.eval_on_selector("#s-ivt", "e => e.scrollIntoView()"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(here / "s-ivt.png"))
        await pg.eval_on_selector("#s-topics", "e => e.scrollIntoView()"); await pg.wait_for_timeout(200)
        await pg.click(".t-head >> nth=0"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(here / "s-topic1.png"))
        # ширина: ничего не вылезает вбок
        out["overflow_x"] = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        out["wide_elems"] = await pg.evaluate("""[...document.querySelectorAll('#rule *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + 1); }).slice(0, 8).map(e => e.className + ' ' + Math.round(e.getBoundingClientRect().right))""")
        # тренировка: ответить на все карточки первой сессии
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
        out["saved"] = await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('oac:state')).progress).length")
        out["errors_phone"] = errs[:]
        # все карточки показываются без ошибок (итоговая тема)
        await ctx.close()
        # ——— iPad портрет и альбом
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
