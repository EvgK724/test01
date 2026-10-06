// Офлайн-кэш для версии на GitHub Pages: свои файлы — сначала сеть, потом кэш; шрифты — из кэша.
// При установке заранее кэшируются и записи голоса Ryan из audio/index.json.
// Записи Safari запрашивает кусками (заголовок Range) и не играет звук, если в ответ пришёл файл целиком, —
// тогда приложение переходит на голос устройства. Поэтому в кэше лежит файл целиком, а отдаётся ровно запрошенный кусок (206).
const CACHE = 'noun-prep-v1';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './apple-touch-icon.png', './icon-192.png', './icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await c.addAll(ASSETS);
    try {
      const r = await fetch('audio/index.json', { cache: 'no-cache' });
      if (r.ok) {
        const j = await r.clone().json();
        await c.put('audio/index.json', r);
        await c.addAll((j.files || []).map((h) => 'audio/' + h + '.mp3'));
      }
    } catch (err) { /* записей ещё нет */ }
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    e.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return res;
      }))
    );
    return;
  }

  if (url.origin !== self.location.origin) return;

  // Записи не меняются (имя = хэш фразы): сначала кэш.
  if (/\/audio\/[0-9a-f]{8}\.mp3$/.test(url.pathname)) {
    e.respondWith(audioResponse(req));
    return;
  }

  // Свои файлы — всегда сверяясь с сервером (no-cache): иначе iPad до 10 минут показывает прежнюю версию страницы.
  e.respondWith(
    fetch(req, { cache: 'no-cache' }).then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req).then((hit) => hit || caches.match('./index.html')))
  );
});

async function audioResponse(req) {
  const c = await caches.open(CACHE);
  let full = await c.match(req.url);
  if (!full) {
    try {
      full = await fetch(req.url);                 // без Range — файл целиком, его и кладём в кэш
    } catch (err) {
      return fetch(req);
    }
    if (!full.ok) return full;
    try { await c.put(req.url, full.clone()); } catch (err) { /* нет места — просто отдаём */ }
  }
  const range = req.headers.get('range');
  return range ? rangeResponse(full, range) : full;
}

async function rangeResponse(res, range) {
  const buf = await res.arrayBuffer();
  const size = buf.byteLength;
  const m = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
  let start = 0;
  let end = size - 1;
  if (m && m[1]) {
    start = Number(m[1]);
    if (m[2]) end = Math.min(Number(m[2]), size - 1);
  } else if (m && m[2]) {
    start = Math.max(0, size - Number(m[2]));     // bytes=-N — последние N байт
  }
  if (start >= size || start > end) {
    return new Response(null, { status: 416, headers: { 'Content-Range': 'bytes */' + size } });
  }
  return new Response(buf.slice(start, end + 1), {
    status: 206,
    statusText: 'Partial Content',
    headers: {
      'Content-Type': res.headers.get('Content-Type') || 'audio/mpeg',
      'Content-Range': 'bytes ' + start + '-' + end + '/' + size,
      'Content-Length': String(end - start + 1),
      'Accept-Ranges': 'bytes'
    }
  });
}
