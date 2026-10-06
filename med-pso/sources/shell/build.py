# Сборка объединённого приложения «Медицина ПСО», этап 1: оболочка + модули без изменений.
# Запуск из sources/: python3 shell/build.py
#
# Что делает:
#   1. Берёт тело каждого модуля — то, что сейчас публикуется отдельно:
#      генераторы → sources/<папка>/index.html; «АТТ» → ../../stroke-att/index.html (блоки APP-HEAD и APP-BODY).
#      Сверяет с site/apps/<ключ>.html (опубликованные страницы) и печатает, совпадает ли модуль.
#   2. Первой строкой добавляет мост: parent.__pso.attach("<ключ>", window) — оболочка подставит модулю
#      свой window.claude, и прогресс модуля ляжет в отдельный документ progress-<ключ>.
#   3. Собирает каталог для главной (ключи localStorage, id карточек — для счётчиков «к повторению»)
#      и поисковый индекс apps/search.json (темы, карточки; у «АТТ» ещё тезисы, случаи и тест).
#   4. Пишет ../app/: shell.html — страница для публикации (без каркаса), index.html — она же с каркасом
#      (открыть локально: cd ../app && python3 -m http.server), apps/<ключ>.html, apps/search.json, apps/icons/.
import json, re, html, pathlib, subprocess, datetime
from PIL import Image

HERE = pathlib.Path("shell")
ROOT = pathlib.Path("..")
OUT = ROOT / "app"
(OUT / "apps" / "icons").mkdir(parents=True, exist_ok=True)
CAT = json.loads((ROOT / "catalog.json").read_text())
SKEL = pathlib.Path("_skeleton.html").read_text()
SK_HEAD = SKEL[:SKEL.index("<body>") + len("<body>")]
ATT_SRC = ROOT / ".." / "stroke-att" / "index.html"   # исходник «АТТ» в репозитории test01
BRIDGE = '<script>try{parent.__pso.attach("%s",window)}catch(e){}</script>\n'
dec = json.JSONDecoder()

def published(key):
    """Тело модуля из опубликованной страницы site/apps/<ключ>.html (каркас claude.ai снят)."""
    page = (ROOT / "site" / "apps" / f"{key}.html").read_text()
    assert page.startswith(SK_HEAD + "\n") and page.endswith("\n</body></html>"), key
    return page[len(SK_HEAD) + 1:-len("\n</body></html>")]

def att_body():
    s = ATT_SRC.read_text()
    head = re.search(r"<!--APP-HEAD-->(.*?)<!--/APP-HEAD-->", s, re.S).group(1)
    body = re.search(r"<!--APP-BODY-->(.*?)<!--/APP-BODY-->", s, re.S).group(1)
    return head.strip() + "\n" + body.strip() + "\n", s

def grab(s, name):
    i = s.find("const " + name + " = ")
    if i < 0: return None
    return dec.raw_decode(s, i + len("const " + name + " = "))[0]

def att_data(src):
    js = r"""
const fs = require('fs'); const s = fs.readFileSync(process.argv[1], 'utf8');
const d = s.slice(s.indexOf('/*DATA-START*/'), s.indexOf('/*DATA-END*/'));
const o = new Function(d + ';return {TOPICS,REVIEW,CARDS,CASES,TEST};')();
process.stdout.write(JSON.stringify(o));
"""
    return json.loads(subprocess.run(["node", "-e", js, str(src)], capture_output=True, text=True, check=True).stdout)

def plain(s):
    """HTML из «АТТ» → обычный текст для поиска и показа."""
    return html.unescape(re.sub(r"<[^>]+>", "", s))

def unmark(s):
    """Разметка примеров [текст|b] → текст."""
    return re.sub(r"\[([^\]|]+)(?:\|\w)?\]", r"\1", s)

