// Mock-based regression tests. They do not certify MP3 decoding or audible Ryan playback.
// Run: node --test kollokatsii/tools/test_audio.mjs
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const template = readFileSync(new URL('tools/template.html', root), 'utf8');
const html = readFileSync(new URL('index.html', root), 'utf8');
const swSource = readFileSync(new URL('sw.js', root), 'utf8');
const manifest = JSON.parse(readFileSync(new URL('phrases.json', root), 'utf8'));
const data = html.match(/\/\*DATA-START\*\/([\s\S]*?)\/\*DATA-END\*\//)?.[1];
assert.ok(data, 'Built app must contain its data block');
const corpus = vm.runInNewContext(data + '\n;({units: UNITS, parse: parseRow, phrases: allPhrases()});');
const voiceSection = source => {
  const start = source.indexOf('function fnv(s) {');
  const end = source.indexOf('// ---------- Состояние ----------', start);
  assert.ok(start >= 0 && end > start, 'Audio section boundaries were changed; update the harness');
  return source.slice(start, end);
};
const audioSource = voiceSection(template);
const texts = Array.from(corpus.phrases);
const tick = async () => { for (let i = 0; i < 8; i++) await Promise.resolve(); };
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return {promise, resolve, reject};
}
function fnv(text) {
  let h = 0x811c9dc5;
  for (const byte of Buffer.from(text, 'utf8')) h = Math.imul(h ^ byte, 0x01000193) >>> 0;
  return h.toString(16).padStart(8, '0');
}
const goodManifest = {voice: 'en-GB-RyanNeural', files: texts.map(fnv)};
const response = body => ({ok: true, json: async () => body});

function player({fetch = async () => response(goodManifest), storage = {}} = {}) {
  const audios = [], plays = [], toasts = [], deviceSpeech = [], events = new Map(), docEvents = new Map();
  const values = new Map(Object.entries(storage)), timers = new Map();
  let timerId = 0;
  class MockAudio {
    constructor() { this.paused = true; this.loads = 0; this.pending = deferred(); audios.push(this); }
    play() { this.paused = false; plays.push({src: this.src, rate: this.playbackRate}); return this.pending.promise; }
    pause() { this.paused = true; }
    removeAttribute(name) { if (name === 'src') this.src = ''; }
    load() { this.loads++; }
    succeed() { this.onplaying?.(); this.pending.resolve(); }
    fail(name = 'NotAllowedError') { const error = new Error('Mock playback failure'); error.name = name; this.pending.reject(error); }
  }
  const document = {visibilityState: 'visible', addEventListener: (name, fn) => docEvents.set(name, fn)};
  const context = vm.createContext({
    TextEncoder, AbortController, Audio: MockAudio, fetch, Date, document,
    allPhrases: () => texts,
    store: {get: key => values.get(key) ?? null, set: (key, value) => values.set(key, value)},
    toast: text => toasts.push(text), syncSettings: () => {},
    setTimeout: fn => { timers.set(++timerId, fn); return timerId; },
    clearTimeout: id => timers.delete(id),
    addEventListener: (name, fn) => events.set(name, fn),
    speechSynthesis: {speak: value => deviceSpeech.push(value), cancel: () => {}},
    SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
  });
  context.window = context;
  vm.runInContext(audioSource + '\n;globalThis.api = {voice, speak, set, fnv};', context);
  const nav = template.match(/function setTab\(t\) \{[^\n]*\}\nfunction openUnit\(n\) \{[^\n]*\}/)?.[0];
  assert.ok(nav, 'Navigation functions must be tested from app source');
  vm.runInContext('const state = {tab:"units", unit:0, open:{}};\n' + nav + '\n;Object.assign(api, {setTab, openUnit, state});', context);
  return {...context.api, audios, plays, toasts, deviceSpeech, events, docEvents, document, values, timers};
}

test('built audio matches template; every term/example is in phrases.json without hash or progress-ID collisions', () => {
  assert.equal(voiceSection(html), audioSource, 'Rebuild index.html after changing the template');
  const wanted = new Set(), ids = new Set();
  for (const unit of corpus.units) for (const section of unit.s) for (const row of section.i) {
    const fields = row.split(' | ').map(value => value.trim());
    const term = fields[0].replace(/[{}]/g, ''), example = fields[2].replace(/[\[\]{}]/g, '');
    wanted.add(term); wanted.add(example);
    const id = 'u' + unit.n + ':' + term.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    assert.ok(!ids.has(id), `Duplicate progress ID: ${id}`); ids.add(id);
  }
  assert.equal(manifest.voice, 'en-GB-RyanNeural');
  assert.equal(manifest.phrases.length, new Set(manifest.phrases).size);
  assert.deepEqual(new Set(manifest.phrases), wanted);
  const hashes = new Map();
  for (const text of wanted) { const hash = fnv(text); assert.ok(!hashes.has(hash), `FNV collision: ${text} / ${hashes.get(hash)}`); hashes.set(hash, text); }
  const p = player();
  assert.equal(p.fnv('hello'), '4f9f2cab');
  for (const text of wanted) assert.equal(p.fnv(text), fnv(text), `UTF-8 hash mismatch: ${text}`);
});

