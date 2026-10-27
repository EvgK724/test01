#!/usr/bin/env python3
"""Проверка «Коллокаций» в Chromium: список уроков, страница урока (скрытый перевод, озвучка, переход по урокам),
карточки (переворот, оценки, «Не знаю» возвращается, смахивание), тренировка (ошибка повторяется в конце раунда,
интервалы), поиск по-английски и по-русски с переходом к коллокации; все 55 уроков при ширине 320 и на iPad
с обычным и крупным текстом — без сдвига вбок, обрезки и переносов внутри слов; ошибки JS.
Запуск из корня репозитория: python3 kollokatsii/tools/test.py [папка для скриншотов]"""
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


# Голос: вместо настоящей озвучки запоминаем, что прозвучало
SPEECH = """window.__said = []; window.speechSynthesis && (speechSynthesis.speak = u => __said.push(u.text), speechSynthesis.cancel = () => {});"""


def page(b, tab="units", width=390, height=844, scale=None, init=""):
    ctx = b.new_context(viewport={"width": width, "height": height}, locale="ru-RU", device_scale_factor=1)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.add_init_script(SPEECH + f"localStorage.setItem('kol:tab', '{tab}');" + init)
    pg.goto(URL)
    pg.wait_for_selector("#view > *")
    if scale:  # крупный текст телефона: как applyTextSize(), с множителем iPad
        pg.evaluate(f"document.documentElement.style.fontSize = (105 * Math.min({scale} * deviceK(), 2.2)).toFixed(2) + '%'")
    return ctx, pg


LAYOUT = """() => { const out = {bad: [], clip: [], split: []}, range = document.createRange();
  for (const el of document.querySelectorAll('#view *')) { const r = el.getBoundingClientRect();
    if (r.width && (r.right > innerWidth + 1 || r.left < -1)) out.bad.push(el.className + ' ' + Math.round(r.right)); }
  for (const el of document.querySelectorAll('.tab, .btn, .opt, .pill, .big, .urow .t, .col .en, .fc .front')) {
    if (!el.getClientRects().length) continue;
    if (el.scrollWidth > el.clientWidth + 1) out.clip.push(el.className + ': ' + el.textContent.trim().slice(0, 30)); }
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let node;
  while ((node = w.nextNode())) { const el = node.parentElement;
    if (!el || el.closest('script, style, [hidden], select, option') || !el.getClientRects().length) continue;
    const re = /[A-Za-zА-Яа-яЁё0-9]{2,}/g; let m;
    while ((m = re.exec(node.textContent))) { range.setStart(node, m.index); range.setEnd(node, m.index + m[0].length);
      if (new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.bottom))).size > 1) out.split.push(m[0]); } }
  out.doc = document.documentElement.scrollWidth > innerWidth || document.querySelector('main').scrollWidth > document.querySelector('main').clientWidth;
  for (const k of ['bad', 'clip', 'split']) out[k] = out[k].slice(0, 5);
  return out; }"""


def fits(pg, label):
    r = pg.evaluate(LAYOUT)
    ok = not r["doc"] and not r["bad"] and not r["clip"] and not r["split"]
    return ok, f"{label}: {r['bad'] or ''}{r['clip'] or ''}{r['split'] or ''}"


