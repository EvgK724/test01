# Самостоятельный сайт «Артерии мозга» для GitHub Pages или любого хостинга: без аккаунтов, работает офлайн,
# ставится на экран «Домой». Прогресс хранится в браузере телефона (облачной синхронизации здесь нет).
import json, pathlib, shutil, zipfile
from PIL import Image
art = pathlib.Path("art"); site = art / "site"
shutil.rmtree(site, ignore_errors=True); site.mkdir()
frag = (art / "index.html").read_text()
i = frag.index("</style>") + len("</style>")
head_part, body_part = frag[:i], frag[i:]
assert head_part.lstrip().startswith("<title>")
DESC = "Атлас артерий мозга для врачей ПСО: схемы, показания к ВСТЭ по КР МЗ РФ 2024 и AHA/ASA 2026, тренажёр."
html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{DESC}">
<meta name="theme-color" content="#0e1113">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="Артерии">
<link rel="apple-touch-icon" sizes="180x180" href="icon-180.png">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="manifest" href="manifest.webmanifest">
{head_part.strip()}
</head>
<body>
{body_part.strip()}
<script>
// Офлайн‑режим: после первого открытия приложение работает без интернета
if ("serviceWorker" in navigator) {{ window.addEventListener("load", () => {{ navigator.serviceWorker.register("sw.js").catch(() => {{}}); }}); }}
</script>
</body>
</html>
"""
(site / "index.html").write_text(html)
manifest = {
    "name": "Артерии мозга", "short_name": "Артерии", "description": DESC, "lang": "ru",
    "start_url": "./", "scope": "./", "display": "standalone",
    "background_color": "#0e1113", "theme_color": "#0e1113",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
(site / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
(site / "sw.js").write_text('''// Кэш для работы без интернета. Сначала сеть — обновления приходят сразу; без сети — из кэша.
const CACHE = "arterii-v2";
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  e.respondWith(
    fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req).then(r => r || caches.match("index.html")))
  );
});
''')
shutil.copy(art / "tile" / "icon-180.png", site / "icon-180.png")
shutil.copy(art / "tile" / "icon-192.png", site / "icon-192.png")
Image.open(art / "tile" / "tile-1024.png").convert("RGB").resize((512, 512), Image.LANCZOS).save(site / "icon-512.png", optimize=True)
(site / "README.md").write_text("""# Артерии мозга

Атлас артерий мозга для врачей ПСО: интерактивные схемы (Виллизиев круг, ВСА, СМА, ВББ, бассейны, ASPECTS),
показания к ВСТЭ по КР МЗ РФ «Ишемический инсульт и ТИА» (2024) и AHA/ASA 2026, тренажёр со 100 карточками.

- Работает в браузере телефона без регистрации; после первого открытия — и без интернета.
- Ставится на экран «Домой»: iPhone — Safari → «Поделиться» → «На экран „Домой"»; Android — Chrome → ⋮ → «Установить приложение».
- Прогресс тренировки хранится в браузере на каждом телефоне.

Учебный материал для отработки решения о ВСТЭ: решение принимает невролог по клиническим рекомендациям и локальному протоколу.
""")
zp = pathlib.Path("arterii-site.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(site.iterdir()):
        z.write(f, f.name)
print("ok", [f"{f.name}:{f.stat().st_size}" for f in sorted(site.iterdir())], zp.stat().st_size)
