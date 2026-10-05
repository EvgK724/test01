import asyncio, pathlib, sys
sys.path.insert(0, "art")
from views import VIEWS_SVG
from playwright.async_api import async_playwright
css = pathlib.Path("art/atlas.css").read_text()
def page(evt, hl):
    cells = "".join(f'<div class="cell{" evt" if evt else ""}"><p>{k}</p>{v}</div>' for k, v in VIEWS_SVG.items())
    js = "".join(f"document.querySelectorAll('[data-seg=\"{h}\"]').forEach(n=>n.classList.add('on'));" for h in hl)
    return f"""<html><body style="margin:0;background:#0e1113;color:#e8e8e8;font-family:sans-serif">
<style>{css} .grid{{display:grid;grid-template-columns:repeat(3,360px);gap:20px;padding:20px}} .cell{{background:#171c1f;border-radius:16px;padding:10px}} p{{margin:0 0 6px;color:#7cc0dd}}</style>
<div class="grid">{cells}</div><script>{js}</script></body></html>"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1180, "height": 900}, device_scale_factor=1.5)
        for name, evt, hl in [("plain", False, []), ("evt", True, ["m1"]), ("hl", False, ["m2", "c4", "mca", "am2", "ba", "v4"])]:
            pathlib.Path("art/pv.html").write_text(page(evt, hl))
            await pg.goto("file://" + str(pathlib.Path("art/pv.html").resolve()))
            await pg.wait_for_timeout(200)
            await pg.screenshot(path=f"art/views-{name}.png", full_page=True)
        await b.close()
asyncio.run(main())
print("ok")
