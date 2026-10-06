# Проверка «Антиагреганты при ИИ и ТИА»: калькулятор на известных входах, карточки, раскладки, ошибки JS.
import asyncio, json, pathlib, datetime
from playwright.async_api import async_playwright
here = pathlib.Path(__file__).resolve().parent
URL = "file://" + str(here / "preview.html")
def ago(h):
    d = datetime.datetime.now() - datetime.timedelta(hours=h)
    return d.strftime("%Y-%m-%dT%H:%M")
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
        async def case(name, ev="is", score="3", hrs=10, rep="none", ht="no", flags=()):
            await pg.evaluate("""([ev, sc, on, rep, ht, fl]) => {
                document.querySelector('[data-ev="' + ev + '"]').click();
                document.getElementById(ev === 'is' ? 'nihss' : 'abcd').value = sc;
                document.getElementById('onset').value = on;
                document.querySelector('[data-rep="' + rep + '"]').click();
                document.querySelector('[data-ht="' + ht + '"]').click();
                for (const f of ['af','sten','athero','icas','ich','onclop','cyp']){ const want = fl.includes(f); if (pc[f] !== want) document.querySelector('[data-flag="' + f + '"]').click(); }
                renderPlan(); }""", [ev, score, ago(hrs), rep, ht, list(flags)])
            out[name] = await pg.eval_on_selector_all("#pres .rl > .rv, #pres .rl > .rn, #pres .dzr li, #pres .res-note", "els => els.map(e => e.innerText.replace(/\\s+/g, ' ').trim())")
        await case("is3_10h")
        await case("is3_10h_ich", flags=("ich",))
        await case("is3_10h_cyp", flags=("cyp",))
        await case("is5_10h", score="5")
        await case("is5_40h_sten", score="5", hrs=40, flags=("sten",))
        await case("is5_100h", score="5", hrs=100)
        await case("is8", score="8")
        await case("is14", score="14")
        await case("is3_9d", hrs=216)
        await case("tia6", ev="tia", score="6")
        await case("tia4_30h", ev="tia", score="4", hrs=30)
        await case("tia2", ev="tia", score="2")
        await case("tia2_sten_50h", ev="tia", score="2", hrs=50, flags=("sten",))
        await case("tia_af", ev="tia", score="5", flags=("af",))
        await case("is_af", score="3", flags=("af",))
        await case("ivt", score="3", rep="ivt")
        await case("evt", score="12", rep="evt")
        await case("ht", score="3", ht="yes")
        await case("icas_mono", score="8", flags=("icas",))
        await case("icas_clop", score="2", flags=("icas", "onclop"))
        await pg.eval_on_selector("#pcalc", "e => e.scrollIntoView()"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=str(here / "s-calc.png"), full_page=False)
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
