# Проверка оболочки «Медицина ПСО»: каждый модуль открывается из главной и отвечает на карточку, прогресс
# ложится в свой документ progress-<ключ> и в свои ключи localStorage, счётчики и поиск, ширины 320–430 и iPad.
# Запуск из sources/ после shell/build.py: python3 shell/test.py  (Playwright с Chromium)
import asyncio, json, pathlib, threading, functools, http.server, socketserver
from playwright.async_api import async_playwright
HERE = pathlib.Path("shell").resolve()
APP = (pathlib.Path("..") / "app").resolve()
CAT = json.loads((pathlib.Path("..") / "catalog.json").read_text())
KEYS = [a["key"] for a in CAT["apps"]]

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(APP)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_address[1]}/index.html"

# Подставной window.claude (db + user) — только в верхнем окне; ошибки всех окон собираются в top.__errs
FAKE = r"""
(() => {
  const errs = (window.top.__errs = window.top.__errs || []);
  window.addEventListener("error", e => errs.push((window === window.top ? "shell: " : "frame: ") + (e.message || e)));
  window.addEventListener("unhandledrejection", e => errs.push("reject: " + (e.reason && (e.reason.message || e.reason))));
  if (window !== window.top || !window.__withCloud) return;
  const store = window.__store = {};
  const snap = (path) => ({ exists: path in store, data: () => store[path] ? JSON.parse(JSON.stringify(store[path])) : undefined });
  const doc = path => ({
    get: async () => snap(path),
    set: async v => { store[path] = JSON.parse(JSON.stringify(v)); },
    update: async v => { store[path] = Object.assign({}, store[path] || {}, JSON.parse(JSON.stringify(v))); },
  });
  const db = { doc, collection: path => ({ get: async () => ({ docs: Object.keys(store).filter(p => p.startsWith(path + "/") && !p.slice(path.length + 1).includes("/")).map(p => ({ id: p.slice(path.length + 1), exists: true, data: () => JSON.parse(JSON.stringify(store[p])) })) }) }) };
  const user = { id: async () => "u1" };
  window.claude = { use: async n => n === "db" ? db : n === "user" ? user : null };
})();
"""
SIZES = [("320", 320, 568), ("375", 375, 667), ("390", 390, 844), ("430", 430, 932), ("pad-port", 820, 1180), ("pad-land", 1180, 820)]

async def overflow(pg):
    return await pg.evaluate("""() => {
      const h = document.getElementById('home'), W = h.clientWidth, out = [];
      document.querySelectorAll('#home *').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && r.right > W + 0.5 && !e.closest('[hidden]')) out.push((e.className || e.tagName) + ' +' + Math.round(r.right - W)); });
      return { sw: h.scrollWidth, cw: W, bad: out.slice(0, 5) };
    }""")

async def answer(fr, kind):
    if kind == "att":
        await fr.click('.tab[data-tab="cards"]'); await fr.click("#showBtn"); await fr.click('[data-r="know"]')
        return True
    await fr.click("#go")
    for _ in range(6):
        loc = fr.locator("#opts:not([hidden]) .opt")
        if await loc.count():
            await loc.first.click(); await fr.click("#next"); return True
        nxt = fr.locator("#next:not([hidden])")
        if await nxt.count(): await nxt.click()
        else: break
    return False