apps, index, report = [], {}, []
for a in CAT["apps"]:
    key = a["key"]
    pub = published(key)
    if a["generator"]:
        folder = pathlib.Path(a["generator"].replace("sources/", "")).name
        body = (pathlib.Path(folder) / "index.html").read_text()
        T, C = grab(body, "TOPICS"), grab(body, "CARDS")
        mixed = grab(body, "MIXED_TOPIC")
        topics = [{"n": t["n"], "title": t["title"], "sub": t.get("sub", ""), "text": t.get("rule", "")} for t in T if t["n"] != mixed]
        tnames = {t["n"]: t["title"] for t in T}
        cards = [{"id": c["id"], "t": c["t"], "q": c["q"], "a": c["a"], "why": c.get("why", "")} for c in C]
        ids = [c["id"] for c in C]
        kind, extra = "gen", ""
        ls = a["localStorage"]["LS_STATE"]
    else:
        body, src = att_body()
        D = att_data(ATT_SRC)
        tnames = {k: v["name"] for k, v in D["TOPICS"].items()}
        topics = [{"n": k, "title": v["name"], "sub": "трудные места",
                   "text": "\n\n".join(plain(p["t"]) for p in D["REVIEW"].get(k, []))} for k, v in D["TOPICS"].items()]
        cards = [{"id": c["id"], "t": c["t"], "q": plain(c["q"]), "a": plain(c["a"]), "why": ""} for c in D["CARDS"]]
        cards += [{"id": f"case{i + 1}", "t": c["t"], "kind": "case", "q": plain(c["text"]) + " " + plain(c["q"]),
                   "a": plain(c["opts"][c["a"]]), "why": plain(c["why"])} for i, c in enumerate(D["CASES"])]
        cards += [{"id": f"test{i + 1}", "t": c["t"], "kind": "test", "q": plain(c["q"]),
                   "a": plain(c["opts"][c["a"]]), "why": plain(c["why"])} for i, c in enumerate(D["TEST"])]
        ids = [c["id"] for c in D["CARDS"]]
        kind = "att"
        extra = f"{len(D['CASES'])} случаев · тест {len(D['TEST'])}"
        ls = a["localStorage"]["LS_KEY"]
    assert len(ids) == len(set(ids)), key
    same = body == pub
    report.append(f"{key:12} {'как опубликовано' if same else 'ИЗМЕНЁН относительно site/apps'} · тем {len(topics)} · карточек {len(ids)}")
    (OUT / "apps" / f"{key}.html").write_text(BRIDGE % key + body)
    for t in topics:
        t["title"] = unmark(t["title"])
    index[key] = {"topics": topics, "names": tnames, "cards": cards}
    icon = ROOT / "tiles" / f"{key}-icon.png"
    if not icon.exists(): icon = HERE / f"tile-{key}" / "icon-400.png"   # у «АТТ» иконка своя, из shell/tile-att
    Image.open(icon).convert("RGB").resize((144, 144), Image.LANCZOS).save(OUT / "apps" / "icons" / f"{key}.png", optimize=True)
    apps.append({"key": key, "title": a["title"], "label": a["label"], "desc": a["desc"], "group": a["group"],
                 "kind": kind, "ls": ls, "ids": ids, "topics": len(topics), "extra": extra,
                 "kw": " ".join(t["title"] for t in topics)})

(OUT / "apps" / "search.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")))
catalog = {"groups": [[k, v] for k, v in CAT["groups"].items()], "apps": apps,
           "built": datetime.date.today().isoformat()}
shell = (HERE / "shell.html").read_text().replace("/*__CATALOG__*/", json.dumps(catalog, ensure_ascii=False, separators=(",", ":")))
assert "/*__" not in shell
(OUT / "shell.html").write_text(shell)
# index.html — для локального просмотра и GitHub Pages: плюс иконка и подпись «ПСО» для экрана «Домой»
Image.open(HERE / "tile" / "icon-180.png").save(OUT / "apps" / "icons" / "pso-180.png", optimize=True)
HOME = ('<link rel="apple-touch-icon" href="apps/icons/pso-180.png"><meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black"><meta name="apple-mobile-web-app-title" content="ПСО">'
        '<meta name="theme-color" content="#0e1113">')
assert SK_HEAD.count("</head>") == 1
(OUT / "index.html").write_text(SK_HEAD.replace("</head>", HOME + "</head>") + "\n" + shell + "\n</body></html>\n")
for line in report: print(line)
sizes = {p.name: p.stat().st_size for p in sorted((OUT / "apps").glob("*.*"))}
print("shell.html", (OUT / "shell.html").stat().st_size, "· search.json", sizes["search.json"],
      "· модули", sum(v for k, v in sizes.items() if k.endswith(".html")))
