// Проверка уроков в собранной index.html: формат строк, пропуск в примере, три неверных варианта, уникальность.
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(root, 'index.html'), 'utf8');
const block = html.match(/\/\*DATA-START\*\/([\s\S]*?)\/\*DATA-END\*\//)[1];
const ctx = {};
vm.runInNewContext(block + '\n;this.UNITS = UNITS; this.parseRow = parseRow; this.allPhrases = allPhrases;', ctx);
const errs = [], warn = [], ids = new Set();
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
let n = 0;
const nums = ctx.UNITS.map(u => u.n);
if (new Set(nums).size !== nums.length) errs.push('номера уроков повторяются');
for (const u of ctx.UNITS) {
  const at = s => `урок ${u.n}: ${s}`;
  for (const k of ['n', 't', 'ru', 'idea', 's']) if (!u[k]) errs.push(at('нет поля ' + k));
  for (const sec of u.s || []) {
    if (!sec.t || !Array.isArray(sec.i) || !sec.i.length) errs.push(at('раздел без названия или строк: ' + sec.t));
    for (const r of sec.i || []) {
      n++;
      const f = r.split(' | ');
      const it = ctx.parseRow(r), w = it.w, where = at(it.cp);
      if (f.length < 4 || f.length > 5) errs.push(`${where}: полей ${f.length} (нужно 4–5)`);
      if (!/\{[^}]+\}/.test(it.c)) errs.push(`${where}: в коллокации нет {ключевого слова}`);
      if ((it.ex.match(/\[/g) || []).length !== 1 || (it.ex.match(/\]/g) || []).length !== 1) errs.push(`${where}: в примере нужна одна [коллокация]`);
      if ((it.ex.match(/\{/g) || []).length !== 1) errs.push(`${where}: в примере нужен один {пропуск}`);
      const inner = (it.ex.match(/\[(.*?)\]/) || [])[1] || '';
      if (!/\{[^}]+\}/.test(inner)) errs.push(`${where}: {пропуск} должен быть внутри [коллокации]`);
      if (!/[.!?…"”]$/.test(it.exp)) errs.push(`${where}: пример без точки в конце`);
      if (/\s{2,}|\s[,.!?]/.test(it.exp) || /\s{2,}/.test(it.ru)) errs.push(`${where}: лишние пробелы`);
      if (!it.ru) errs.push(`${where}: нет перевода`);
      if (w.length !== 3) errs.push(`${where}: неверных вариантов ${w.length}, нужно 3`);
      const low = [it.key, ...w].map(s => s.toLowerCase());
      if (new Set(low).size !== low.length) errs.push(`${where}: варианты повторяются или совпадают с ответом`);
      const cap = s => /^[A-Z]/.test(s);
      if (w.some(x => cap(x) !== cap(it.key))) warn.push(`${where}: заглавная буква у вариантов не как у ответа`);
      const id = 'u' + u.n + ':' + slug(it.cp);
      if (ids.has(id)) errs.push(`${where}: повтор коллокации в уроке`);
      ids.add(id);
      if (/[а-яё]/i.test(it.exp) || /[а-яё]/i.test(it.cp)) errs.push(`${where}: кириллица в английском`);
    }
  }
}
const phrases = ctx.allPhrases();
console.log(`уроков ${ctx.UNITS.length}, коллокаций ${n}, фраз для озвучки ${phrases.length}`);
for (const x of warn.slice(0, 30)) console.log('  ! ' + x);
if (errs.length) { for (const e of errs.slice(0, 80)) console.error('  ✗ ' + e); console.error(`ошибок: ${errs.length}`); process.exit(1); }
