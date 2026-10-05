import asyncio, pathlib, subprocess, sys, time
from playwright.async_api import async_playwright
from PIL import Image
root = pathlib.Path("ctp").resolve()
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8857", "--bind", "127.0.0.1"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
IDS = ["p4-hir", "p6-guideline", "p7-old", "p1-trunc", "p5-early", "p2-relative"]
async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        paths = []
        for w, h in [(390, 800), (360, 740)]:
            ctx = await b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
            pg = await ctx.new_page()
            await pg.goto("http://127.0.0.1:8857/preview.html"); await pg.wait_for_timeout(300)
            await pg.click("#tabDrill")
            for cid in IDS:
                await pg.evaluate(f"queue = [CARDS.find(c => c.id === '{cid}')]; index = 0; mode = 'topic'; topicN = queue[0].t; render();"); await pg.wait_for_timeout(80)
                path = root / f"c-{w}-{cid}.png"; await pg.screenshot(path=str(path)); paths.append(path)
            await pg.click("#tabRule"); await pg.wait_for_timeout(100)
            path = root / f"c-{w}-rule.png"; await pg.screenshot(path=str(path)); paths.append(path)
            await ctx.close()
        await b.close()
    ims = [Image.open(p) for p in paths]
    H = 560; ims = [im.resize((int(im.width * H / im.height), H)) for im in ims]
    rows = [ims[:7], ims[7:]]
    W = max(sum(i.width for i in r) + 10 * (len(r) + 1) for r in rows)
    sheet = Image.new("RGB", (W, 2 * (H + 10) + 10), (60, 60, 60))
    y = 10
    for r in rows:
        x = 10
        for im in r: sheet.paste(im, (x, y)); x += im.width + 10
        y += H + 10
    sheet.save(root / "cards.png")
try:
    asyncio.run(run())
finally:
    srv.terminate()
print("ok")
