#!/usr/bin/env python3
"""Проверка «Футы и фунты» в Chromium: вкладки, скрытые ответы, контекст, раунд тренировки (с ошибкой и повтором),
интервалы повторения, ширины 320–1180 и крупный текст: без сдвига вбок, обрезки и переносов внутри слов.
Запуск из корня репозитория: python3 edinitsy/tools/test.py [папка для скриншотов]"""
import functools, http.server, json, pathlib, re, sys, threading
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tools" / "shots"
OUT.mkdir(parents=True, exist_ok=True)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
fails, errors = [], []


def check(cond, msg):
    print(("ok  " if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)


def page(b, tab="table", width=390, scale=None, init=""):
    ctx = b.new_context(viewport={"width": width, "height": 844}, locale="ru-RU", device_scale_factor=2)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.add_init_script(f"localStorage.setItem('fut:tab', '{tab}');" + init)
    pg.goto(URL)
    pg.wait_for_selector("#view > *")
    if scale:
        pg.evaluate(f"document.documentElement.style.fontSize = '{scale}'")
    return ctx, pg


LAYOUT = """() => { const out = {bad: [], clip: [], split: []}, range = document.createRange();
  for (const el of document.querySelectorAll('#view *')) { if (el.closest('.chips')) continue; const r = el.getBoundingClientRect();
    if (r.width && (r.right > innerWidth + 1 || r.left < -1)) out.bad.push(el.className + ' ' + Math.round(r.right)); }
  for (const el of document.querySelectorAll('.tab, .btn, .chip, .opt, .row .v, .row .k, .pill, .big, .ans, .qt')) {
    if (!el.getClientRects().length) continue;
    if (el.scrollWidth > el.clientWidth + 1) out.clip.push(el.className + ': ' + el.textContent.trim().slice(0, 20)); }
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let node;
  while ((node = w.nextNode())) { const el = node.parentElement;
    if (!el || el.closest('script, style, [hidden], .chips') || !el.getClientRects().length) continue;
    const re = /[A-Za-zА-Яа-яЁё0-9]{2,}/g; let m;
    while ((m = re.exec(node.textContent))) { range.setStart(node, m.index); range.setEnd(node, m.index + m[0].length);
      if (new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.bottom))).size > 1) out.split.push(m[0]); } }
  out.doc = document.documentElement.scrollWidth > innerWidth || document.querySelector('main').scrollWidth > document.querySelector('main').clientWidth;
  for (const k of ['bad', 'clip', 'split']) out[k] = out[k].slice(0, 5);
  return out; }"""

with sync_playwright() as p:
    b = p.chromium.launch()
    # Таблица
    ctx, pg = page(b, "table")
    n_rows = pg.locator(".row").count()
    check(n_rows == 39, f"в таблице все единицы: {n_rows}")
    foot = pg.locator('.row[data-id="foot"]').inner_text().replace("\xa0", " ")
    check("1 фут" in foot and "30,48 см" in foot and "0,3048 м" in foot, f"фут: {foot!r}")
    check("453,6 г" in pg.locator('.row[data-id="lb"]').inner_text().replace("\xa0", " "), "фунт — 453,6 г")
    pg.screenshot(path=str(OUT / "u1-table.png"))
    pg.click('.toggle[data-act="cover"]')
    check(pg.locator(".row.cover").count() == 39, "«Скрыть ответы» прячет все ответы")
    pg.click('.row[data-id="mile"]')
    check(pg.locator(".row.cover").count() == 38 and "4 круга" in pg.locator('.row[data-id="mile"]').inner_text().replace("\xa0", " "), "нажатие открывает ответ и подсказку")
    pg.click('.chip[data-g="temp"]')
    check(pg.locator(".row").count() == 4, "фильтр «Температура»: 4 строки")
    ctx.close()
    # В контексте
    ctx, pg = page(b, "ctx")
    check(pg.locator(".scene").count() == 39 and pg.locator(".scene .ans").count() == 0, "в контексте — 39 ситуаций, ответы скрыты")
    pg.click('.scene[data-id="foot"]')
    t = pg.locator('.scene[data-id="foot"]').inner_text().replace("\xa0", " ")
    check("Рост 6 футов" in t and "≈ 1,83 м" in t and "6 × 30,48 = 182,9 см" in t, f"рост 6 футов → 1,83 м: {t!r}")
    pg.screenshot(path=str(OUT / "u2-ctx.png"))
    pg.click('.toggle[data-act="all"]')
    check(pg.locator(".scene .ans").count() == 39, "«Показать все ответы»")
    ctx.close()
    # Тренировка: раунд, одна ошибка → повтор в конце, интервалы
    ctx, pg = page(b, "train")
    check("из 78" in pg.inner_text("#view"), "в тренировке 78 карточек")
    pg.click('[data-act="start"]')
    first_wrong = True
    asked = 0
    while pg.locator(".opt").count():
        q = pg.locator(".qt").inner_text()
        ans = pg.evaluate("() => round.qs[round.i].c.a")
        opts = pg.eval_on_selector_all(".opt", "els => els.map(e => e.textContent.replace(/\\u00a0/g, ' '))")
        ans = ans.replace("\xa0", " ")
        check(len(opts) == 4 and len(set(opts)) == 4 and ans in opts, f"вопрос «{q[:40]}»: 4 разных варианта, верный среди них") if asked < 3 else None
        k = opts.index(ans)
        if first_wrong:
            k = (k + 1) % 4
        pg.locator(".opt").nth(k).click()
        if asked == 0:
            pg.screenshot(path=str(OUT / "u3-train.png"))
        first_wrong = False
        pg.click('[data-act="next"]')
        asked += 1
        if asked > 20:
            break
    end = pg.inner_text("#view").replace("\xa0", " ")
    check(asked == 11 and "9 из 10 с первого раза" in end and "Повторите" in end, f"раунд: 11 вопросов (ошибка повторена), итог 9 из 10 — {asked}")
    srs = json.loads(pg.evaluate("localStorage.getItem('fut:srs')"))
    check(len(srs) == 10 and sum(1 for v in srs.values() if v["b"] == 1) == 10, "все 10 карточек в интервалах (ошибочная — после повтора)")
    pg.screenshot(path=str(OUT / "u4-end.png"))
    pg.click('[data-act="stop"]')
    ctx.close()
    # Ширины и крупный текст
    for scale in (None, "120.75%", "147%"):
        for w in (320, 375, 390, 430, 820, 1180):
            for tab in ("table", "ctx", "train"):
                ctx, pg = page(b, tab, w, scale, "localStorage.setItem('fut:cover', '0');")
                if tab == "ctx":
                    pg.click('.toggle[data-act="all"]')
                if tab == "table":
                    pg.click('.row[data-id="acre"]')
                r = pg.evaluate(LAYOUT)
                check(not r["doc"] and not r["bad"] and not r["clip"] and not r["split"],
                      f"{w}px {tab}{' ×' + scale if scale else ''}: помещается {r['bad'] or ''}{r['clip'] or ''}{r['split'] or ''}")
                if tab == "train":
                    pg.click('[data-act="start"]')
                    for _ in range(3):
                        pg.locator(".opt").first.click()
                        r = pg.evaluate(LAYOUT)
                        check(not r["doc"] and not r["bad"] and not r["clip"] and not r["split"],
                              f"{w}px вопрос{' ×' + scale if scale else ''}: помещается {r['bad'] or ''}{r['clip'] or ''}{r['split'] or ''}")
                        pg.click('[data-act="next"]')
                if w == 320 and not scale:
                    pg.screenshot(path=str(OUT / f"u-w320-{tab}.png"))
                ctx.close()
    b.close()
check(not errors, f"ошибок JS нет {errors[:3]}")
srv.shutdown()
print("ПРОВАЛОВ:", len(fails))
sys.exit(1 if fails else 0)
