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
    pg.screenshot(path=str(OUT / "03-grid.png"), full_page=False)
    pg.locator('.cal .day[data-k="2026-11-01"]').click()
    dc = pg.locator(".daycard").inner_text()
    check("Лекерова" in dc and "08:00 → 08:00" in dc and "сутки" in dc, f"карточка дня 1 ноября: {dc!r}")
    pg.locator('.chip[data-id="leonard"]').click()
    check(pg.locator(".cal .day.hit").count() == 4, "подсветка Леонарда: 4 пятницы")
    pg.locator('.seg button[data-v="list"]').click()
    check(pg.locator(".dlist li").count() == 4, "список с фильтром: 4 строки")
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
    # 5. Ширины
    for w in (320, 375, 390, 430, 820, 1180):
        for tab in ("me", "all", "wish", "files"):
            ctx, pg = page_at(b, "2026-11-05T12:00:00+05:00" if tab != "wish" else "2026-10-12T21:00:00+05:00", width=w, height=900, me="khamatnurova", tab=tab)
            r = hscroll(pg)
            check(not r["doc"] and not r["main"] and not r["bad"], f"{w}px {tab}: без горизонтальной прокрутки {r['bad'] if r['bad'] else ''}")
            if w in (320, 820) and tab in ("all", "wish"):
                pg.screenshot(path=str(OUT / f"w{w}-{tab}.png"), full_page=False)
            ctx.close()
    b.close()
check(not errors, f"ошибок JS нет {errors[:3]}")
srv.shutdown()
print("ПРОВАЛОВ:", len(fails))
sys.exit(1 if fails else 0)
