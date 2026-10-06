import asyncio, pathlib, subprocess, sys, time
from playwright.async_api import async_playwright
from PIL import Image
root = pathlib.Path("art/site").resolve()
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8866", "--bind", "127.0.0.1"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
shots = []
async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await (await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)).new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("http://127.0.0.1:8866/"); await pg.wait_for_timeout(900)
        await pg.click("#evtTog"); await pg.wait_for_timeout(300)
        for vid in ("willis", "mca"):
            chip = await pg.query_selector(f'.vchip[data-view="{vid}"]')
            if chip: await chip.click(); await pg.wait_for_timeout(300)
            await pg.evaluate("document.getElementById('stage').scrollIntoView({block:'start'})"); await pg.wait_for_timeout(250)
            await pg.mouse.move(2, 2); await pg.wait_for_timeout(250)
            path = root.parent / f"evt-{vid}.png"; await pg.screenshot(path=str(path)); shots.append(path)
        print("errors:", errs)
        await b.close()
try:
    asyncio.run(run())
finally:
    srv.terminate()
ims = [Image.open(s) for s in shots]
h = 760; ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
s = Image.new("RGB", (sum(i.width for i in ims) + 10 * (len(ims) + 1), h + 20), (60, 60, 60))
x = 10
for i in ims: s.paste(i, (x, 10)); x += i.width + 10
s.save("art/evt-both.png"); print("saved", [str(p) for p in shots])
