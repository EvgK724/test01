import re, json, base64, html, pathlib, sys
here = pathlib.Path("vits")
sys.path.insert(0, str(here))
from content import (TOPICS, CARDS, GROUPS, MIXED_TOPIC, DOSES, TARGETS, MONITOR, SAFETY, REDUCE, SPECIAL, CONTRAST, ERRORS, SOURCES)
tpl = (here / "template.html").read_text()
esc = html.escape
NB = "\u00a0"

def typo(s):
    """Неразрывные пробелы: числа с единицами, знаки сравнения, «× 1», предлоги, тире, пропуск, диапазоны."""
    s = s.replace("мета-анализ", "мета\u2011анализ").replace("рт. ст.", "рт.\u00a0ст.").replace("мм рт", "мм\u00a0рт")
    s = re.sub(r"(\d) (?=(?:мг|мл|г|ч|кг|%|мин|лет|дн|дня|дней|сут|ммоль|мкмоль|ВГН|мм|недел|месяц|мес\b|год|пациент|случа|раз))", r"\1" + NB, s)
    s = re.sub(r" ([<>≈≥≤=/−×→±÷]) ", NB + r"\1" + NB, s)
    s = s.replace(" + ", NB + "+ ")   # «статин + эзетимиб + иPCSK9» переносится после плюса
    s = s.replace("ХС ЛНП", "ХС" + NB + "ЛНП").replace("КР по ", "КР" + NB + "по" + NB)
    s = re.sub(r"(?<=[\s(«])([<>≤≥≈]) (?=\d)", r"\1" + NB, s)
    s = re.sub(r"(?<![\w-])(не|в|с|к|и|а|о|у|на|по|за|из|от|до|со|но|же|ли|при|без|для) ", r"\1" + NB, s)
    s = s.replace(" — ", NB + "— ").replace(" · ", NB + "· ")
    # перед пропуском — обычный пробел: вставленный ответ («противопоказан») должен переноситься целиком
    s = re.sub(r"\b(ОШ|ОР|ДИ|КК|ЛНП|КФК|АЛТ|ТГ|САД|УУР|УДД) (?=[\d<>≤≥≈A-C])", r"\1" + NB, s)
    s = re.sub(r"(\w)–(\w)", "\\1–\u2060\\2", s)   # 40–80, 4–12 не рвутся после тире
    return s
nb = lambda s: esc(typo(s))
MARK = {"b": "good", "g": "st", "w": "hl", "p": "hl", "": "pr"}
def marked(s):
    def f(m):
        txt, _, cls = m.group(1).partition("|")
        return f'<span class="{MARK.get(cls, "pr")}">{txt}</span>'
    return re.sub(r"\[([^\]]+)\]", f, esc(typo(s)))

# ——— проверки данных
ids = [c["id"] for c in CARDS]
assert len(ids) == len(set(ids)), "дубли id"
tn = {t["n"] for t in TOPICS}
for c in CARDS:
    assert c["t"] in tn and c["t"] != MIXED_TOPIC, c["id"]
    assert c["q"].count("___") == 1, c["id"]
    assert c["a"] in c["opts"] and len(set(c["opts"])) == len(c["opts"]), c["id"]
for t in TOPICS:
    assert t["group"] in GROUPS, t["n"]
    if t["n"] != MIXED_TOPIC: assert any(c["t"] == t["n"] for c in CARDS), t["n"]

doses = "\n".join(
    f'          <div class="dr"><span class="dk">{nb(k)}</span><span class="dv">{nb(v)}</span><span class="dd">{nb(d)}</span></div>'
    for k, v, d in DOSES)
targets = "\n".join(
    f'          <div class="tr"><span class="tk">{nb(k)}</span><span class="tv">{nb(v)}</span><span class="td">{nb(d)}</span></div>'
    for k, v, d in TARGETS)
monitor = "\n".join(
    f'          <li><p class="sw-k">{nb(k)}</p><p class="sw-v">{nb(v)}</p><p class="sw-s">{nb(src)}</p></li>'
    for k, v, src in MONITOR)
safety = "\n".join(
    f'          <li><p class="ad-k">{nb(k)}</p><p class="ad-v">{nb(v)}</p>' + (f'<p class="ad-n">{nb(n)}</p>' if n else "") + '</li>'
    for k, v, n in SAFETY)
