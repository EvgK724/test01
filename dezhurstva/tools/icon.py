#!/usr/bin/env python3
"""Иконка: неоновый календарь с «+» на тёмном фоне → icon-512.png, icon-192.png, icon-180.png (Playwright)."""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
<defs>
 <radialGradient id="bg" cx="30%" cy="20%" r="95%"><stop offset="0" stop-color="#2A0F2E"/><stop offset=".55" stop-color="#0B0B16"/><stop offset="1" stop-color="#06060B"/></radialGradient>
 <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 <filter id="glow2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="12" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="512" height="512" fill="url(#bg)"/>
<g filter="url(#glow)" fill="none" stroke="#3BE8FF" stroke-width="16" stroke-linecap="round" stroke-linejoin="round">
 <rect x="104" y="128" width="304" height="276" rx="44"/>
 <path d="M104 204h304M184 92v68M328 92v68"/>
</g>
<g filter="url(#glow2)" stroke="#FF4FD8" stroke-width="28" stroke-linecap="round">
 <path d="M256 250v112M200 306h112"/>
</g>
</svg>"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 512, "height": 512})
        pg.set_content(f"<html><body style='margin:0;background:#06060B'>{SVG}</body></html>")
        for size in (512, 192, 180):
            pg.set_viewport_size({"width": 512, "height": 512})
            pg.screenshot(path=str(ROOT / f"icon-{size}.png"), clip={"x": 0, "y": 0, "width": 512, "height": 512}, scale="css")
        b.close()
    from PIL import Image
    big = Image.open(ROOT / "icon-512.png").convert("RGB")
    for size in (192, 180):
        big.resize((size, size), Image.LANCZOS).save(ROOT / f"icon-{size}.png", optimize=True)
    big.save(ROOT / "icon-512.png", optimize=True)
    print("→ icon-512.png, icon-192.png, icon-180.png")


if __name__ == "__main__":
    main()
