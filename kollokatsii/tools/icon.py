#!/usr/bin/env python3
"""Иконка: два сцепленных звена (слова, которые «дружат») — золотое и голубое — на тёмно-синем фоне
→ icon-512.png, icon-192.png, icon-180.png (Playwright + Pillow)."""
import pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
<defs>
 <radialGradient id="bg" cx="30%" cy="20%" r="95%"><stop offset="0" stop-color="#0D2350"/><stop offset=".55" stop-color="#080E20"/><stop offset="1" stop-color="#05070F"/></radialGradient>
 <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 <clipPath id="top"><rect x="0" y="0" width="512" height="256"/></clipPath>
</defs>
<rect width="512" height="512" fill="url(#bg)"/>
<g filter="url(#glow)" fill="none" stroke-width="30">
 <rect x="70" y="176" width="230" height="160" rx="80" stroke="#FFC56B"/>
 <rect x="212" y="176" width="230" height="160" rx="80" stroke="#3BE8FF"/>
 <rect x="70" y="176" width="230" height="160" rx="80" stroke="#FFC56B" clip-path="url(#top)"/>
</g>
</svg>"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 512, "height": 512})
        pg.set_content(f"<html><body style='margin:0;background:#05070F'>{SVG}</body></html>")
        pg.screenshot(path=str(ROOT / "icon-512.png"), clip={"x": 0, "y": 0, "width": 512, "height": 512})
        b.close()
    big = Image.open(ROOT / "icon-512.png").convert("RGB")
    for size in (192, 180):
        big.resize((size, size), Image.LANCZOS).save(ROOT / f"icon-{size}.png", optimize=True)
    big.save(ROOT / "icon-512.png", optimize=True)
    print("→ icon-512.png, icon-192.png, icon-180.png")


if __name__ == "__main__":
    main()
