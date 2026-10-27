#!/usr/bin/env python3
"""Сборка: units/u*.js (уроки) + tools/template.html → index.html, затем проверка данных (tools/check.mjs).
Запуск из корня репозитория: python3 kollokatsii/tools/build.py"""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

HEAD = """var UNITS = [];
function U(u) { UNITS.push(u); }
"""
TAIL = r"""
// Разбор строки урока: «коллокация | перевод | пример | три неверных слова | заметка».
// В коллокации {ключевое слово}; в примере [вся коллокация] и {слово, которое пропускается в тренировке}.
function parseRow(r) {
  var f = r.split(' | ').map(function (s) { return s.trim(); });
  var ex = f[2] || '', m = ex.match(/\{([^}]+)\}/);
  return { c: f[0], cp: f[0].replace(/[{}]/g, ''), ru: f[1] || '', ex: ex, exp: ex.replace(/[\[\]{}]/g, ''),
    key: m ? m[1] : '', w: (f[3] || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean), note: f[4] || '' };
}
// Все английские фразы — по ним GitHub Actions делает записи голосом Microsoft Ryan (tools/extract_phrases.mjs)
function allPhrases() {
  var out = [];
  UNITS.forEach(function (u) { u.s.forEach(function (s) { s.i.forEach(function (r) { var it = parseRow(r); out.push(it.cp, it.exp); }); }); });
  return out.filter(function (p, k) { return out.indexOf(p) === k; });
}
"""


def main():
    units = sorted((ROOT / "units").glob("u*.js"))
    body = HEAD + "\n".join(u.read_text().strip() for u in units) + "\n" + TAIL
    if "</" in body:
        sys.exit("В данных есть «</» — это закрыло бы <script>")
    tpl = (ROOT / "tools" / "template.html").read_text()
    if "/*__DATA__*/" not in tpl:
        sys.exit("В шаблоне нет /*__DATA__*/")
    (ROOT / "index.html").write_text(tpl.replace("/*__DATA__*/", body.strip()))
    r = subprocess.run(["node", str(ROOT / "tools" / "check.mjs")], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        print(r.stderr.strip())
        sys.exit("Проверка данных не прошла (index.html записан, но публиковать нельзя)")
    print(f"→ kollokatsii/index.html, уроков: {len(units)}")


if __name__ == "__main__":
    main()
