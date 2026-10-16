#!/usr/bin/env python3
"""Проверка «Современников» в Chromium: лента и карточка человека (совпадения, события при жизни, подсветка), год (кто жив,
возраст, до н. э., пустой год), пара (одновременно / разминулись), генератор вопросов для всех людей, раунд тренировки
(с ошибкой и повтором), телефоны 320–430 и iPad (портрет и альбом) с обычным и крупным текстом: без сдвига вбок,
обрезки и переносов внутри слов. Запуск из корня репозитория: python3 sovremenniki/tools/test.py [папка для скриншотов]"""
import functools, http.server, json, pathlib, sys, threading
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


def page(b, tab="feed", width=390, scale=None, init="", height=844):
    ctx = b.new_context(viewport={"width": width, "height": height}, locale="ru-RU", device_scale_factor=2)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.add_init_script(f"localStorage.setItem('sovr:tab', '{tab}');" + init)
    pg.goto(URL)
    pg.wait_for_selector("#view > *")
    if scale:  # крупный текст телефона: как applyTextSize(), с множителем iPad
        pg.evaluate(f"document.documentElement.style.fontSize = (105 * Math.min({scale} * deviceK(), 2.2)).toFixed(2) + '%'; render(true)")
    return ctx, pg


def text(pg, sel):
    return pg.inner_text(sel).replace("\xa0", " ")


LAYOUT = """() => { const out = {bad: [], clip: [], split: []}, range = document.createRange();
  const roots = [document.getElementById('view')]; if (!document.getElementById('pers').hidden) roots.push(document.getElementById('persPanel'));
  for (const root of roots) for (const el of root.querySelectorAll('*')) { if (el.closest('.chips')) continue; const r = el.getBoundingClientRect();
    if (r.width && (r.right > innerWidth + 1 || r.left < -1)) out.bad.push(el.className + ' ' + Math.round(r.left) + '…' + Math.round(r.right)); }
  for (const el of document.querySelectorAll('.tab, .btn, .chip, .opt, .pill, .big, .yin, .pchip, .slot, .tyy')) {
    if (!el.getClientRects().length || el.closest('[hidden]')) continue;
    if (el.scrollWidth > el.clientWidth + 1) out.clip.push(el.className + ': ' + el.textContent.trim().slice(0, 24)); }
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let node;
  while ((node = w.nextNode())) { const el = node.parentElement;
    if (!el || el.closest('script, style, [hidden], .chips, select') || !el.getClientRects().length) continue;
    const re = /[A-Za-zА-Яа-яЁё0-9]{2,}/g; let m;
    while ((m = re.exec(node.textContent))) { range.setStart(node, m.index); range.setEnd(node, m.index + m[0].length);
      if (new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.bottom))).size > 1) out.split.push(m[0]); } }
  out.doc = document.documentElement.scrollWidth > innerWidth || document.querySelector('main').scrollWidth > document.querySelector('main').clientWidth
    || (!document.getElementById('pers').hidden && document.getElementById('persPanel').scrollWidth > document.getElementById('persPanel').clientWidth);
  for (const k of ['bad', 'clip', 'split']) out[k] = out[k].slice(0, 5);
  return out; }"""


def fits(pg, label):
    r = pg.evaluate(LAYOUT)
    check(not r["doc"] and not r["bad"] and not r["clip"] and not r["split"], f"{label}: помещается {r['bad'] or ''}{r['clip'] or ''}{r['split'] or ''}")