async def main():
    out = {"modules": {}}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # ——— телефон, с облаком
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, device_scale_factor=2)
        await ctx.add_init_script("window.__withCloud = true;" + FAKE)
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(600)
        out["eyebrow"] = await pg.inner_text("#eyebrow")
        out["tiles"] = await pg.locator(".tile").count()
        out["icons_ok"] = await pg.evaluate("[...document.querySelectorAll('.t-ic')].every(i => i.complete && i.naturalWidth > 0)")
        await pg.screenshot(path=str(HERE / "s-home.png"))
        meta = {a["key"]: a for a in json.loads(await pg.evaluate("JSON.stringify(CAT.apps)"))}
        for key in KEYS:
            r = {}
            await pg.click(f'.tile[data-k="{key}"]')
            await pg.wait_for_selector("#frame.ready", timeout=15000)
            await pg.wait_for_timeout(500)
            f = pg.frames[1]
            r["text"] = await f.evaluate("document.body.innerText.length")
            r["bridged"] = await f.evaluate("!!window.claude && window.claude !== window.top.claude")
            r["overflow"] = await f.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            r["answered"] = await answer(f, meta[key]["kind"])
            await pg.wait_for_timeout(1700)            # модуль сохраняет в облако с задержкой (0,7–1,2 с)
            if key == "daat": await pg.screenshot(path=str(HERE / "s-module.png"))
            await pg.click("#back"); await pg.wait_for_timeout(400)
            r["tile"] = await pg.inner_text(f'.tile[data-k="{key}"] .cnt')
            r["ls"] = await pg.evaluate(f"!!localStorage.getItem({json.dumps(meta[key]['ls'])})")
            out["modules"][key] = r
        store = json.loads(await pg.evaluate("JSON.stringify(Object.keys(window.__store))"))
        out["cloud_docs"] = store
        out["shared_doc_written"] = "data/users/u1/progress" in store
        out["summary"] = await pg.inner_text("#sum")
        out["today"] = await pg.inner_text("#today")
        await pg.screenshot(path=str(HERE / "s-home-after.png"))
        # поиск
        for q in ["тикагрелор", "ELAN", "Tmax", "ГИТ", "ёжик-несуществующий"]:
            await pg.fill("#q", q); await pg.wait_for_timeout(500)
            out["search " + q] = {"tiles": await pg.locator(".tile:not([hidden])").count(),
                                  "hits": await pg.locator(".hit").count(),
                                  "label": await pg.inner_text("#foundLbl") if await pg.locator("#found:not([hidden])").count() else "",
                                  "empty": await pg.locator("#empty:not([hidden])").count()}
            if q == "тикагрелор": await pg.screenshot(path=str(HERE / "s-search.png"))
        await pg.fill("#q", ""); await pg.wait_for_timeout(200)
        # перезапуск: «Продолжить» и прогресс из localStorage
        await pg.reload(); await pg.wait_for_timeout(800)
        out["after_reload_today"] = await pg.inner_text("#today")
        out["errors"] = await pg.evaluate("window.__errs || []")
        await ctx.close()
        # ——— без облака (GitHub Pages / локально): модули работают на localStorage
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await ctx.add_init_script(FAKE)
        pg = await ctx.new_page(); await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click('.tile[data-k="att"]'); await pg.wait_for_selector("#frame.ready"); await pg.wait_for_timeout(300)
        out["no_cloud_att"] = await answer(pg.frames[1], "att")
        await pg.click("#back"); await pg.wait_for_timeout(200)
        out["no_cloud_tile"] = await pg.inner_text('.tile[data-k="att"] .cnt')
        out["errors_no_cloud"] = await pg.evaluate("window.__errs || []")
        await ctx.close()
        # ——— ширины: главная и открытый модуль
        out["sizes"] = {}
        for name, w, h in SIZES:
            ctx = await b.new_context(viewport={"width": w, "height": h}, has_touch=True)
            await ctx.add_init_script(FAKE)
            pg = await ctx.new_page(); await pg.goto(URL); await pg.wait_for_timeout(700)
            o = await overflow(pg)
            await pg.screenshot(path=str(HERE / f"s-{name}.png"))
            await pg.click('.tile[data-k="trombotsity"]'); await pg.wait_for_selector("#frame.ready"); await pg.wait_for_timeout(400)
            o["module_overflow"] = await pg.frames[1].evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            o["frame_h"] = await pg.evaluate("document.getElementById('frame').getBoundingClientRect().height")
            await pg.screenshot(path=str(HERE / f"s-{name}-module.png"))
            o["errors"] = await pg.evaluate("window.__errs || []")
            out["sizes"][name] = o
            await ctx.close()
        await b.close()
    (HERE / "test-out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))
asyncio.run(main())
