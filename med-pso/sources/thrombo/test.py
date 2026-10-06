# Проверка «Антитромботики при тромбоцитопении»: калькулятор на известных входах, 4Ts, карточки, раскладки, ошибки JS.
import asyncio, json, pathlib
from playwright.async_api import async_playwright
here = pathlib.Path(__file__).resolve().parent
URL = "file://" + str(here / "preview.html")
FL = ["vhr", "bleed", "icas", "hit"]
async def main():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, device_scale_factor=2)
        pg = await ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.screenshot(path=str(here / "s-top.png"))
        async def case(name, plt, tr="st", flags=()):
            await pg.evaluate("""([plt, tr, fl, FL]) => {
                document.getElementById('plt').value = plt;
                document.querySelector('[data-tr="' + tr + '"]').click();
                for (const f of FL){ const want = fl.includes(f); if (pc[f] !== want) document.querySelector('[data-flag="' + f + '"]').click(); }
                renderPlan(); }""", [plt, tr, list(flags), FL])
            out[name] = await pg.eval_on_selector_all("#pres .rl > .rv, #pres .rl > .rn, #pres .dzr li, #pres .res-note", "els => els.map(e => e.innerText.replace(/\\s+/g, ' ').trim())")
        await case("p200", "200")
        await case("p120", "120")
        await case("p80", "80")
        await case("p80_fall", "80", "fall")
        await case("p60_bleed", "60", flags=("bleed",))
        await case("p60_icas", "60", flags=("icas",))
        await case("p50", "50")
        await case("p40", "40")
        await case("p40_vhr", "40", flags=("vhr",))
        await case("p40_icas", "40", flags=("icas",))
        await case("p27_bleed", "27", flags=("bleed",))
        await case("p22", "22")
        await case("p15_vhr", "15", flags=("vhr",))
        await case("p8", "8")
        await case("p90_hit", "90", flags=("hit",))
        await case("empty", "")
        # 4Ts
        async def t4(name, vals):
            await pg.evaluate("""(vals) => { vals.forEach((v, q) => document.querySelector('[data-tq="' + q + '"][data-tv="' + v + '"]').click()); }""", vals)
            out[name] = await pg.eval_on_selector_all("#tres .rl > .rv, #tres .rl > .rn", "els => els.map(e => e.innerText.replace(/\\s+/g, ' ').trim())")
        await t4("4ts_1", [0, 0, 0, 1]); await t4("4ts_5", [2, 2, 0, 1]); await t4("4ts_8", [2, 2, 2, 2])
        await pg.evaluate("document.getElementById('plt').value = '35'; renderPlan()")
        await pg.eval_on_selector("#pcalc", "e => e.scrollIntoView()"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=str(here / "s-calc.png"), full_page=False)
        await pg.eval_on_selector("#s-levels", "e => e.scrollIntoView()"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=str(here / "s-levels.png"), full_page=False)
        await pg.eval_on_selector("#tcalc", "e => e.scrollIntoView()"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=str(here / "s-4ts.png"), full_page=False)
        out["overflow_x"] = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        await pg.click("#go"); await pg.wait_for_timeout(200)
        n = 0
        for i in range(30):
            loc = pg.locator("#opts:not([hidden]) .opt")
            if not await loc.count(): break
            await loc.first.click(); n += 1
            if i == 0: await pg.screenshot(path=str(here / "s-answer.png"))
            await pg.click("#next")
        out["answered"] = n
        out["errors_phone"] = errs[:]
        await ctx.close()
        for name, vp in [("pad-port", {"width": 820, "height": 1180}), ("pad-land", {"width": 1180, "height": 820})]:
            ctx = await b.new_context(viewport=vp, has_touch=True)
            pg = await ctx.new_page(); e2 = []
            pg.on("pageerror", lambda e: e2.append(str(e)))
            await pg.goto(URL); await pg.wait_for_timeout(400)
            await pg.screenshot(path=str(here / f"s-{name}.png"))
            out["errors_" + name] = e2
            await ctx.close()
        await b.close()
    print(json.dumps(out, ensure_ascii=False, indent=1))
asyncio.run(main())