with sync_playwright() as p:
    b = p.chromium.launch()
    # Данные
    ctx, pg = page(b)
    info = pg.evaluate("""() => ({ units: UNITS.length, items: ITEMS.length, first: UNITS[0].n, last: UNITS[UNITS.length - 1].n,
      ids: new Set(ITEMS.map(i => i.id)).size, parts: PARTS.reduce((s, p) => s + UNITS.filter(u => u.n >= p.from && u.n <= p.to).length, 0),
      noKey: ITEMS.filter(i => !i.key || i.w.length !== 3).map(i => i.id).slice(0, 3) })""")
    check(info["units"] == 55 and info["first"] == 6 and info["last"] == 60, f"55 уроков, 6–60: {info['units']}")
    check(info["items"] > 1500 and info["ids"] == info["items"], f"коллокации с уникальными id: {info['items']}")
    check(info["parts"] == 55, "каждый урок — в одной из частей списка")
    check(not info["noKey"], f"у каждой коллокации пропуск и три неверных варианта {info['noKey']}")
    # Список уроков
    n = pg.locator(".urow").count()
    check(n == 55, f"в списке 55 уроков: {n}")
    pg.screenshot(path=str(OUT / "k1-units.png"))
    # Страница урока: перевод скрыт, нажатие открывает; озвучка; соседний урок
    pg.click('.urow[data-n="13"]')
    check("Weather" in pg.inner_text(".uhead"), "открывается урок 13 Weather")
    cols = pg.locator(".col").count()
    check(cols == pg.evaluate("UNIT[13].items.length"), f"на странице урока все коллокации: {cols}")
    pg.click('.toggle[data-act="cover"]')
    check(pg.locator(".ru.cover").count() == cols, "«Скрыть перевод» прячет все переводы")
    pg.locator(".ru.cover").first.click()
    check(pg.locator(".ru.cover").count() == cols - 1, "нажатие открывает один перевод")
    pg.locator(".col .say").first.click()
    pg.locator(".col .ex").first.click()
    said = pg.evaluate("__said")
    check(said[:2] == [pg.evaluate("UNIT[13].items[0].cp"), pg.evaluate("UNIT[13].items[0].exp")], f"озвучка коллокации и примера: {said[:2]}")
    pg.screenshot(path=str(OUT / "k2-unit.png"))
    pg.locator('.unav .btn').last.click()
    check("Travel" in pg.inner_text(".uhead"), "кнопка следующего урока ведёт к уроку 14")
    ctx.close()
    # Карточки урока: переворот, «Не знаю» возвращается, «Знаю» — интервал 1 день, смахивание
    ctx, pg = page(b, "units")
    pg.click('.urow[data-n="7"]')
    pg.click('[data-act="ucards"]')
    check(pg.locator("#fc").count() == 1 and pg.evaluate("session.deck.length") == 20, "карточки урока 7: заход из 20")
    first = pg.evaluate("session.deck[0].id")
    pg.click("#fc")
    check(pg.locator(".grades .btn").count() == 3, "после переворота — «Не знаю», «Почти», «Знаю»")
    pg.screenshot(path=str(OUT / "k3-card.png"))
    pg.click('[data-act="grade"][data-q="0"]')
    deck = pg.evaluate("session.deck.map(c => c.id)")
    check(deck.count(first) == 2 and len(deck) == 21, "«Не знаю» возвращает карточку в этот же заход")
    pg.click("#fc")
    second = pg.evaluate("session.deck[1].id")
    box = pg.locator("#fc").bounding_box()
    pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    pg.mouse.down()
    pg.mouse.move(box["x"] + box["width"] / 2 + 160, box["y"] + box["height"] / 2, steps=8)
    pg.mouse.up()
    pg.wait_for_timeout(400)
    srs = json.loads(pg.evaluate("localStorage.getItem('kol:srs')"))
    check(srs.get(second, {}).get("b") == 1 and pg.evaluate("session.i") == 2, "смахивание вправо — «Знаю», следующая карточка")
    check(srs[first]["b"] == 0, "«Не знаю» — карточка к повторению сегодня")
    ctx.close()
    # Тренировка: одна ошибка повторяется в конце раунда
    ctx, pg = page(b, "train")
    pg.click('[data-act="tstart"]')
    asked, wrong_first = 0, True
    while pg.locator(".opt").count() and asked < 25:
        ans = pg.evaluate("round.qs[round.i].a")
        opts = pg.eval_on_selector_all(".opt", "els => els.map(e => e.textContent)")
        if asked < 10:
            check(len(opts) == 4 and len(set(opts)) == 4 and ans in opts, f"вопрос {asked + 1}: 4 разных варианта, верный среди них") if asked < 3 else None
        k = opts.index(ans)
        if wrong_first:
            k = (k + 1) % 4
        pg.locator(".opt").nth(k).click()
        if asked == 0:
            pg.screenshot(path=str(OUT / "k4-train.png"))
        wrong_first = False
        pg.click('[data-act="next"]')
        asked += 1
    end = pg.inner_text("#view").replace("\xa0", " ")
    check(asked == 11 and "9 из 10 с первого раза" in end and "Запомните" in end, f"раунд: 11 вопросов (ошибка повторена), итог 9 из 10 — {asked}")
    kinds = pg.evaluate("round.qs.map(q => q.kind)")
    check("gap" in kinds and "mean" in kinds, f"в раунде оба вида заданий: {sorted(set(kinds))}")
    ctx.close()
    # Все задания тренировки: верный ответ один, неверные не совпадают с ответом, примеры с пропуском
    ctx, pg = page(b, "train")
    bad = pg.evaluate("""() => { const out = [];
      for (const it of ITEMS) for (const kind of ['gap', 'mean']) { const q = makeQ(it, kind);
        if (q.opts.length !== 4 || new Set(q.opts.map(o => o.toLowerCase())).size !== 4 || q.opts.filter(o => o === q.a).length !== 1) out.push(it.id + ' ' + kind);
        if (kind === 'gap' && !/\\{/.test(it.ex)) out.push(it.id + ' нет пропуска'); }
      return out.slice(0, 5); }""")
    check(not bad, f"во всех {info['items'] * 2} заданиях 4 разных варианта и один верный {bad}")
    ctx.close()
    # Поиск: по-английски и по-русски, переход к коллокации на странице урока
    ctx, pg = page(b, "search")
    pg.fill("#q", "decision")
    hits = pg.locator(".hit").count()
    check(hits >= 5, f"поиск «decision»: {hits} результатов")
    pg.fill("#q", "решение")
    check(pg.locator(".hit").count() >= 3, "поиск по-русски «решение»")
    pg.screenshot(path=str(OUT / "k5-search.png"))
    target = pg.locator(".hit").first.get_attribute("data-id")
    pg.locator(".hit").first.click()
    pg.wait_for_timeout(200)
    vis = pg.evaluate(f"""() => {{ const el = document.getElementById('c-' + {json.dumps(target)}); if (!el) return false;
      const r = el.getBoundingClientRect(); return r.top >= 0 && r.top < innerHeight; }}""")
    check(vis and pg.evaluate("state.tab") == "units", "из поиска — на страницу урока, коллокация на экране")
    ctx.close()
    # Повторение «на сегодня» с главного экрана
    ctx, pg = page(b, "units", init="""localStorage.setItem('kol:srs', JSON.stringify({'u6:highly-unlikely': {b: 1, d: 20000101, n: 1}}));""")
    check(pg.locator('[data-act="godue"]').count() == 1 and "1" in pg.inner_text('[data-act="godue"]'), "на главной — «Повторить сегодня: 1»")
    pg.click('[data-act="godue"]')
    check(pg.evaluate("session.deck.map(c => c.id)") == ["u6:highly-unlikely"], "повторение показывает только то, что пора повторить")
    ctx.close()
    # Все уроки: телефон 320 и iPad (портрет и альбом), обычный и крупный текст
    for (w, h, scale) in ((320, 700, None), (320, 700, 1.4), (390, 844, 1.15), (820, 1180, None), (1180, 820, 1.4)):
        ctx, pg = page(b, "units", w, h, scale)
        ok, msg = fits(pg, f"{w}×{h}{' ×' + str(scale) if scale else ''} список уроков")
        check(ok, msg)
        problems = []
        for u in pg.evaluate("UNITS.map(u => u.n)"):
            pg.evaluate(f"openUnit({u}); render()")
            ok, msg = fits(pg, f"урок {u}")
            if not ok:
                problems.append(msg)
        check(not problems, f"{w}×{h}{' ×' + str(scale) if scale else ''}: все 55 уроков помещаются {problems[:3]}")
        for tab in ("cards", "train", "search"):
            pg.evaluate(f"setTab('{tab}'); render()")
            ok, msg = fits(pg, f"{w} {tab}")
            check(ok, msg)
        # Карточки и задания: каждая коллокация на карточке (обе стороны) и в задании, при этой ширине
        bad = pg.evaluate("""() => { const out = [];
          for (const it of ITEMS) {
            session = { scope: 'all', deck: [it], i: 0, flip: true, n: [0, 0, 0], total: 1 }; state.tab = 'cards'; render(true);
            const fc = document.getElementById('fc'), f = fc.querySelector('.front');
            if (fc.getBoundingClientRect().right > innerWidth + 1 || f.scrollWidth > f.clientWidth + 1) out.push(it.id);
          }
          session = null; return out.slice(0, 5); }""")
        check(not bad, f"{w}×{h}{' ×' + str(scale) if scale else ''}: все карточки помещаются {bad}")
        if w in (320, 1180):
            pg.evaluate("setTab('train'); startRound('all'); render()")
            pg.screenshot(path=str(OUT / f"k-w{w}-train.png"))
        ctx.close()
    b.close()
errors = [e for e in errors if "favicon" not in e]
check(not errors, f"ошибок JS нет {errors[:3]}")
srv.shutdown()
print("ПРОВАЛОВ:", len(fails))
sys.exit(1 if fails else 0)
