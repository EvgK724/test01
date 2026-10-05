import re, json, base64, html, pathlib, sys
here = pathlib.Path("ctp")
sys.path.insert(0, str(here))
from content import TOPICS, CARDS, GROUPS, MAPS, TISSUE, CONTRAST, ERRORS, MIXED_TOPIC
tpl = (here / "template.html").read_text()
# Озвучка — остаток английского шаблона, в «КТ-перфузии» она не нужна: убираем код, как в остальных модулях.
_a, _b = tpl.index("// ——— Озвучка:"), tpl.index("// ——— Очередь")
tpl = tpl[:_a] + "function stopAudio(){}   // озвучки в этом приложении нет\n\n" + tpl[_b:]
tpl = tpl.replace('const LS_SPEAK = "ctp:autospeak";\n', "")
tpl = re.sub(r"  \.(?:say|mm-play)(?: svg)?\{[^}]*\}\n", "", tpl)
assert not re.search(r"speechSynthesis|playClip|preloadClip|LS_SPEAK|mm-play|\.say\{|new Audio", tpl)
esc = html.escape
NB = "\u00a0"
def typo(s):
    """Неразрывные пробелы и дефисы: КТ‑перфузия, 100 г, Tmax > 6 с, предлоги, тире, пропуск."""
    s = s.replace("КТ-", "КТ\u2011")
    s = re.sub(r"(\d) (?=(?:мл|г|с|ч|мг|мин|мм|лет|кг|%|секунд|час))", r"\1" + NB, s)
    s = re.sub(r" ([<>≈≥≤=/]) ", NB + r"\1" + NB, s)
    s = re.sub(r"(?<![\w-])(не|в|с|к|и|а|о|у|на|по|за|из|от|до|со|но|же) ", r"\1" + NB, s)
    s = s.replace(" — ", NB + "— ").replace(" ___", NB + "___")
    s = re.sub(r"(\d)–(\d)", "\\1–\u2060\\2", s)   # диапазон 4,5–9 не рвётся после тире
    return s
nb = lambda s: esc(typo(s))
num = lambda s: s
MARK = {"b": "good", "g": "st", "w": "hl", "p": "hl", "": "pr"}
def marked(s):
    def f(m):
        txt, _, cls = m.group(1).partition("|")
        return f'<span class="{MARK.get(cls, "pr")}">{txt}</span>'
    return re.sub(r"\[([^\]]+)\]", f, esc(typo(s)))

maps = "\n".join(
    f'            <tr><th scope="row"><span class="w pr" lang="en">{esc(w)}</span><span class="p">{nb(name)}</span></th>'
    f'<td><span class="e">{nb(what)}</span><span class="r">{num(nb(unit))}</span></td></tr>'
    for w, name, what, unit in MAPS)
def cell(v):
    f, small = v
    return f'<td><span class="f">{num(esc(f))}</span>' + (f'<small>{num(esc(small))}</small>' if small else "") + '</td>'
tissue = "\n".join(
    f'            <tr><th scope="row" lang="en">{esc(p)}</th>{cell(core)}{cell(pen)}{cell(olig)}</tr>'
    for p, core, pen, olig in TISSUE)
contrast = "\n".join(
    '        <div class="md"><div>' + "".join(f'<p class="cp-en">{marked(en)}</p><p class="cp-ru">{nb(ru)}</p>' for en, ru in rows) + '</div></div>'
    for rows in CONTRAST)
errors = "\n".join(
    f'          <li class="err"><span class="sr">Неверно:</span> <s>{num(nb(w))}</s> <span class="arr" aria-hidden="true">→</span> '
    f'<span class="sr">верно:</span> <span class="good">{num(nb(r))}</span><span class="err-note">{num(nb(note))}</span></li>'
    for w, r, note in ERRORS)
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
out = (tpl.replace("<!--__MAPS__-->", maps).replace("<!--__TISSUE__-->", tissue).replace("<!--__CONTRAST__-->", contrast)
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
print("ok", len(out), "bytes;", len(TOPICS), "topics;", len(CARDS), "cards")