test('a click plays immediately while manifest is pending; unknown text never plays', async () => {
  const pending = deferred(), p = player({fetch: () => pending.promise});
  p.speak(texts[0]);
  assert.equal(p.plays.length, 1, 'Must call play synchronously in the user gesture');
  assert.equal(p.plays[0].src, `audio/${fnv(texts[0])}.mp3`);
  assert.equal(p.voice.files, null);
  p.speak('An unknown phrase that is not part of this course.');
  assert.equal(p.plays.length, 1);
  assert.equal(p.audios[0].paused, true);
  pending.resolve(response(goodManifest)); await tick();
  assert.ok(p.voice.files.has(fnv(texts[0])));
  assert.deepEqual(p.deviceSpeech, []);
});

test('playback failure is reported without device TTS; retry uses the same Ryan recording and clears after success', async () => {
  const p = player(); await tick();
  p.speak(texts[0]); p.audios[0].fail(); await tick();
  assert.equal(p.toasts.length, 1);
  assert.ok(p.voice.failed.has(fnv(texts[0])));
  assert.deepEqual(p.deviceSpeech, []);
  p.speak(texts[0]);
  assert.match(p.plays[1].src, new RegExp(`^audio/${fnv(texts[0])}\\.mp3\\?retry=\\d+$`));
  p.audios[1].succeed(); await tick();
  assert.ok(!p.voice.failed.has(fnv(texts[0])));
  p.speak(texts[0]); assert.equal(p.plays[2].src, `audio/${fnv(texts[0])}.mp3`);
});

test('switching clips cancels the old audio and ignores stale error events and promise rejections', async () => {
  const p = player(); await tick(); p.speak(texts[0]);
  const first = p.audios[0], staleError = first.onerror;
  p.speak(texts[1]); const second = p.audios[1];
  assert.equal(first.paused, true); assert.equal(first.src, ''); assert.equal(first.loads, 1);
  assert.equal(first.onerror, null); assert.equal(first.onplaying, null);
  staleError(new Error('Late old media event')); first.fail('NetworkError'); await tick();
  assert.equal(p.voice.audio, second); assert.equal(second.paused, false);
  assert.equal(p.toasts.length, 0); assert.equal(p.voice.failed.size, 0);
  second.fail('AbortError'); await tick(); assert.equal(p.toasts.length, 0);
  assert.deepEqual(p.deviceSpeech, []);
});

test('a manifest for a different voice cannot authorise or optimistically play that recording', async () => {
  const p = player({fetch: async () => response({...goodManifest, voice: 'en-US-OtherNeural'})}); await tick();
  p.speak(texts[0]); assert.equal(p.plays.length, 0);
  assert.deepEqual(p.deviceSpeech, []);
});

test('an absent indexed recording requests a manifest refresh without fallback, then a later click can play', async () => {
  let calls = 0;
  const p = player({fetch: async () => response(++calls === 1 ? {voice: goodManifest.voice, files: []} : goodManifest)});
  await tick(); p.speak(texts[0]); assert.equal(p.plays.length, 0); await tick();
  p.speak(texts[0]); assert.equal(p.plays.length, 1);
  assert.equal(calls, 2); assert.deepEqual(p.deviceSpeech, []);
});

test('tab/unit navigation, pagehide and hidden document stop playback without changing study progress', async () => {
  const saved = JSON.stringify({'u6:highly-unlikely': {b: 2, d: 20261030, n: 7}});
  const p = player({storage: {'kol:srs': saved, 'kol:slow': '1'}}); await tick();
  for (const leave of [() => p.setTab('cards'), () => p.openUnit(14), () => p.events.get('pagehide')(), () => { p.document.visibilityState = 'hidden'; p.docEvents.get('visibilitychange')(); }]) {
    p.speak(texts[0]); const current = p.voice.audio;
    assert.equal(p.plays.at(-1).rate, 0.82);
    leave(); assert.equal(current.paused, true); assert.equal(current.src, ''); assert.equal(p.voice.audio, null);
  }
  assert.equal(p.values.get('kol:srs'), saved);
  assert.equal(p.values.get('kol:slow'), '1');
});

