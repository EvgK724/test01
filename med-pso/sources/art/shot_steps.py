import asyncio, pathlib, subprocess, sys, time
from playwright.async_api import async_playwright
from PIL import Image
root = pathlib.Path("art/site").resolve()
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8865", "--bind", "127.0.0.1"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await (await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)).new_page()
        await pg.goto("http://127.0.0.1:8865/"); await pg.wait_for_timeout(900)
        await pg.click("#evtTog"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('evtLegend').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(root.parent / "st-legend.png"))
        await pg.evaluate("document.querySelector('.steps').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(root.parent / "st-steps.png"))
        await b.close()
try:
    asyncio.run(run())
finally:
    srv.terminate()
a = Image.open("art/st-legend.png"); c = Image.open("art/st-steps.png")
h = 760; a = a.resize((int(a.width * h / a.height), h)); c = c.resize((int(c.width * h / c.height), h))
s = Image.new("RGB", (a.width + c.width + 30, h + 20), (60, 60, 60)); s.paste(a, (10, 10)); s.paste(c, (a.width + 20, 10)); s.save("art/st-both.png")
