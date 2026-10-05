import re, json, base64, html, pathlib, sys
here = pathlib.Path("art")
sys.path.insert(0, str(here))
from content import (TOPICS, CARDS, GROUPS, MIXED_TOPIC, SEG, VIEWS, EVT_LABEL, EVT_LEGEND, SEGTAB, CRIT, ERRORS)
from views import VIEWS_SVG
tpl = (here / "template.html").read_text()
esc = html.escape
NB = "\u00a0"

def typo(s):
    """Неразрывные пробелы и дефисы: КТ‑, 24 ч, NIHSS ≥ 6, предлоги, тире, пропуск, диапазоны."""
    s = s.replace("КТ-", "КТ\u2011")
    s = re.sub(r"(\d) (?=(?:мл|г|с|ч|мг|мин|мм|лет|кг|%|секунд|час|балл))", r"\1" + NB, s)
    s = re.sub(r" ([<>≈≥≤=/+−]) ", NB + r"\1" + NB, s)
    s = re.sub(r"(?<![\w-])(не|в|с|к|и|а|о|у|на|по|за|из|от|до|со|но|же|ли) ", r"\1" + NB, s)
    s = s.replace(" — ", NB + "— ").replace(" ___", NB + "___").replace(" · ", NB + "· ")
    s = re.sub(r"(\w)–(\w)", "\\1–\u2060\\2", s)   # M1–M4, 6–24, C6–C2 не рвутся после тире
    return s
nb = lambda s: esc(typo(s))
MARK = {"b": "good", "g": "st", "w": "hl", "p": "hl", "": "pr"}

# ——— проверки данных
svg_keys = {}
for v in VIEWS:
    svg = VIEWS_SVG[v["id"]]
    found = {}
    for m in re.finditer(r'<g class="seg([^"]*)" data-seg="([^"]+)"(?: data-evt="(\w+)")?', svg):
        cls, k, ev = m.groups()
        if "a-off" in cls: continue
        found.setdefault(k, set()).add(ev)
    assert set(found) == set(v["segs"]), (v["id"], set(found) ^ set(v["segs"]))
    for k, evs in found.items():
        assert k in SEG, k
        for ev in evs:
            if ev is None: continue
            assert "evt" in SEG[k] and SEG[k]["evt"]["c"] == ev, (v["id"], k, ev, SEG[k].get("evt", {}).get("c"))
    svg_keys[v["id"]] = set(found)
used = set().union(*svg_keys.values())
assert used == set(SEG), set(SEG) ^ used
ids = [c["id"] for c in CARDS]
assert len(ids) == len(set(ids)), "дубли id"
for c in CARDS:
    assert 1 <= c["t"] <= 8, c["id"]
    if "tap" in c:
        assert "___" not in c["q"] and c["opts"] == [] and c["a"] in svg_keys[c["tap"]["v"]], c["id"]
        assert re.search(r"\[[^\]]+\]", c["q"]), c["id"]
    else:
        assert c["q"].count("___") == 1, c["id"]
        assert c["a"] in c["opts"] and len(set(c["opts"])) == len(c["opts"]), c["id"]
    if "fig" in c:
        assert c["fig"]["hl"] in svg_keys[c["fig"]["v"]], c["id"]
    for note in (c.get("also") or {}).values():
        assert "тоже" not in note, c["id"]

# ——— типографика данных
def T(x, skip=("id", "group", "svg", "segs", "v", "hl", "c")):
    if isinstance(x, str): return typo(x)
    if isinstance(x, list): return [T(v, skip) for v in x]
    if isinstance(x, dict): return {k: (v if k in skip else T(v, skip)) for k, v in x.items()}
    return x
TOPICS, CARDS, SEG = T(TOPICS), T(CARDS), T(SEG)
for c in CARDS:
    if "tap" not in c: assert c["a"] in c["opts"], c["id"]
