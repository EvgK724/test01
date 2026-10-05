import re, json, base64, html, pathlib, sys
here = pathlib.Path("thrombo")
sys.path.insert(0, str(here))
from content import (TOPICS, CARDS, GROUPS, MIXED_TOPIC, MATRIX, LEVELS, THRESH, REPERF, HIT, T4, SPECIAL, CONTRAST, ERRORS, SOURCES)
tpl = (here / "template.html").read_text()
esc = html.escape
NB = "\u00a0"
SH = "\u00ad"   # мягкий перенос в длинных словах: на узком экране слово рвётся с дефисом, а не вылезает
SHY = [(w, w.replace("|", SH)) for w in ["севдо|тромбо|цитопени", "ромбо|цитопени", "рофилакти|ческ", "невмо|компресси", "нтра|краниальн", "еморраги|ческ"]]
SHY = [(w.replace("|", ""), h) for w, h in SHY]

def typo(s):
    """Неразрывные пробелы: числа с единицами, знаки сравнения, «× 2», предлоги, тире, пропуск, диапазоны."""
    s = s.replace("мета-анализ", "мета\u2011анализ").replace("Мета-анализ", "Мета\u2011анализ")
    for w, h in SHY: s = s.replace(w, h)
    s = s.replace("½ ", "½" + NB).replace("10⁹/л", "10⁹/\u2060л")
    s = re.sub(r"(\d) (?=(?:мг|мл|г\b|ч\b|кг|%|мин|лет|дн|дня|дней|сут|ЕД|мкл|недел|месяц|год|пациент|случа|балл|раз|тыс|000|ТЛТ))", r"\1" + NB, s)
    s = re.sub(r"(?<![;,:.]) ([<>≈≥≤=/−×→±÷]) ", NB + r"\1" + NB, s)
    s = re.sub(r"(?<=[;,:.]) ([<>≈≥≤=/−×→±÷]) ", r" \1" + NB, s)   # после «;» знак начинает новую мысль — перенос перед ним разрешён
    s = s.replace(" + ", NB + "+ ")
    s = s.replace("КР по ", "КР" + NB + "по" + NB).replace("по ИИ 2024", "по" + NB + "ИИ" + NB + "2024")
    s = re.sub(r"(?<=[\s(«])([<>≤≥≈]) (?=\d)", r"\1" + NB, s)
    s = re.sub(r"^([<>≤≥≈]) (?=\d)", r"\1" + NB, s)
    s = re.sub(r"(?<![\w-])(не|в|с|к|и|а|о|у|на|по|за|из|от|до|со|но|же|ли|при|без|для) ", r"\1" + NB, s)
    s = s.replace(" — ", NB + "— ").replace(" · ", NB + "· ")
    s = re.sub(r"\b(ОШ|ОР|ДИ|NIHSS|УУР|УДД|ЕОК|EHA|EHRA|ESC|ISTH|SCAI|ASH|AABB|TRISP|TROVE|PATCH|рек\.) (?=[\d<>≤≥≈A-Z])", r"\1" + NB, s)
    s = re.sub(r"(\w)–(\w)", "\\1–\u2060\\2", s)   # 25–50 не рвётся после тире
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

LV = ["> 50", "20–50", "< 20"]
matrix = "\n".join(
    f'          <div class="mxr"><p class="mxr-k">{nb(k)}</p><div class="mxr-c">'
    + "".join(f'<span class="c-{v}"><small>{nb(LV[i])}</small>{nb(t)}</span>' for i, (v, t) in enumerate(cells))
    + '</div></div>'
    for k, cells in MATRIX)
VL = {"yes": "можно", "maybe": "с условием", "no": "нет"}
levels = "\n".join(
    f'        <div class="lvl lvl-{key}"><h3 class="lvl-h">{nb(title)}<small>{nb(sub)}</small></h3><ul class="lst">\n'
    + "\n".join(f'          <li><p class="iv-k">{nb(k)}</p><p class="iv-v v-{v}"><span class="sr">{VL[v]}: </span>{nb(what)}</p><p class="iv-n">{nb(src)}</p></li>' for k, v, what, src in rows)
    + '\n        </ul></div>'
    for key, title, sub, rows in LEVELS)
thresh = "\n".join(f'          <li><p class="sw-k">{nb(k)}</p><p class="sw-v">{nb(v)}</p><p class="sw-s">{nb(src)}</p></li>' for k, v, src in THRESH)
VERD = {"yes": "да", "maybe": "с условием", "no": "нельзя"}
def verdicts(rows):
    return "\n".join(
        f'          <li><p class="iv-k">{nb(k)}' + (f' <span>· {nb(cond)}</span>' if cond else "") + '</p>'
        f'<p class="iv-v v-{v}"><span class="sr">{VERD[v]}: </span>{nb(what)}</p></li>'
        for k, cond, v, what in rows)
reperf, hit, special = verdicts(REPERF), verdicts(HIT), verdicts(SPECIAL)
DEF = [2, 2, 0, 1]   # пример: 5 баллов
t4 = "\n".join(
    f'        <p class="fl" id="t{i}Lbl">{nb(name)}</p>\n        <div class="seg s1" role="group" aria-labelledby="t{i}Lbl">\n'
    + "\n".join(f'          <button type="button" class="chip" data-tq="{i}" data-tv="{2 - j}" aria-pressed="{str(2 - j == DEF[i]).lower()}"><b>{2 - j}</b>{nb(o)}</button>' for j, o in enumerate(opts))
    + '\n        </div>'
    for i, (name, opts) in enumerate(T4))
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
out = tpl
for key, val in [("MATRIX", matrix), ("LEVELS", levels), ("THRESH", thresh), ("REPERF", reperf), ("T4", t4), ("HIT", hit),
                 ("SPECIAL", special), ("CONTRAST", contrast), ("ERRORS", errors), ("SOURCES", sources)]:
    assert out.count(f"<!--__{key}__-->") == 1, key
    out = out.replace(f"<!--__{key}__-->", val)
out = out.replace("/*__DATA__*/", data)
for size in (180, 192):
    b64 = base64.b64encode((here / "tile" / f"icon-{size}.png").read_bytes()).decode()
    out = out.replace(f"__ICON{size}__", "data:image/png;base64," + b64)
h0 = out.index('<div class="app"'); h1 = out.index("<script>", h0)
out = out[:h0] + re.sub(r"(\d)–(\d)", "\\1–&#8288;\\2", out[h0:h1]).replace("10⁹/л", "10⁹/&#8288;л").replace("½ ", "½&nbsp;") + out[h1:]
s0 = out.index("<style>"); s1 = out.index("</style>", s0)
out = out[:s0] + re.sub(r"(?<![\w.#-])(\d+(?:\.\d+)?)px", r"calc(\1px*var(--k))", out[s0:s1]) + out[s1:]
assert "__ICON" not in out and "/*__DATA__*/" not in out and "<!--__" not in out
(here / "index.html").write_text(out)
skel = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0;font:14px system-ui,sans-serif;background:#faf9f7}img{max-width:100%}[hidden]{display:none!important}</style></head><body>')
(here / "preview.html").write_text(skel + "\n" + out + "\n</body></html>")
print("ok", len(out), "bytes;", len(TOPICS), "topics;", len(CARDS), "cards")
