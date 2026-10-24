#!/usr/bin/env python3
"""Проверка «Медузы Горгоны» в Chromium: данные (главы, толкования, вопросы), главы (раскрытие, версии, «Дальше», прочитано,
переход к толкованию), фильтры толкований и следа, раунд тренировки с ошибкой и повтором, телефоны 320–440 и iPad
(портрет и альбом) с обычным и крупным текстом: без сдвига вбок, обрезки и переносов внутри слов.
Запуск из корня репозитория: python3 medusa/tools/test.py [папка для скриншотов]"""
import functools, http.server, pathlib, sys, threading
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


def page(b, tab="life", width=390, height=844, scale=None, init="", insets=None):
    ctx = b.new_context(viewport={"width": width, "height": height}, locale="ru-RU", device_scale_factor=2, is_mobile=width < 700, has_touch=True)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    if insets:
        ctx.new_cdp_session(pg).send("Emulation.setSafeAreaInsetsOverride", {"insets": {"top": insets[0], "bottom": insets[1], "left": 0, "right": 0}})
    pg.add_init_script(f"localStorage.setItem('medusa:tab', '{tab}');" + init)
    pg.goto(URL)
    pg.wait_for_selector("#view > *")
    if scale:  # крупный текст телефона: как applyTextSize(), с множителем iPad
        pg.evaluate(f"document.documentElement.style.fontSize = (110 * Math.min({scale} * deviceK(), 2.2)).toFixed(2) + '%'; render(true)")
    return ctx, pg


LAYOUT = """() => { const out = {bad: [], clip: [], split: []}, range = document.createRange();
  for (const el of document.getElementById('view').querySelectorAll('*')) { if (el.closest('.chips')) continue; const r = el.getBoundingClientRect();
    if (r.width && (r.right > innerWidth + 1 || r.left < -1)) out.bad.push(el.className + ' ' + Math.round(r.left) + '…' + Math.round(r.right)); }
  for (const el of document.querySelectorAll('.tab, .btn, .chip, .opt, .step, .vs-sw button, .pill, .st, .src')) {
    if (!el.getClientRects().length || el.closest('[hidden]')) continue;
    if (el.scrollWidth > el.clientWidth + 1) out.clip.push(el.className + ': ' + el.textContent.trim().slice(0, 24)); }
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let node;
  while ((node = w.nextNode())) { const el = node.parentElement;
    if (!el || el.closest('script, style, [hidden], .chips, svg') || !el.getClientRects().length) continue;
    const re = /[A-Za-zА-Яа-яЁё0-9]{2,}/g; let m;
    while ((m = re.exec(node.textContent))) { range.setStart(node, m.index); range.setEnd(node, m.index + m[0].length);
      if (new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.bottom))).size > 1) out.split.push(m[0]); } }
  out.doc = document.documentElement.scrollWidth > innerWidth || document.querySelector('main').scrollWidth > document.querySelector('main').clientWidth;
  for (const k of ['bad', 'clip', 'split']) out[k] = out[k].slice(0, 5);
  return out; }"""


def fits(pg, label):
    r = pg.evaluate(LAYOUT)
    check(not r["doc"] and not r["bad"] and not r["clip"] and not r["split"], f"{label}: помещается {r['bad'] or ''}{r['clip'] or ''}{r['split'] or ''}")


def open_all(pg):
    """Раскрыть главы по очереди и проверить вёрстку каждой (раскрыта всегда одна)."""
    for cid in pg.evaluate("CH.map(c => c.id)"):
        pg.evaluate(f"state.open = '{cid}'; render(true)")
        yield cid


