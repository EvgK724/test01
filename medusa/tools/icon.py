#!/usr/bin/env python3
"""Иконка: неоновый горгонейон из самого приложения (функция gorgon()) на тёмном фоне → icon-512.png, icon-192.png, icon-180.png.
Запуск после build.py: python3 medusa/tools/icon.py (Playwright + Pillow)."""
import pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 512, "height": 512})
        pg.goto((ROOT / "index.html").as_uri())
        svg = pg.evaluate("gorgon()")
        pg.set_content("<html><body style='margin:0;width:512px;height:512px;display:grid;place-items:center;"
                       "background:radial-gradient(circle at 50% 42%, #0D2350 0%, #080E20 55%, #04060D 100%)'>"
                       f"<div style='width:440px;height:440px;filter:drop-shadow(0 0 22px rgba(59,232,255,.45))'>{svg}</div></body></html>")
        pg.evaluate("document.querySelector('svg').setAttribute('width', 440); document.querySelector('svg').setAttribute('height', 440)")
        pg.screenshot(path=str(ROOT / "icon-512.png"), clip={"x": 0, "y": 0, "width": 512, "height": 512})
        b.close()
    big = Image.open(ROOT / "icon-512.png").convert("RGB")
    for size in (192, 180):
        big.resize((size, size), Image.LANCZOS).save(ROOT / f"icon-{size}.png", optimize=True)
    big.save(ROOT / "icon-512.png", optimize=True)
    print("→ icon-512.png, icon-192.png, icon-180.png")


if __name__ == "__main__":
    main()