with sync_playwright() as p:
    b = p.chromium.launch()
    # Данные: у каждого — событие его времени
    ctx, pg = page(b)
    bad = pg.evaluate("() => P.filter(p => !EV[p.e] || !evIn(p, EV[p.e])).map(p => p.id)")
    check(pg.evaluate("P.length") == 94 and not bad, f"94 человека, у каждого событие при жизни {bad}")
    # Лента
    n_ren = pg.evaluate("P.filter(p => p.era === 'ren').length")
    check(pg.locator(".tr.p").count() == n_ren and pg.locator(".tr.ev").count() == 0, f"Возрождение: {n_ren} человек, событий отдельно нет")
    leo = text(pg, '.tr.p[data-id="leonardo"]')
    check("1452 – 1519" in leo and "1492 — Колумб открыл Америку" in leo, f"строка Леонардо: {leo!r}")
    pg.screenshot(path=str(OUT / "s1-feed.png"))
    pg.click('.chip[data-act="era"][data-v=""]')
    check(pg.locator(".tr.p").count() == 94, "«Все» — 94 человека")
    pg.click('.toggle[data-act="ev"]')
    check(pg.locator(".tr.ev").count() > 90, f"«Все события» — строки событий: {pg.locator('.tr.ev').count()}")
    pg.click('.toggle[data-act="ev"]')
    pg.click('.chip[data-act="era"][data-v="ren"]')
    # Карточка человека
    pg.click('.tr.p[data-id="leonardo"]')
    t = text(pg, "#persPanel")
    check("1452 – 1519" in t and "прожил 67 лет" in t and "1492 — Колумб открыл Америку (ему 40 лет)" in t and "Христофор Колумб" in t,
          "Леонардо: годы, прожил 67, событие и возраст, ровесник Колумб")
    check("1519 – 1522 — первое кругосветное плавание · 67 лет" in t and "за 72 года до рождения" in t, "при жизни и до рождения — с возрастом")
    pg.screenshot(path=str(OUT / "s2-person.png"))
    pg.click('#persPanel [data-act="close"]')
    check(pg.locator(".band").count() == 1 and pg.locator(".tr.p.on").count() == 1 and "Подсвечены годы" in text(pg, "#view"), "годы Леонардо подсвечены на ленте")
    pg.click('#persPanel [data-act="close"]') if pg.is_visible("#pers") else None
    pg.click('.tr.p[data-id="michelangelo"]')
    t = text(pg, "#persPanel")
    check("В год его смерти родились" in t and "Уильям Шекспир" in t and "Галилео Галилей" in t and "В тот же год умер" in t and "Андреас Везалий" in t,
          "Микеланджело: в год смерти родились Шекспир и Галилей, в тот же год умер Везалий")
    pg.click('#persPanel .pchip[data-id="raphael"]')
    check("Рафаэль Санти" in text(pg, "#pTitle"), "переход к современнику")
    pg.click('#persPanel .tr.ev[data-y="1503"]')
    check(pg.is_hidden("#pers") and pg.evaluate("state.tab") == "year" and pg.input_value("#yin") == "1503", "событие в карточке → «Год» 1503")
    pg.click('.tab[data-tab="feed"]')
    pg.click('[data-act="unfocus"]')
    check(pg.locator(".band").count() == 0, "подсветку можно убрать")
    pg.evaluate("openPerson('pushkin')")
    t = text(pg, "#persPanel")
    check("прожил 37 лет" in t and "В год его рождения умер" in t and "Джордж Вашингтон" in t, "Пушкин: прожил 37, в год рождения умер Вашингтон")
    pg.evaluate("openPerson('curie')")
    check("прожила 66 лет" in text(pg, "#persPanel") and "(ей " in text(pg, "#persPanel"), "Склодовская-Кюри: прожила, ей")
    ctx.close()
    # Год
    ctx, pg = page(b, "year")
    pg.click('.chip[data-act="year"][data-y="1519"]')
    t = text(pg, "#yres")
    check("Леонардо да Винчи" in t and "умер в этом году, 67 лет" in t and "Микеланджело" in t and "44 года" in t
          and "Первое кругосветное плавание" in t and "Уильям Шекспир" not in t, "1519: умер Леонардо (67), Микеланджело — 44, кругосветка")
    pg.screenshot(path=str(OUT / "s3-year.png"))
    pg.click('[data-act="ystep"][data-k="1"]')
    check(pg.input_value("#yin") == "1520" and "Рафаэль Санти" in text(pg, "#yres") and "умер в этом году, 37 лет" in text(pg, "#yres"), "+1 → 1520: умер Рафаэль (37)")
    pg.click('.chip[data-act="year"][data-y="-44"]')
    t = text(pg, "#yres")
    check("В 44 году до н. э." in t and "Юлий Цезарь" in t and "умер в этом году, 55 лет" in t and "Клеопатра" in t and "25 лет" in t, "44 до н. э.: Цезарь (55), Клеопатре 25")
    pg.fill("#yin", "1812"); pg.press("#yin", "Enter")
    yv = pg.evaluate("state.year")
    check(yv == -1812, f"ввод при нажатом «до н. э.» → {yv}")
    pg.click("#ybc")
    t = text(pg, "#yres")
    check(pg.evaluate("state.year") == 1812 and "Отечественная война, Бородино" in t and "Александр Пушкин" in t and "13 лет" in t, "1812: Бородино, Пушкину 13")
    pg.click('[data-act="ystep"][data-k="-100"]')
    pg.evaluate("setYear(600)")
    t = text(pg, "#yres")
    check("Никого из списка нет в живых" in t and "Гален" in t and "Карл Великий" in t, "600 год: никого, ближайшие — Гален и Карл Великий")
    pg.evaluate("const r = document.getElementById('yr'); r.value = 0; r.dispatchEvent(new Event('input', {bubbles: true}))")
    check(pg.evaluate("state.year") == -1, "нулевого года нет: 1 → 1 до н. э.")
    pg.evaluate("const r = document.getElementById('yr'); r.value = 1564; r.dispatchEvent(new Event('input', {bubbles: true}))")
    check("Микеланджело" in text(pg, "#yres") and "Уильям Шекспир" in text(pg, "#yres") and pg.input_value("#yin") == "1564", "ползунок → 1564")
    ctx.close()
    # Пара
    ctx, pg = page(b, "pair")
    t = text(pg, "#view")
    check("Жили одновременно" in t and "22 года: 1799 – 1821" in t and "Наполеон Бонапарт — на 30 лет" in t
          and "1799 — родился Александр Пушкин" in t and "Наполеон Бонапарт — 30 лет в этом году" in t
          and "1821 — умер Наполеон Бонапарт" in t and "Александр Пушкин — 22 года в этом году" in t, "Наполеон и Пушкин: 22 года вместе, возраст")
    check(pg.locator(".band").count() == 1 and "Отечественная война, Бородино" in t, "общая полоса и события, когда оба живы")
    pg.screenshot(path=str(OUT / "s4-pair.png"))
    pg.select_option('select[data-sel="pa"]', "leonardo"); pg.select_option('select[data-sel="pb"]', "shakespeare")
    t = text(pg, "#view")
    check("Разминулись" in t and "на 45 лет" in t and pg.locator(".band").count() == 0, "Леонардо и Шекспир разминулись на 45 лет")
    pg.click('[data-act="swap"]')
    check(pg.evaluate("[state.pa, state.pb]") == ["shakespeare", "leonardo"], "поменять местами")
    pg.select_option('select[data-sel="pb"]', "shakespeare")
    check(pg.evaluate("state.pa !== state.pb"), "один и тот же человек дважды не выбирается")
    pg.click('[data-act="rnd"]')
    check(pg.evaluate("state.pa !== state.pb"), "случайная пара")
    ctx.close()
    # Генератор: все люди × все виды вопросов
    ctx, pg = page(b, "train")
    r = pg.evaluate("""() => { const bad = [], miss = {};
      for (const p of P) for (const t of Object.keys(GEN)) for (let i = 0; i < 6; i++) {
        const q = GEN[t](p);
        if (!q) { miss[t] = (miss[t] || 0) + 1; continue; }
        const n = q.type === 'older' || q.type === 'met' ? 2 : 4;
        if (q.opts.length !== n || new Set(q.opts).size !== n || !q.opts.includes(q.a)) bad.push(p.id + ':' + t + ' ' + JSON.stringify(q.opts));
        if (t === 'ev' && q.opts.some(o => o !== q.a && E.some(e => cap(e.t) === o && evIn(p, e)))) bad.push(p.id + ':ev wrong-inside');
        if (t === 'alive' && q.opts.filter(o => { const x = P.find(z => z.n === o); return alive(x, q.tl.line); }).length !== 1) bad.push(p.id + ':alive');
      }
      return { bad: bad.slice(0, 5), nb: bad.length, miss }; }""")
    check(not r["nb"], f"вопросы: 4 (или 2) разных варианта, верный среди них, неверные события — вне жизни {r['bad']}")
    check(all(r["miss"].get(t, 0) == 0 for t in ("b", "d", "ev", "evy")), f"годы и событие — для всех 94 человек; пропуски по видам: {r['miss']}")
    check(pg.evaluate("P.every(p => makeQ(p))"), "для каждого человека есть вопрос")
    # Раунд: одна ошибка → повтор в конце
    pg.click('[data-act="start"]')
    first_wrong, asked, kinds = True, 0, set()
    while pg.locator(".opt").count():
        it = pg.evaluate("() => { const q = round.qs[round.i]; return { a: q.a.replace(/\\u00a0/g, ' '), type: q.type }; }")
        kinds.add(it["type"])
        opts = pg.eval_on_selector_all(".opt", "els => els.map(e => e.textContent.replace(/\\u00a0/g, ' '))")
        k = opts.index(it["a"])
        if first_wrong:
            k = (k + 1) % len(opts)
        pg.locator(".opt").nth(k).click()
        if asked == 0:
            pg.screenshot(path=str(OUT / "s5-answer.png"))
            check(pg.locator(".fb.bad").count() == 1 and pg.locator(".fb .tl").count() == 1, "после ответа — разбор и лента")
        first_wrong = False
        pg.click('[data-act="next"]')
        asked += 1
        if asked > 20:
            break
    end = text(pg, "#view")
    check(asked == 11 and "9 из 10 с первого раза" in end and "Повторите" in end, f"раунд: 11 вопросов (ошибка повторена), итог 9 из 10 — {asked}")
    srs = json.loads(pg.evaluate("localStorage.getItem('sovr:srs')"))
    check(len(srs) == 10 and all(v["b"] == 1 for v in srs.values()), "10 человек в интервалах (ошибочный — после повтора)")
    pg.screenshot(path=str(OUT / "s6-end.png"))
    print("    виды вопросов в раунде:", sorted(kinds))
    ctx.close()
    # iPad: на всю ширину и крупнее
    for w, h in ((390, 844), (820, 1180), (1180, 820)):
        ctx, pg = page(b, "feed", w, height=h)
        info = pg.evaluate("""() => ({ wide: document.documentElement.classList.contains('wide'),
          root: parseFloat(getComputedStyle(document.documentElement).fontSize), view: document.getElementById('view').getBoundingClientRect().width })""")
        if w < 700:
            check(not info["wide"] and abs(info["root"] - 16.8) < 0.1, f"телефон {w}px — обычный размер: {info['root']}")
        else:
            check(info["wide"] and info["view"] >= w - 50 and info["root"] > 21, f"iPad {w}×{h}: на всю ширину ({info['view']:.0f}), шрифт {info['root']:.1f}px")
            pg.screenshot(path=str(OUT / f"s-ipad{w}-feed.png"))
        ctx.close()
    # Все вопросы с ответом при крупном тексте: узкий телефон и iPad в альбоме
    for w, h in ((320, 844), (1180, 820)):
        ctx, pg = page(b, "train", w, 1.4, height=h)
        bad = []
        for t in ("b", "d", "ev", "evy", "older", "met", "alive", "age"):
            for i in range(0, 94, 3 if w == 320 else 7):
                ok = pg.evaluate(f"""() => {{ const q = GEN['{t}'](P[{i}]); if (!q) return false; q.kind = KIND['{t}'];
                  round = {{ qs: [q], i: 0, pick: null, ok: 0, miss: [], again: new Set() }}; answer(0); render(); return true; }}""")
                if not ok:
                    continue
                r = pg.evaluate(LAYOUT)
                if r["doc"] or r["bad"] or r["clip"] or r["split"]:
                    bad.append(f"{t}:{pg.evaluate(f'P[{i}].id')} {r['bad'] or ''}{r['clip'] or ''}{r['split'] or ''}")
        pg.evaluate("round = null; localStorage.removeItem('sovr:srs')")
        check(not bad, f"{w}×{h} ×1.4: все виды вопросов с разбором помещаются {bad[:3]}")
        ctx.close()
    # Все карточки людей на узком экране с крупным текстом
    ctx, pg = page(b, "feed", 320, 1.4)
    bad = []
    for pid in pg.evaluate("P.map(p => p.id)"):
        pg.evaluate(f"openPerson('{pid}')")
        r = pg.evaluate(LAYOUT)
        if r["doc"] or r["bad"] or r["clip"] or r["split"]:
            bad.append(f"{pid}: {r['bad'] or ''}{r['clip'] or ''}{r['split'] or ''}")
    check(not bad, f"320 ×1.4: все 94 карточки людей помещаются {bad[:3]}")
    ctx.close()
    # Ширины и крупный текст: вкладки, карточка, вопросы
    SIZES = [(320, 844), (375, 844), (390, 844), (430, 932), (744, 1133), (820, 1180), (1024, 1366), (1180, 820), (1366, 1024), (1024, 768)]
    for scale in (None, 1.15, 1.4):
        for w, h in SIZES:
            for tab in ("feed", "year", "pair", "train"):
                ctx, pg = page(b, tab, w, scale, "localStorage.setItem('sovr:era', '');" if tab == "feed" and w in (320, 1366) else "", h)
                sfx = f"{w}×{h} {tab}{' ×' + str(scale) if scale else ''}"
                fits(pg, sfx)
                if tab == "feed" and w in (320, 744, 1180):
                    pg.locator('.tr.p').nth(3).click()
                    fits(pg, sfx + " карточка")
                if tab == "year":
                    pg.evaluate("setYear(-44)")
                    fits(pg, sfx + " 44 до н. э.")
                if tab == "train":
                    pg.click('[data-act="start"]')
                    for _ in range(3):
                        pg.locator(".opt").first.click()
                        fits(pg, sfx + " вопрос")
                        pg.click('[data-act="next"]')
                if w in (320, 1180) and not scale:
                    pg.screenshot(path=str(OUT / f"s-w{w}-{tab}.png"))
                ctx.close()
    b.close()
check(not errors, f"ошибок JS нет {errors[:3]}")
srv.shutdown()
print("ПРОВАЛОВ:", len(fails))
sys.exit(1 if fails else 0)
