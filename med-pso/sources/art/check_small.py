import asyncio, pathlib, subprocess, sys, time
from playwright.async_api import async_playwright
root = pathlib.Path("art").resolve()
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8863", "--bind", "127.0.0.1"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w, h in [(360, 740), (390, 844), (1180, 760), (820, 1130)]:
            pg = await (await b.new_context(viewport={"width": w, "height": h})).new_page()
            await pg.goto("http://127.0.0.1:8863/preview.html"); await pg.wait_for_timeout(700)
            await pg.click("#tabDrill"); await pg.wait_for_timeout(100)
            bad = await pg.evaluate("""(() => { const bad = []; CARDS.forEach(c => { queue = [c]; index = 0; render();
                choose(c.a); const k = document.getElementById('card'); if (k.scrollHeight > k.clientHeight + 2) bad.push(c.id + ':' + (k.scrollHeight - k.clientHeight)); }); return bad; })()""")
            print(w, h, bad)
        await b.close()
try:
    asyncio.run(run())
finally:
    srv.terminate()