reduce_ = "\n".join(
    f'          <li><p class="sw-k">{nb(k)}</p><p class="sw-v">{nb(v)}</p><p class="sw-s">{nb(src)}</p></li>'
    for k, v, src in REDUCE)
VERD = {"yes": "да", "maybe": "с условием", "no": "нельзя"}
special = "\n".join(
    f'          <li><p class="iv-k">{nb(k)}' + (f' <span>· {nb(cond)}</span>' if cond else "") + '</p>'
    f'<p class="iv-v v-{v}"><span class="sr">{VERD[v]}: </span>{nb(what)}</p></li>'
    for k, cond, v, what in SPECIAL)
contrast = "\n".join(
    '        <div class="md"><div>' + "".join(f'<p class="cp-en">{marked(en)}</p><p class="cp-ru">{nb(ru)}</p>' for en, ru in rows) + '</div></div>'
    for rows in CONTRAST)
errors = "\n".join(
    f'          <li class="err"><span class="sr">Неверно:</span> <s>{nb(w)}</s> <span class="arr" aria-hidden="true">→</span> '
    f'<span class="sr">верно:</span> <span class="good">{nb(r)}</span><span class="err-note">{nb(note)}</span></li>'
    for w, r, note in ERRORS)
sources = "\n".join(
    f'        <li><a href="{esc(url)}" target="_blank" rel="noopener">{esc(text)}</a></li>'
    for text, url in SOURCES)

def T(x):
    if isinstance(x, str): return typo(x)
    if isinstance(x, list): return [T(v) for v in x]
    if isinstance(x, dict): return {k: (v if k in ("id", "group") else T(v)) for k, v in x.items()}
    return x
TOPICS, CARDS = T(TOPICS), T(CARDS)
for k in CARDS: assert k["a"] in k["opts"], k["id"]
data = ("// ——— Темы по группам: правило и примеры. […] — главное в примере (оранжевый).\n"
        f"const MIXED_TOPIC = {MIXED_TOPIC};\n"
        "const GROUPS = " + json.dumps(GROUPS, ensure_ascii=False) + ";\n"
        "const TOPICS = " + json.dumps(TOPICS, ensure_ascii=False, indent=1) + ";\n\n"
        "// ——— Карточки. opts — варианты, a — правильный, why — пояснение.\n"
        "const CARDS = " + json.dumps(CARDS, ensure_ascii=False, indent=1) + ";")
out = (tpl.replace("<!--__DOSES__-->", doses).replace("<!--__TARGETS__-->", targets).replace("<!--__MONITOR__-->", monitor)
          .replace("<!--__SAFETY__-->", safety).replace("<!--__REDUCE__-->", reduce_).replace("<!--__SPECIAL__-->", special)
          .replace("<!--__CONTRAST__-->", contrast).replace("<!--__ERRORS__-->", errors).replace("<!--__SOURCES__-->", sources)
          .replace("/*__DATA__*/", data))
for size in (180, 192):
    b64 = base64.b64encode((here / "tile" / f"icon-{size}.png").read_bytes()).decode()
    out = out.replace(f"__ICON{size}__", "data:image/png;base64," + b64)
h0 = out.index('<div class="app"'); h1 = out.index("<script>", h0)
out = out[:h0] + re.sub(r"(\d)–(\d)", "\\1–&#8288;\\2", out[h0:h1]) + out[h1:]   # 40–80 мг не рвётся после тире
s0 = out.index("<style>"); s1 = out.index("</style>", s0)
out = out[:s0] + re.sub(r"(?<![\w.#-])(\d+(?:\.\d+)?)px", r"calc(\1px*var(--k))", out[s0:s1]) + out[s1:]
assert "__ICON" not in out and "/*__DATA__*/" not in out and "<!--__" not in out
(here / "index.html").write_text(out)
skel = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0;font:14px system-ui,sans-serif;background:#faf9f7}img{max-width:100%}[hidden]{display:none!important}</style></head><body>')
(here / "preview.html").write_text(skel + "\n" + out + "\n</body></html>")
print("ok", len(out), "bytes;", len(TOPICS), "topics;", len(CARDS), "cards")