with sync_playwright() as p:
    b = p.chromium.launch()

    # ——— Данные
    ctx, pg = page(b)
    d = pg.evaluate("""() => ({ ch: CH.length, views: VIEWS.length, leg: LEG.length, q: Q.length,
      badView: CH.filter(c => c.view && !VBY[c.view]).map(c => c.id),
      badQ: Q.filter(q => q.o.length !== 4 || !(q.a >= 0 && q.a < 4) || new Set(q.o).size !== 4 || !['life', 'views', 'legacy'].includes(q.s)).map(q => q.id),
      dupQ: Q.length - new Set(Q.map(q => q.id)).size, dupCh: CH.length - new Set(CH.map(c => c.id)).size,
      badVG: VIEWS.filter(v => !D.VG.some(g => g.id === v.g)).map(v => v.id), badLG: LEG.filter(x => !D.LG.some(g => g.id === x.g)).map(x => x.t),
      noSrc: CH.filter(c => !c.src || !c.src.length).map(c => c.id) })""")
    check(d["ch"] == 10 and d["views"] >= 12 and d["leg"] >= 20 and d["q"] >= 50, f"данные: {d['ch']} глав, {d['views']} толкований, {d['leg']} вех, {d['q']} вопросов")
    check(not d["badView"] and not d["badQ"] and not d["dupQ"] and not d["dupCh"] and not d["badVG"] and not d["badLG"] and not d["noSrc"], f"ссылки и вопросы целы {d}")
    secs = pg.evaluate("[pool('life').length, pool('views').length, pool('legacy').length]")
    check(all(n >= 10 for n in secs), f"в каждом разделе тренировки не меньше 10 вопросов {secs}")

    # ——— Жизнь: герой, главы
    check(pg.locator(".hero svg").count() == 1 and pg.locator(".ch").count() == 10, "герой с горгонейоном и 10 глав")
    pg.screenshot(path=str(OUT / "life.png"))
    pg.locator(".ch-h").first.click()
    check(pg.locator("#ch-rod .ch-b").count() == 1 and pg.locator("#ch-rod .tree li").count() >= 8, "глава I раскрыта, в ней родословная")
    check("Прочитано 1 из 10" in pg.inner_text(".hero"), "прочитано 1 из 10")
    pg.locator("#ch-rod [data-act=vs][data-k=b]").click()
    check("Флеграх" in pg.inner_text("#ch-rod .ch-b"), "версия Еврипида переключается")
    pg.locator("#ch-rod .btn.primary").click()
    check(pg.locator("#ch-sisters .ch-b").count() == 1 and pg.locator("#ch-rod .ch-b").count() == 0, "«Дальше» открывает главу II и закрывает I")
    pg.screenshot(path=str(OUT / "chapter.png"))
    pg.evaluate("state.open = 'beauty'; render(true)")
    pg.locator("#ch-beauty [data-act=toview]").click()
    pg.wait_for_timeout(300)
    check(pg.evaluate("state.tab") == "views" and pg.locator("#vw-cixous").count() == 1, "переход к толкованию (Сиксу)")
    ctx.close()
    ctx, pg = page(b, init="localStorage.setItem('medusa:read', JSON.stringify(['rod','sisters','beauty']));")
    check("Прочитано 3 из 10" in pg.inner_text(".hero") and pg.locator(".step.read").count() == 3, "прочитанное сохраняется")
    ctx.close()

    # ——— Толкования и след
    ctx, pg = page(b, tab="views")
    n_all = pg.locator(".vw").count()
    pg.locator("[data-act=vg][data-v=authors]").click()
    v = pg.inner_text("#view")
    check(pg.locator(".vw").count() == 3 and all(n in v for n in ("Голосовкер", "Гаубец", "Грейвс")), f"фильтр «Доолимпийская Медуза»: Голосовкер, Гаубец, Грейвс (всего {n_all})")
    pg.screenshot(path=str(OUT / "views.png"))
    pg.locator(".tab[data-tab=legacy]").click()
    years = pg.evaluate("[...document.querySelectorAll('.lg li')].length")
    pg.locator("[data-act=lg][data-v=sci]").click()
    check(pg.locator(".lg li").count() == 4 and "Caput medusae" in pg.inner_text("#view"), f"след: {years} вех, фильтр «Наука и медицина»")
    pg.locator("[data-act=lg][data-v=byz]").click()
    check("Смедерево" in pg.inner_text("#view"), "след: Медуза в стенах сербских церквей")
    pg.screenshot(path=str(OUT / "legacy.png"))
    ctx.close()

    # ——— Тренировка: раунд с ошибкой
    ctx, pg = page(b, tab="train")
    pg.locator("[data-act=start]").click()
    check(pg.evaluate("round.qs.length") == 10, "в раунде 10 вопросов")
    wrong = pg.evaluate("round.qs[0].opts.findIndex(o => o !== round.qs[0].a)")
    pg.locator(".opt").nth(wrong).click()
    check(pg.locator(".fb.bad").count() == 1 and pg.evaluate("round.qs.length") == 11, "ошибка: подсказка и повтор в конце раунда")
    pg.screenshot(path=str(OUT / "train-wrong.png"))
    for _ in range(12):
        if pg.evaluate("round.i >= round.qs.length"):
            break
        if pg.evaluate("round.pick == null"):
            k = pg.evaluate("round.qs[round.i].opts.indexOf(round.qs[round.i].a)")
            pg.locator(".opt").nth(k).click()
        pg.locator("[data-act=next]").click()
    txt = pg.text_content("#view")   # text_content: у заголовков text-transform: uppercase
    check("Раунд окончен" in txt and "9" in txt, "раунд окончен: 9 из 10 с первого раза, ошибка в «Повторите»")
    srs = pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('medusa:srs'))).length")
    check(srs == 10, f"прогресс сохранён по 10 вопросам ({srs})")
    pg.locator("[data-act=stop]").click()
    check("Знаю" in pg.text_content("#view"), "назад к прогрессу")
    ctx.close()

    # ——— Вёрстка: телефоны и iPad, обычный и крупный текст
    sizes = [(320, 640), (375, 812), (390, 844), (430, 932), (440, 956), (820, 1180), (1180, 820)]
    for w, h in sizes:
        for scale in (None, 1.35):
            lab = f"{w}×{h}{' ×1.35' if scale else ''}"
            for tab in ("life", "views", "legacy", "train"):
                ctx, pg = page(b, tab=tab, width=w, height=h, scale=scale, insets=(62, 34) if w == 440 else None)
                if tab == "life":
                    bad = []
                    for cid in open_all(pg):
                        r = pg.evaluate(LAYOUT)
                        if r["doc"] or r["bad"] or r["clip"] or r["split"]:
                            bad.append((cid, r["bad"][:1] + r["clip"][:1] + r["split"][:2]))
                    check(not bad, f"{lab} все главы: помещаются {bad[:2]}")
                elif tab == "train":
                    pg.locator("[data-act=start]").click()
                    worst = []
                    for i in range(pg.evaluate("Q.length")):
                        pg.evaluate(f"round.qs = [mkQ(Q[{i}])]; round.i = 0; round.pick = null; render(true)")
                        r = pg.evaluate(LAYOUT)
                        if r["doc"] or r["bad"] or r["clip"] or r["split"]:
                            worst.append((pg.evaluate(f"Q[{i}].id"), r["clip"][:1] + r["split"][:2]))
                    check(not worst, f"{lab} все вопросы: помещаются {worst[:2]}")
                else:
                    fits(pg, f"{lab} {tab}")
                if w in (320, 440, 1180) and not scale:
                    pg.screenshot(path=str(OUT / f"w{w}-{tab}.png"))
                ctx.close()

    # Прокрутка до краёв: шапка уезжает, меню плавает поверх, последний блок поднимается выше меню
    ctx, pg = page(b, width=440, height=956, insets=(62, 34))
    r = pg.evaluate("""() => { main.scrollTop = 1e6; const t = document.querySelector('nav.tabs').getBoundingClientRect(), last = view.lastElementChild.getBoundingClientRect(), m = main.getBoundingClientRect();
      return { mainTop: m.top, mainBottom: m.bottom, ih: innerHeight, lastBottom: Math.round(last.bottom), menuTop: Math.round(t.top) }; }""")
    check(r["mainTop"] == 0 and r["mainBottom"] == r["ih"] and r["lastBottom"] <= r["menuTop"], f"экран от края до края, последний блок выше меню {r}")
    ctx.close()
    b.close()

print("ошибок JS нет" if not errors else f"ОШИБКИ JS: {errors[:5]}")
print("ПРОВАЛОВ:", len(fails) + (1 if errors else 0))
sys.exit(1 if fails or errors else 0)
