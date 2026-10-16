#!/usr/bin/env python3
"""Иконка: три неоновые полосы жизни на общей шкале и вертикальная линия года → icon-512.png, icon-192.png, icon-180.png (Playwright + Pillow)."""
import pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
<defs>
 <radialGradient id="bg" cx="30%" cy="20%" r="95%"><stop offset="0" stop-color="#0D2350"/><stop offset=".55" stop-color="#080E20"/><stop offset="1" stop-color="#05070F"/></radialGradient>
 <linearGradient id="bar" x1="0" x2="1"><stop offset="0" stop-color="#3D8BFF"/><stop offset="1" stop-color="#3BE8FF"/></linearGradient>
 <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="512" height="512" fill="url(#bg)"/>
<g stroke="#1E3766" stroke-width="3"><path d="M128 80v352M224 80v352M320 80v352M416 80v352"/></g>
<g filter="url(#glow)" stroke="url(#bar)" stroke-width="38" stroke-linecap="round" fill="none">
 <path d="M86 170h210"/><path d="M196 262h232"/><path d="M128 354h176"/>
</g>
<g filter="url(#glow)"><path d="M264 92v330" stroke="#EFFFFF" stroke-width="9" stroke-linecap="round"/>
 <rect x="248" y="72" width="32" height="32" rx="4" transform="rotate(45 264 88)" fill="#EFFFFF"/></g>
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