views = [{"id": v["id"], "chip": v["chip"], "cap": typo(v["cap"]), "intro": typo(v["intro"]), "segs": v["segs"],
          "evt": v["evt"], "svg": VIEWS_SVG[v["id"]]} for v in VIEWS]

legend = "\n".join(
    f'          <li><span class="sw sw-{c}" aria-hidden="true"></span><span><b>{nb(t)}</b><small>{nb(n)}</small></span></li>'
    for c, t, n in EVT_LEGEND)
segtab = "\n".join(
    f'            <tr><th scope="row">{esc(a)}</th><td>' + " ".join(
        f'<span class="sg-i"><b>{esc(code)}</b>{nb(name)}</span>' for code, name in items) + '</td></tr>'
    for a, items in SEGTAB)
def verdict(src, v):
    if not v: return ""
    return (f'<div class="cr-v"><span class="cr-src">{src}</span>'
            f'<span class="v v-{v[0]}">{nb(v[1])}</span></div>')
crit = "\n".join(
    f'          <li class="cr"><p class="cr-s">{nb(sit)}</p>' + verdict("КР 2024", kr) + verdict("AHA 2026", aha) + '</li>'
    for sit, kr, aha in CRIT)
errors = "\n".join(
    f'          <li class="err"><span class="sr">Неверно:</span> <s>{nb(w)}</s> <span class="arr" aria-hidden="true">→</span> '
    f'<span class="sr">верно:</span> <span class="good">{nb(r)}</span><span class="err-note">{nb(note)}</span></li>'
    for w, r, note in ERRORS)

data = ("// ——— Темы по группам: правило и примеры. […] — главное в примере (оранжевый).\n"
        f"const MIXED_TOPIC = {MIXED_TOPIC};\n"
        "const GROUPS = " + json.dumps(GROUPS, ensure_ascii=False) + ";\n"
        "const EVT_LABEL = " + json.dumps(EVT_LABEL, ensure_ascii=False) + ";\n"
        "// ——— Сосуды и области атласа: подпись, название, строки описания, показания к ВСТЭ (КР 2024 и AHA 2026)\n"
        "const SEG = " + json.dumps(SEG, ensure_ascii=False, indent=1) + ";\n"
        "// ——— Схемы: встроенный SVG, порядок кнопок сосудов\n"
        "const VIEWS = " + json.dumps(views, ensure_ascii=False) + ";\n"
        "const TOPICS = " + json.dumps(TOPICS, ensure_ascii=False, indent=1) + ";\n\n"
        "// ——— Карточки. opts — варианты, a — правильный, why — пояснение; fig — схема с выделенным сосудом, tap — покажи на схеме.\n"
        "const CARDS = " + json.dumps(CARDS, ensure_ascii=False, indent=1) + ";")
out = (tpl.replace("<!--__LEGEND__-->", legend).replace("<!--__SEGTAB__-->", segtab).replace("<!--__CRIT__-->", crit)
          .replace("<!--__ERRORS__-->", errors).replace("/*__DATA__*/", data))
for size in (180, 192):
    b64 = base64.b64encode((here / "tile" / f"icon-{size}.png").read_bytes()).decode()
    out = out.replace(f"__ICON{size}__", "data:image/png;base64," + b64)
s0 = out.index("<style>"); s1 = out.index("</style>", s0)
out = out[:s0] + re.sub(r"(?<![\w.#-])(\d+(?:\.\d+)?)px", r"calc(\1px*var(--k))", out[s0:s1]) + out[s1:]
assert "__ICON" not in out and "/*__DATA__*/" not in out and "<!--__" not in out
(here / "index.html").write_text(out)
live = pathlib.Path("_skeleton.html").read_text()
(here / "preview.html").write_text(live[:live.index("<body>") + 6] + "\n" + out + "\n</body></html>")
n_fig = sum(1 for c in CARDS if "fig" in c); n_tap = sum(1 for c in CARDS if "tap" in c)
print("ok", len(out), "bytes;", len(TOPICS), "topics;", len(CARDS), "cards (fig", n_fig, "tap", n_tap, ")")
