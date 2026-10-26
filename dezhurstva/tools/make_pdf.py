#!/usr/bin/env python3
"""PDF графика для печати — лист A4 альбомом, тот же, что рисует printSheet() в собранной index.html (Chromium через Playwright).
files/<месяц>.pdf — без телефонов; files/<месяц>-print.pdf — заготовка «для печати»: «Врач, телефон» и пустое место
под номер у каждой фамилии. Где это место, возвращает render(): {id: [x, y, ширина]} в пунктах PDF от левого верхнего угла,
y — базовая линия (Chromium округляет размер листа, поэтому от низа считает приложение — по настоящей высоте страницы).
Номера вписывает приложение на телефоне организатора (vendor/pdf-lib.min.js) — в файлы они не попадают.
Вызывает build.py; отдельно: python3 dezhurstva/tools/make_pdf.py 2026-11"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PX = 0.75   # 1 CSS px = 0,75 пт: Chromium печатает 96 px на дюйм

CSS = """() => [...document.styleSheets].flatMap(s => [...s.cssRules])
  .filter(r => r.selectorText && r.selectorText.startsWith('.pv')).map(r => r.cssText).join('\\n')"""
SLOTS = """() => Object.fromEntries([...document.querySelectorAll('.pv .slot')].map(s => {
  const r = s.getBoundingClientRect(), b = s.querySelector('i').getBoundingClientRect();
  return [s.dataset.id, [r.left, b.top, r.width]];
}))"""


def render(months, root=ROOT):
    from playwright.sync_api import sync_playwright
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        app = browser.new_page()
        app.goto((root / "index.html").as_uri())
        css = app.evaluate(CSS)
        sheet = browser.new_page(viewport={"width": 1123, "height": 794})
        for mk in months:
            for slots in (False, True):
                title, body = app.evaluate("([mk, s]) => ['График дежурств ПСО — ' + monthTitle(mk).toLowerCase(), printSheet(mk, s)]", [mk, slots])
                sheet.set_content(f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>{title}</title>'
                                  f'<style>@page {{ size: 297mm 210mm; margin: 0; }} html, body {{ margin: 0; }}\n{css}</style></head>'
                                  f'<body>{body}</body></html>')
                sheet.pdf(path=str(root / "files" / f"{mk}{'-print' if slots else ''}.pdf"), width="297mm", height="210mm",
                          print_background=True, prefer_css_page_size=True)
                if slots:
                    out[mk] = {k: [round(x * PX, 1), round(y * PX, 1), round(w * PX, 1)]
                               for k, (x, y, w) in sheet.evaluate(SLOTS).items()}
        browser.close()
    return out


if __name__ == "__main__":
    print(json.dumps(render(sys.argv[1:]), ensure_ascii=False))