function worker({keys = [], offline = false} = {}) {
  const origin = 'https://evgk724.github.io', base = origin + '/test01/kollokatsii/';
  const events = new Map(), buckets = new Map(keys.map(key => [key, new Map()])), deleted = [], fetched = [];
  const absolute = request => new URL(typeof request === 'string' ? request : request.url, base).href;
  const fetch = async request => {
    fetched.push(request); if (offline) throw new Error('Mock network offline');
    return new Response(Uint8Array.from([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]), {headers: {'Content-Type': 'audio/mpeg'}});
  };
  const cacheFor = name => {
    if (!buckets.has(name)) buckets.set(name, new Map());
    const values = buckets.get(name);
    return {
      addAll: async () => {},
      match: async request => values.get(absolute(request))?.clone(),
      put: async (request, response) => values.set(absolute(request), response.clone()),
    };
  };
  const context = {URL, Response, Request, Headers, fetch, self: {
    location: {origin, href: base + 'sw.js'}, clients: {claim: async () => {}}, skipWaiting: async () => {},
    addEventListener: (name, handler) => events.set(name, handler),
  }, caches: {
    keys: async () => [...buckets.keys()], open: async name => cacheFor(name),
    delete: async name => { deleted.push(name); return buckets.delete(name); },
    match: async request => { for (const name of buckets.keys()) { const hit = await cacheFor(name).match(request); if (hit) return hit; } },
  }};
  vm.runInNewContext(swSource + '\n;globalThis.cacheName = CACHE;', context);
  return {base, deleted, fetched, buckets, cacheName: context.cacheName, offline: value => { offline = value; },
    async activate() { let pending; events.get('activate')({waitUntil: p => { pending = p; }}); await pending; },
    request(path, range, method = 'GET') {
      const request = new Request(new URL(path, base), {method, headers: range ? {Range: range} : {}});
      let pending; events.get('fetch')({request, respondWith: value => { pending = value; }}); return pending;
    },
  };
}

test('SW activation preserves neighbour caches and does not intercept neighbouring apps', async () => {
  const w = worker({keys: ['kollokatsii-v0', 'noun-prep-v1', 'medusa-v3', 'englex-pocket-shell']});
  w.buckets.set(w.cacheName, new Map()); await w.activate();
  assert.deepEqual(w.deleted, ['kollokatsii-v0']);
  for (const key of ['noun-prep-v1', 'medusa-v3', 'englex-pocket-shell', w.cacheName]) assert.ok(w.buckets.has(key));
  for (const path of ['/test01/noun-prepositions/index.html', '/Englex-Pocket/', '/test01/kollokatsii-other/', 'https://example.com/']) assert.equal(w.request(path), undefined);
  assert.equal(w.request('index.html', null, 'POST'), undefined);
  assert.equal((await w.request('index.html')).status, 200);
});

test('SW caches the whole Ryan file once; offline Safari ranges return exact bytes and 416', async () => {
  const w = worker(), file = 'audio/01234567.mp3';
  const first = await w.request(file, 'bytes=0-1');
  assert.equal(first.status, 206); assert.equal(first.headers.get('Content-Range'), 'bytes 0-1/10');
  assert.equal(first.headers.get('Content-Length'), '2'); assert.deepEqual([...new Uint8Array(await first.arrayBuffer())], [0, 1]);
  assert.equal(typeof w.fetched[0], 'string', 'Cache miss fetch must omit the original Range header');
  assert.equal(w.buckets.get(w.cacheName).size, 1); w.offline(true);
  for (const [range, expected, contentRange] of [['bytes=4-', [4,5,6,7,8,9], 'bytes 4-9/10'], ['bytes=-3', [7,8,9], 'bytes 7-9/10'], ['bytes=8-99', [8,9], 'bytes 8-9/10']]) {
    const result = await w.request(file + '?retry=123', range);
    assert.equal(result.status, 206); assert.equal(result.headers.get('Content-Range'), contentRange);
    assert.deepEqual([...new Uint8Array(await result.arrayBuffer())], expected);
  }
  for (const range of ['bytes=10-', 'bytes=8-3']) { const result = await w.request(file, range); assert.equal(result.status, 416); assert.equal(result.headers.get('Content-Range'), 'bytes */10'); }
  assert.equal((await w.request(file)).status, 200);
  assert.equal(w.fetched.length, 1); assert.equal(w.buckets.get(w.cacheName).size, 1);
});
