// Офлайн-кэш: свои файлы — сначала сеть (без связи — последняя сохранённая версия), записи Ryan — из кэша.
// Записей тысячи, поэтому заранее их не качаем: каждая кладётся в кэш при первом прослушивании.
// Записи Safari запрашивает кусками (заголовок Range) и не играет звук, если в ответ пришёл файл целиком, —
// поэтому в кэше лежит файл целиком, а отдаётся ровно запрошенный кусок (206). Так же сделано в noun-prepositions.
const CACHE = 'kollokatsii-v2-ryan';
const SCOPE = new URL('./', self.location.href).pathname;
const ASSETS = ['./', './index.html', './audio/index.json', './manifest.webmanifest', './icon-180.png', './icon-192.png', './icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith('kollokatsii-') && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin || !url.pathname.startsWith(SCOPE)) return;
  // Записи не меняются (имя = хэш фразы): сначала кэш
  if (/\/audio\/[0-9a-f]{8}\.mp3$/.test(url.pathname)) {
    e.respondWith(audioResponse(req));
    return;
  }
  // Свои файлы — всегда сверяясь с сервером (no-cache), без связи — из кэша
  e.respondWith(
    fetch(req, { cache: 'no-cache' }).then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then((hit) => hit || (req.mode === 'navigate' ? caches.match('./') : undefined)))
  );
});

async function audioResponse(req) {
  const c = await caches.open(CACHE);
  // Повторное нажатие после ошибки не создаёт вторую копию одной и той же записи.
  const key = new URL(req.url); key.search = '';
  let full = await c.match(key.href);
  if (!full) {
    try {
      full = await fetch(req.url);                 // без Range — файл целиком, его и кладём в кэш
    } catch (err) {
      return fetch(req);
    }
    if (!full.ok) return full;
    try { await c.put(key.href, full.clone()); } catch (err) { /* нет места — просто отдаём */ }
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
