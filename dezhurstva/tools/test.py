#!/usr/bin/env python3
"""Проверка приложения в Chromium: вкладки, выбор себя, сетка, пожелания, ширины экрана, ошибки JS.
Запуск из корня репозитория: python3 dezhurstva/tools/test.py [папка для скриншотов]"""
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
data = json.loads((ROOT / "data" / "schedule.json").read_text())
fails, errors = [], []


def text(loc):
    return loc.inner_text().replace("\xa0", " ")


def check(cond, msg):
    print(("ok  " if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)


def page_at(b, when, width=390, height=844, me=None, tab=None):
    ctx = b.new_context(viewport={"width": width, "height": height}, timezone_id="Asia/Yekaterinburg", locale="ru-RU", device_scale_factor=2)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.clock.install(time=when)
    init = ""
    if me:
        init += f"localStorage.setItem('dezh:me', {json.dumps(me)});"
    if tab:
        init += f"localStorage.setItem('dezh:tab', {json.dumps(tab)});"
    if init:
        pg.add_init_script(init)
    pg.goto(URL)
    pg.wait_for_selector("#view > *")
    return ctx, pg


def hscroll(pg):
    return pg.evaluate("""() => { const m = document.querySelector('main'); const bad = [];
      for (const el of document.querySelectorAll('#view *')) { if (el.closest('.chips')) continue; const r = el.getBoundingClientRect();
        if (r.width && (r.right > innerWidth + 1 || r.left < -1)) bad.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right)); }
      return { doc: document.documentElement.scrollWidth > innerWidth, main: m.scrollWidth > m.clientWidth, bad: bad.slice(0, 5) }; }""")


def split_words(pg):
    """Слова, разорванные между строками (перенос внутри слова)."""
    return pg.evaluate("""() => { const bad = [], range = document.createRange();
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let node;
      while ((node = w.nextNode())) { const el = node.parentElement;
        if (!el || el.closest('script, style, textarea, [hidden], .chips') || !el.getClientRects().length) continue;
        const re = /[A-Za-zА-Яа-яЁё0-9]{2,}/g; let m;
        while ((m = re.exec(node.textContent))) { range.setStart(node, m.index); range.setEnd(node, m.index + m[0].length);
          const tops = new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.bottom)));
          if (tops.size > 1) bad.push(m[0]); } }
      return bad.slice(0, 8); }""")


def clipped(pg):
    return pg.evaluate("""() => { const out = [];
      const sel = '.tab, .brush button, .seg button, .wdrow button, .btn, .chip, .mbar h2, .day .w, .day .n, .wcal .day .t, .pill, .stepper output, .dlist b.nm';
      for (const el of document.querySelectorAll(sel)) { const st = getComputedStyle(el);
        if (st.display === 'none' || !el.getClientRects().length) continue;
        if (el.scrollWidth > el.clientWidth + 1) out.push((el.className || el.tagName) + ': ' + el.textContent.trim().slice(0, 20));
        const pr = el.parentElement.getBoundingClientRect(), r = el.getBoundingClientRect();
        if (el.matches('.day .w, .day .n, .wcal .day .t, .dlist b.nm') && (r.left < pr.left - 1 || r.right > pr.right + 1)) out.push('клетка: ' + el.textContent.trim()); }
      return out.slice(0, 6); }""")


with sync_playwright() as p:
    b = p.chromium.launch()
    # 1. Первый запуск: выбор себя
    ctx, pg = page_at(b, "2026-11-05T12:00:00+05:00")
    check(pg.locator(".name").count() == len(data["doctors"]), "выбор себя: все врачи")
    pg.screenshot(path=str(OUT / "01-pick.png"))
    pg.locator(".name", has_text="Клепиков").click()
    hero = text(pg.locator(".hero"))
    check("сегодня в 16:18" in hero and "5 ноября" in hero, f"ближайшее дежурство Клепикова: {hero!r}")
    check(pg.locator(".dlist li:not(.mark)").count() == 7, "7 дежурств в ноябре")
    check("134 ч 48 мин" in text(pg.locator(".sum")), "сумма часов 134 ч 48 мин")
    check(pg.locator('a[href^="webcal:"]').get_attribute("href").endswith("/cal/klepikov.ics"), "ссылка webcal")
    pg.screenshot(path=str(OUT / "02-me.png"), full_page=False)
    # 2. График: сейчас дежурит (5 ноября 03:00 — Алекешова с 4 ноября, праздник, до 08:00)
    ctx.close()
    ctx, pg = page_at(b, "2026-11-05T03:00:00+05:00", me="klepikov", tab="all")
    now = pg.locator(".now").inner_text()
    check("Сейчас" in now and "Алекешова" in now and "до 08:00" in now, f"сейчас дежурит: {now!r}")
    check(pg.locator(".cal .day").count() == 30, "30 дней в сетке")
    check(pg.locator(".cal .day.off").count() == 10, "выходных и праздников 10 (9 сб/вс + 4 ноября)")
    check(pg.locator(".cal .day.hol").count() == 1, "праздник 4 ноября отмечен")
    check(pg.locator(".cal .day.mine").count() == 7, "мои дни подсвечены")
    codes = pg.eval_on_selector_all(".cal .day .w", "els => [...new Set(els.map(e => e.textContent))]")
    check(all(len(c) == 2 and c[0].isupper() and c[1].islower() for c in codes) and len(codes) == len(set(codes)) == 7
          and {"Лк", "Ло", "Кл", "Ка", "Ом"} <= set(codes), f"в сетке по две буквы, без совпадений: {sorted(codes)}")
    gap = pg.evaluate("""() => { let worst = 99; for (const d of document.querySelectorAll('.cal .day')) {
        const n = d.querySelector('.n'), w = d.querySelector('.w'); if (!w) continue;
        worst = Math.min(worst, w.getBoundingClientRect().top - n.getBoundingClientRect().bottom); } return worst; }""")
    check(gap >= 0, f"число и буквы в клетке не наезжают (зазор {gap:.1f}px)")
    pg.screenshot(path=str(OUT / "03-grid.png"), full_page=False)
    pg.locator('.cal .day[data-k="2026-11-01"]').click()
    dc = pg.locator(".daycard").inner_text()
    check("Лекерова" in dc and "08:00 → 08:00" in dc and "сутки" in dc, f"карточка дня 1 ноября: {dc!r}")
    pg.locator('.chip[data-id="leonard"]').click()
    check(pg.locator(".cal .day.hit").count() == 4, "подсветка Леонарда: 4 пятницы")
    pg.locator('.seg button[data-v="list"]').click()
    check(pg.locator(".dlist li").count() == 4, "список с фильтром: 4 строки")
    pg.locator('.chip[data-id=""]').click()
    one = pg.evaluate("""() => [...document.querySelectorAll('.dlist b.nm')].every(b => b.getClientRects().length === 1 && b.scrollWidth <= b.clientWidth + 1)""")
    check(one, "в списке фамилии в одну строку, без переноса")
    pg.screenshot(path=str(OUT / "04-list.png"), full_page=False)
    ctx.close()
    # 3. Пожелания (сегодня 12 октября → декабрь, до 15 ноября)
    ctx, pg = page_at(b, "2026-10-12T21:00:00+05:00", me="omutov", tab="wish")
    h = text(pg.locator("#view .card").first)
    check("декабрь 2026" in h and "15 ноября" in h, f"пожелания на декабрь до 15 ноября: {h[:90]!r}")
    check(pg.locator('.wcal .day[data-k="2026-12-31"]').get_attribute("class").count("off") == 1, "31 декабря 2026 — выходной по переносу")
    pg.locator('.brush button[data-v="no"]').click()
    pg.locator('.toggle[data-act="range"]').click()
    pg.locator('.wcal .day[data-k="2026-12-01"]').click()
    pg.locator('.wcal .day[data-k="2026-12-05"]').click()
    pg.locator('.toggle[data-act="range"]').click()
    pg.locator('.brush button[data-v="yes"]').click()
    pg.locator('.wcal .day[data-k="2026-12-19"]').click()
    pg.locator('.wdrow.no button[data-i="0"]').click()
    pg.locator('.wdrow.yes button[data-i="4"]').click()
    pg.locator('button[data-act="qmode"][data-f="total"][data-v="max"]').click()
    pg.locator('button[data-act="qn"][data-f="total"][data-d="1"]').click()
    pg.fill("#note", "Не ставить подряд с выходными")
    s = pg.locator("#summary").inner_text()
    check("Не ставить: пн; 1–5" in s and "Хочу: пт; 19" in s and "всего не больше 5" in s and "Комментарий: Не ставить подряд" in s, f"итог пожеланий: {s!r}")
    cfg = json.loads((ROOT / "data" / "config.json").read_text())["form"]
    if cfg.get("action"):
        posted = []
        pg.route(cfg["action"], lambda route: (posted.append(route.request.post_data or ""), route.fulfill(status=200, body="ok")))
        pg.locator('button[data-act="send"]').click()
        pg.wait_for_selector(".sent")
        from urllib.parse import parse_qs
        body = parse_qs(posted[0]) if posted else {}
        val = (body.get(cfg["entry"]) or [""])[0]
        check(len(posted) == 1 and "#DEZH " in val and '"who":"omutov"' in val and '"m":"2026-12"' in val,
              f"отправка в Google Форму: поле {cfg['entry']}, {len(val)} симв.")
    else:
        check(pg.locator('button[data-act="send"]').is_disabled(), "отправка выключена, пока форма не настроена")
    pg.screenshot(path=str(OUT / "05-wish.png"), full_page=True)
    ctx.close()
    # 4. Excel
    ctx, pg = page_at(b, "2026-10-12T21:00:00+05:00", me="omutov", tab="files")
    href = pg.locator('.file a').first.get_attribute("href")
    check(href.startswith("files/2026-11.xlsx"), "ссылка на Excel ноября")
    r = pg.request.get(URL.replace("index.html", href))
    check(r.ok and len(r.body()) > 3000, "файл Excel скачивается")
    pg.screenshot(path=str(OUT / "06-files.png"), full_page=False)
    ctx.close()
    # 4а. Для печати: телефоны из файла графика (вымышленные), сборка файла в браузере
    import base64, io, subprocess, tempfile, zipfile
    tmp = pathlib.Path(tempfile.mkdtemp())
    fake = {d: f"8900000{i:04d}" for i, d in enumerate(data["doctors"])}
    (tmp / "ph.json").write_text(json.dumps(fake))
    subprocess.run([sys.executable, str(ROOT / "tools" / "make_xlsx.py"), "2026-11", "--full", str(tmp / "src.xlsx"),
                    "--phones", str(tmp / "ph.json")], check=True, capture_output=True)
    ctx, pg = page_at(b, "2026-10-12T21:00:00+05:00", me="klepikov", tab="files")
    pg.locator("details.org > summary").click()
    pg.set_input_files("#phfile", str(tmp / "src.xlsx"))
    pg.wait_for_function("document.querySelectorAll('[data-ph]')[0].value !== ''")
    vals = pg.eval_on_selector_all("[data-ph]", "els => els.map(e => [e.dataset.ph, e.value])")
    check(all(v == fake[k] for k, v in vals) and len(vals) == len(fake), "телефоны взяты из файла графика")
    pg.fill('[data-ph="omutov"]', "8 900 111-22-33")
    pg.locator('button[data-act="pprep"]').first.click()
    pg.wait_for_selector('button[data-act="pshare"]')
    b64 = pg.evaluate("""async () => { const buf = new Uint8Array(await printReady.file.arrayBuffer()); let s = '';
      for (let i = 0; i < buf.length; i++) s += String.fromCharCode(buf[i]); return btoa(s); }""")
    z = zipfile.ZipFile(io.BytesIO(base64.b64decode(b64)))
    import openpyxl
    ws = openpyxl.load_workbook(io.BytesIO(base64.b64decode(b64))).worksheets[0]
    a_col = [ws.cell(r, 1).value for r in range(3, 13)]
    check(a_col[0] == "Врач, телефон" and a_col[2] == f"КЛЕПИКОВ {fake['klepikov']}" and "ОМУТОВ 8 900 111-22-33" in a_col,
          f"файл для печати: телефоны у фамилий {a_col[:3]}")
    check(ws.cell(5, 6).value == "+", "в файле для печати те же «+»")
    pg.screenshot(path=str(OUT / "07-print.png"), full_page=False)
    ctx.close()
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    # 5. Ширины: ничего не вылезает за экран и не обрезается внутри кнопок и клеток; ещё раз с текстом крупнее на 15%
    for scale in ("", "129.4%"):
        for w in (320, 360, 375, 390, 393, 402, 430, 440, 820, 1180):
            for tab in ("me", "all", "wish", "files"):
                ctx, pg = page_at(b, "2026-11-05T12:00:00+05:00" if tab != "wish" else "2026-10-12T21:00:00+05:00", width=w, height=900, me="khamatnurova", tab=tab)
                if scale:
                    pg.evaluate(f"document.documentElement.style.fontSize = '{scale}'")
                if tab == "files":
                    pg.locator("details.org > summary").click()
                if tab == "all":
                    pg.locator('.cal .day[data-k="2026-11-02"]').click()
                    r = hscroll(pg)
                    c = clipped(pg)
                    check(not r["doc"] and not r["main"] and not r["bad"] and not c, f"{w}px сетка{' +15%' if scale else ''} {r['bad'] or ''} {c or ''}")
                    if w in (320, 390) and not scale:
                        pg.screenshot(path=str(OUT / f"w{w}-grid.png"), full_page=False)
                    sw = split_words(pg)
                    check(not sw, f"{w}px сетка и карточка дня{' +15%' if scale else ''}: без переносов внутри слов {sw or ''}")
                    pg.locator('.seg button[data-v="list"]').click()
                    one = pg.evaluate("() => [...document.querySelectorAll('.dlist b.nm')].every(b => b.getClientRects().length === 1)")
                    check(one, f"{w}px список{' +15%' if scale else ''}: фамилии без переноса")
                r = hscroll(pg)
                c = clipped(pg)
                check(not r["doc"] and not r["main"] and not r["bad"] and not c,
                      f"{w}px {tab}{' +15%' if scale else ''}: без сдвига вбок и обрезки {r['bad'] or ''} {c or ''}")
                sw = split_words(pg)
                check(not sw, f"{w}px {tab}{' +15%' if scale else ''}: без переносов внутри слов {sw or ''}")
                if not scale and w in (320, 390) and tab in ("me", "all", "wish", "files"):
                    pg.screenshot(path=str(OUT / f"w{w}-{tab}.png"), full_page=False)
                if tab == "me":
                    pg.locator('[data-act="change"]').click()
                    sw = split_words(pg)
                    check(not sw and not hscroll(pg)["bad"], f"{w}px выбор себя{' +15%' if scale else ''}: без переносов внутри слов {sw or ''}")
                    pg.locator('[data-act="cancelpick"]').click()
                if tab == "me" and w in (320, 390):
                    pg.click("#helpBtn")
                    r = pg.evaluate("() => { const p = document.querySelector('#help .panel'); return p.scrollWidth > p.clientWidth; }")
                    check(not r, f"{w}px справка «?» помещается{' +15%' if scale else ''}")
                ctx.close()
    b.close()
check(not errors, f"ошибок JS нет {errors[:3]}")
srv.shutdown()
print("ПРОВАЛОВ:", len(fails))
sys.exit(1 if fails else 0)
