# Шаблон «Артерии мозга» собираю из шаблона «КТ-перфузия»: тренажёр тот же (русский, без озвучки),
# вкладка «Атлас» — интерактивные схемы сосудов, окраска по показаниям к ВСТЭ, счёт ASPECTS,
# шаги принятия решения о ВСТЭ, шпаргалка сегментов, критерии КР 2024 и AHA 2026, ловушки, темы.
# В тренировке — карточки со схемой: «что выделено» и «покажи на схеме».
import pathlib
s = pathlib.Path("ctp/template.html").read_text()
atlas_css = pathlib.Path("art/atlas.css").read_text()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:70], s.count(a))
    s = s.replace(a, b)

def cut(a, b_marker, keep_b=True, repl=""):
    global s
    i = s.index(a); j = s.index(b_marker, i)
    s = s[:i] + repl + (s[j:] if keep_b else s[j + len(b_marker):])

rep("<title>КТ-перфузия</title>", "<title>Артерии мозга</title>")
rep("  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n",
    "  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n  [hidden]{display:none!important}   /* скрытое остаётся скрытым и вне оболочки артефакта */\n")

# ——— стили: схемы (atlas.css) и интерфейс атласа
CSS = atlas_css + r"""
  .atlas{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:12px 12px 14px}
  .vchips{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
  .vchip{min-height:44px;padding:0 6px;border-radius:12px;border:1px solid var(--line-2);background:transparent;color:var(--soft);font-size:15px;cursor:pointer}
  .vchip[aria-pressed="true"]{background:var(--raise);color:var(--text);border-color:var(--accent)}
  .v-cap{margin:12px 2px 0;font-size:13px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--blue)}
  .stage{position:relative;margin:4px -6px 0;border-radius:16px;background:radial-gradient(ellipse at 50% 45%,rgba(124,192,221,.07),rgba(124,192,221,0) 70%)}
  .stage .art{max-height:72vh}
  @media (hover:hover){.stage .art .seg:not(.on):hover .ln{stroke:#ffffff}.stage .art .reg:not(.on):not(.x):hover .area{fill:rgba(255,255,255,.14)}}
  .tools{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:6px}
  .tog{min-height:44px;display:inline-flex;align-items:center;gap:9px;padding:0 16px 0 14px;border-radius:999px;border:1px solid var(--line-2);background:transparent;color:var(--soft);font-size:15px;cursor:pointer}
  .tog[aria-pressed="true"]{border-color:var(--accent);color:var(--text);background:rgba(217,119,87,.1)}
  .tog-dot{width:10px;height:10px;border-radius:50%;background:var(--line-2)}
  .tog[aria-pressed="true"] .tog-dot{background:var(--accent);box-shadow:0 0 8px rgba(217,119,87,.8)}
  .asp-score{font-size:15px;color:var(--soft);font-variant-numeric:tabular-nums}
  .asp-score b{margin-left:2px;font-family:var(--serif);font-weight:400;font-size:28px;line-height:1;color:var(--text)}
  .mini{min-height:44px;padding:0 14px;border-radius:12px;border:1px solid var(--line-2);background:transparent;color:var(--soft);font-size:15px;cursor:pointer}
  .mini:disabled{opacity:.45;cursor:default}
  .legend-e{list-style:none;margin:10px 0 0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 12px}
  .legend-e li{display:grid;grid-template-columns:14px minmax(0,1fr);gap:8px;align-items:start}
  .legend-e .sw{width:14px;height:6px;margin-top:8px;border-radius:3px}
  .legend-e b{display:block;font-size:14px;font-weight:600;line-height:1.3;color:var(--text)}
  .legend-e small{display:block;font-size:12px;line-height:1.3;color:var(--muted)}
  .sw-yes{background:var(--e-yes);box-shadow:0 0 6px rgba(61,220,132,.8)}.sw-maybe{background:var(--e-maybe)}.sw-no{background:var(--e-no)}.sw-na{background:var(--e-na)}
  .info{margin-top:12px;padding:12px 14px 14px;border-radius:16px;background:var(--bg);border:1px solid var(--line);scroll-margin:12px}
  .i-intro{margin:0;font-size:16px;line-height:1.5;color:var(--soft)}
  .i-name{margin:0;font-family:var(--serif);font-weight:400;font-size:23px;line-height:1.25;text-wrap:balance}
  .badge{display:inline-block;margin:8px 0 0;padding:3px 11px;border-radius:999px;font-size:13px;font-weight:600;border:1px solid currentColor}
  .b-yes{color:var(--e-yes);background:rgba(61,220,132,.12)}
  .b-maybe{color:var(--e-maybe);background:rgba(255,210,63,.1)}
  .b-no{color:var(--e-no);background:rgba(255,90,95,.1)}
  .b-na{color:#a3adb2;background:rgba(147,158,163,.08)}
  .i-rows{margin:4px 0 0}
  .i-rows dt{margin-top:10px;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--blue)}
  .i-rows dd{margin:3px 0 0;font-size:16px;line-height:1.45;color:var(--soft);text-wrap:pretty}
  .i-evt{margin-top:12px;padding-top:2px;border-top:1px solid var(--line)}
  .i-evt dt{color:var(--text)}
  .s-h{margin:14px 2px 6px;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
  .schips{display:flex;flex-wrap:wrap;gap:6px}
  .schip{min-height:44px;min-width:48px;padding:0 12px;border-radius:12px;border:1px solid var(--line-2);background:transparent;color:var(--soft);font-size:15px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px}
  .schip[aria-pressed="true"]{border-color:var(--accent);color:var(--text);background:rgba(217,119,87,.12)}
  .evt-on .schip[data-evt]::before{content:"";width:10px;height:10px;border-radius:50%;background:var(--e-na)}
  .evt-on .schip[data-evt="yes"]::before{background:var(--e-yes);box-shadow:0 0 6px rgba(61,220,132,.8)}
  .evt-on .schip[data-evt="maybe"]::before{background:var(--e-maybe)}
  .evt-on .schip[data-evt="no"]::before{background:var(--e-no)}
  .art .reg.x .area{fill:rgba(233,167,160,.55);stroke:#e9a7a0}
  .crit{list-style:none;margin:0;padding:0}
  .cr{padding:11px 14px 12px;border-top:1px solid var(--line)}
  .cr:first-child{border-top:0}
  .cr-s{margin:0 0 5px;font-family:var(--serif);font-size:18px;line-height:1.3}
  .cr-v{display:grid;grid-template-columns:74px minmax(0,1fr);gap:8px;align-items:baseline;margin-top:4px}
  .cr-src{font-size:12px;font-weight:600;letter-spacing:.03em;color:var(--muted)}
  .v{font-size:15px;line-height:1.4}
  .v::before{content:"";display:inline-block;width:8px;height:8px;margin-right:7px;border-radius:50%;background:currentColor;vertical-align:1px}
  .v-yes{color:var(--e-yes)}.v-maybe{color:var(--e-maybe)}.v-no{color:var(--e-no)}.v-na{color:#a3adb2}
  .sg{width:100%;border-collapse:collapse}
  .sg th{width:62px;padding:11px 6px 11px 14px;vertical-align:top;text-align:left;font-family:var(--serif);font-weight:400;font-size:20px;line-height:1.3;color:var(--accent);border-top:1px solid var(--line)}
  .sg td{padding:11px 14px 11px 0;border-top:1px solid var(--line);font-size:15px;line-height:1.55;color:var(--soft)}
  .sg tr:first-child th,.sg tr:first-child td{border-top:0}
  .sg-i{display:inline-block;margin-right:12px}
  .sg-i b{margin-right:5px;font-weight:600;color:var(--text)}
  .src{margin:22px 2px 4px;font-size:13px;line-height:1.5;color:var(--muted)}
  .fig{margin:0 -8px}
  .fig .art{height:min(30vh,300px);transition:height .25s ease}
  .fig .art .reg .area{fill:rgba(255,255,255,.06);stroke:#56626a}
  .fig .art .reg.on .area{fill:rgba(217,119,87,.6);stroke:#d97757}
  .fig .art .vl{display:none}
  body:not(.tab):not(.wide) .fig.shown .art{height:min(22vh,220px)}
  .fig .art .seg.ok .ln{stroke:#9ad0b4;filter:drop-shadow(0 0 5px rgba(154,208,180,.7))}
  .fig .art .seg.bad .ln{stroke:#e9a7a0}
  .fig .art .reg.ok .area{fill:rgba(154,208,180,.55);stroke:#9ad0b4}
  .fig .art .reg.bad .area{fill:rgba(233,167,160,.5);stroke:#e9a7a0}
  .tapmode .art .seg:not(.a-off){cursor:pointer}
  .tapmode .art .seg:focus,.tapmode .art .seg:focus-visible{outline:none}
  .tapmode .art .seg:focus-visible .ln{stroke:#ffffff}
  .q .pr{color:var(--accent)}
  #check:disabled{opacity:.45;cursor:default}
"""
rep("  /* ——— Планшет */\n", CSS + "\n  /* ——— Планшет */\n")
rep("  body.wide .r-right .lbl:first-child{margin-top:14px}\n",
    "  body.wide .r-right .lbl:first-child{margin-top:14px}\n"
    "  body.wide #rule{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr)}\n"
    "  body.tab .fig .art{height:min(34vh,380px)}\n"
    "  body.tab .fig .art .vl.dim,body.wide .fig .art .vl.dim,body.tab .fig.shown .art .vl,body.wide .fig.shown .art .vl{display:inline}\n"
    "  body.wide .card.has-fig{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);grid-template-rows:auto auto auto minmax(0,1fr);column-gap:22px;row-gap:14px;align-content:start}\n"
    "  body.wide .card.has-fig .fig{grid-column:1;grid-row:1 / span 4;margin:0;align-self:center}\n"
    "  body.wide .card.has-fig .fig .art{height:min(64vh,520px)}\n"
    "  body.wide .card.has-fig .kind{grid-column:2;grid-row:1}\n"
    "  body.wide .card.has-fig .q{grid-column:2;grid-row:2;font-size:22px}\n"
    "  body.wide .card.has-fig .hint{grid-column:2;grid-row:3}\n"
    "  body.wide .card.has-fig .back{grid-column:2;grid-row:3}\n")
rep("@media (prefers-reduced-motion:reduce){.bar-fill,.t-chev{transition:none}.big:active,.opt:active{transform:none}}",
    "@media (prefers-reduced-motion:reduce){.bar-fill,.t-chev,.art .ln,.art .reg .area,.fig .art{transition:none}.big:active,.opt:active{transform:none}}")

# ——— вкладки и карточка тренировки
rep('aria-controls="rule">Правила</button>', 'aria-controls="rule">Атлас</button>')
rep('      <span class="kind" id="kind">Тема 1</span>\n',
    '      <span class="kind" id="kind">Тема 1</span>\n      <div class="fig" id="fig" hidden></div>\n')
rep('''    <div class="actions" id="actNext" hidden>''',
    '''    <div class="actions" id="actCheck" hidden>
      <button class="big primary" id="check" type="button" disabled>Проверить</button>
    </div>
    <div class="actions" id="actNext" hidden>''')
rep('<button class="big" id="toRule" type="button">Правила</button>', '<button class="big" id="toRule" type="button">Атлас</button>')

def step(n, title, formula):
    return f'          <li><span class="sn">{n}</span><div><p class="s-t">{title}</p><p class="s-f">{formula}</p></div></li>\n'
D = '&nbsp;<span class="sep">·</span> '
nw = lambda t: f'<span class="nw">{t}</span>'
steps = (step(1, "КТ или МРТ", "заключение за&nbsp;40&nbsp;мин" + D + "нет крови" + D + "ASPECTS")
         + step(2, "КТА с&nbsp;уровня дуги аорты", "сразу" + D + "креатинин не&nbsp;ждать")
         + step(3, "Тромболизис", "при показаниях" + D + nw("КТА его не&nbsp;задерживает"))
         + step(4, "Найди окклюзию", "ВСА" + D + "M1" + D + "M2" + D + "ОА" + D + "ПА" + D + "ЗМА" + D + "шея")
         + step(5, "Прими решение о&nbsp;ВСТЭ", "время" + D + "NIHSS" + D + "ASPECTS" + D + nw("критерии КР&nbsp;2024"))
         + step(6, "Вызови ангиографическую службу", "сразу" + D + nw("эффект ТЛТ не&nbsp;ждать")))

a = s.index('    <div class="r-left">'); b = s.index('  </section>\n</div>')
s = s[:a] + '''    <div class="r-left">
      <h1 class="r-title">Артерии мозга</h1>
      <p class="r-sub">Анатомия для ПСО: по&nbsp;КТА найти окклюзию, понять, что страдает, и&nbsp;принять решение о&nbsp;ВСТЭ. Критерии&nbsp;— по&nbsp;<b>КР&nbsp;МЗ&nbsp;РФ&nbsp;2024</b> и&nbsp;<b>AHA/ASA&nbsp;2026</b>.</p>
      <div class="atlas" id="atlas">
        <div class="vchips" id="vchips" role="group" aria-label="Схема"></div>
        <p class="v-cap" id="vCap"></p>
        <div class="stage" id="stage"></div>
        <div class="tools" id="tools">
          <button class="tog" id="evtTog" type="button" aria-pressed="false"><span class="tog-dot" aria-hidden="true"></span>Показания к&nbsp;ВСТЭ</button>
          <button class="tog" id="aspTog" type="button" aria-pressed="false" hidden><span class="tog-dot" aria-hidden="true"></span>Считать баллы</button>
          <span class="asp-score" id="aspScore" hidden>ASPECTS <b>10</b></span>
          <button class="mini" id="aspReset" type="button" hidden>Сбросить</button>
        </div>
        <ul class="legend-e" id="evtLegend" hidden>
<!--__LEGEND__-->
        </ul>
        <div class="info" id="info" aria-live="polite"></div>
        <p class="s-h" id="segHead">Все сосуды схемы</p>
        <div class="schips" id="schips" role="group" aria-labelledby="segHead"></div>
      </div>
      <div class="algo algo-2">
        <p class="algo-h">Решение о&nbsp;ВСТЭ&nbsp;— по&nbsp;шагам</p>
        <ol class="steps">
''' + steps + '''        </ol>
        <p class="algo-note">Решение о&nbsp;ВСТЭ принимает невролог ПСО, техническую возможность оценивает рентгенэндоваскулярный хирург. В&nbsp;окне 6–24&nbsp;ч по&nbsp;КР&nbsp;2024 нужна КТ‑перфузия или мультифазная КТА.</p>
      </div>
      <div class="go-wrap"><button class="big primary" id="go" type="button">Начать тренировку</button></div>
    </div>
    <div class="r-right">
      <h2 class="lbl">Сегменты&nbsp;— шпаргалка</h2>
      <div class="mx-wrap">
        <table class="sg">
          <tbody>
<!--__SEGTAB__-->
          </tbody>
        </table>
      </div>
      <h2 class="lbl">Критерии ВСТЭ: КР&nbsp;2024 и&nbsp;AHA&nbsp;2026</h2>
      <div class="mx-wrap">
        <ul class="crit">
<!--__CRIT__-->
        </ul>
      </div>
      <p class="mx-note">КР: уровень убедительности (A–C) и&nbsp;достоверности (1–5)&nbsp;— «да&nbsp;· A1» значит УУР&nbsp;A, УДД&nbsp;1. AHA: класс 1&nbsp;— рекомендуется, 2a&nbsp;— разумно, 2b&nbsp;— можно рассмотреть, 3&nbsp;— пользы нет.</p>
      <h2 class="lbl">Ловушки</h2>
      <div class="mx-wrap">
        <ul class="errs">
<!--__ERRORS__-->
        </ul>
      </div>
      <h2 class="lbl">Темы</h2>
      <div class="topics" id="topics"></div>
      <p class="src">Источники: клинические рекомендации МЗ&nbsp;РФ «Ишемический инсульт и&nbsp;транзиторная ишемическая атака», 2024 (ID&nbsp;814_1); 2026 Guideline for the Early Management of Patients With Acute Ischemic Stroke (AHA/ASA). Сверяйтесь с&nbsp;локальным протоколом.</p>
    </div>
''' + s[b:]

# ——— скрипт: ключи, название, без озвучки
rep('const LS_STATE = "ctp:state";\nconst LS_SPEAK = "ctp:autospeak";\nconst LS_TAB = "ctp:tab";\nconst LS_OPEN = "ctp:open";',
    'const LS_STATE = "art:state";\nconst LS_TAB = "art:tab";\nconst LS_OPEN = "art:open";\nconst LS_VIEW = "art:view";')
rep('let autoSpeak = false;   // озвучки в этом приложении нет\n', 'let tapPick = null;          // выбранный на схеме сосуд в карточке «покажи»\n')
rep('["apple-mobile-web-app-title", "Перфузия"],', '["apple-mobile-web-app-title", "Артерии"],')
rep("// Новые карточки идут вперемешку по темам: метод, карты, ядро и пенумбра, коллатерали, отбор, ловушки и отчёт чередуются.",
    "// Новые карточки идут вперемешку по темам: круг, ВСА, СМА, ПМА и ЗМА, ВББ, синдромы, КТА и отбор на ВСТЭ чередуются.")
a = s.index("// ——— Озвучка: записи голосом"); b = s.index("// ——— Очередь")
s = s[:a] + "function stopAudio(){}   // озвучки в этом приложении нет\n\n" + s[b:]
cut('const PLAY_SVG = ', '\n', keep_b=False)
rep('function label(a){ return a === "" ? "ничего" : a; }',
    'function label(a){ return a === "" ? "ничего" : a; }\n'
    'function segName(k){ const x = SEG[k]; return x ? (x.short || x.chip) : k; }')

# ——— карточка: схема, вопрос «покажи на схеме»
a = s.index("function render(){"); b = s.index("function renderDone(){")
s = s[:a] + r'''// Схема в карточке: без подписей до ответа. fig — выделен один сосуд, tap — нажми на нужный сосуд сам.
function renderFig(card){
  const box = $("fig");
  const f = card && (card.fig || card.tap);
  tapPick = null;
  $("card").classList.toggle("has-fig", !!f);
  if (!f){ box.hidden = true; box.textContent = ""; box.className = "fig"; return; }
  box.hidden = false;
  box.className = "fig fig-q" + (card.tap ? " tapmode" : "");
  box.innerHTML = VIEW_BY[f.v].svg;
  const svg = box.querySelector("svg");
  if (card.fig){
    svg.setAttribute("aria-label", "Схема без подписей, один сосуд выделен");
    segNodes(svg, card.fig.hl).forEach(n => n.classList.add("on"));
    return;
  }
  svg.setAttribute("role", "group");
  svg.setAttribute("aria-label", "Схема без подписей: нажми на нужный сосуд");
  let i = 0;
  svg.querySelectorAll(".seg").forEach(g => {
    if (g.classList.contains("a-off")) return;
    g.setAttribute("tabindex", "0");
    g.setAttribute("role", "button");
    g.setAttribute("aria-label", "Вариант " + (++i));
    g.addEventListener("click", () => pickSeg(g.dataset.seg));
    g.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); pickSeg(g.dataset.seg); } });
  });
}
function pickSeg(k){
  if (answered) return;
  const svg = $("fig").querySelector("svg");
  if (!svg) return;
  tapPick = k;
  svg.querySelectorAll(".seg.on").forEach(n => n.classList.remove("on"));
  segNodes(svg, k).forEach(n => n.classList.add("on"));
  $("check").disabled = false;
}
function revealFig(card, opt, ok){
  const box = $("fig");
  if (box.hidden) return;
  box.classList.add("shown");
  const svg = box.querySelector("svg");
  if (!svg || !card.tap) return;
  svg.querySelectorAll(".seg.on").forEach(n => n.classList.remove("on"));
  segNodes(svg, card.a).forEach(n => n.classList.add("ok"));
  if (!ok && opt) segNodes(svg, opt).forEach(n => n.classList.add("bad"));
  svg.querySelectorAll(".seg[tabindex]").forEach(g => { g.removeAttribute("tabindex"); g.removeAttribute("role"); g.removeAttribute("aria-label"); });
  box.classList.remove("tapmode");
}

function render(){
  stopAudio();
  answered = false;
  const card = queue[index];
  $("card").scrollTop = 0;
  if (!card){ renderDone(); return; }
  show("kind", true);
  $("kind").textContent = topicLabel(card.t);
  renderFig(card);
  const q = $("q");
  q.textContent = "";
  if (card.tap){
    q.append(marked(card.q));
    q.removeAttribute("aria-label");
  } else {
    const i = card.q.indexOf("___");
    // пропуск и знак препинания после него не разрываются переносом строки
    const post = card.q.slice(i + 3), pm = post.match(/^[?.!,;:]+/);
    const gapBox = el("span", "nw");
    gapBox.append(el("span", "gap"));
    if (pm) gapBox.append(pm[0]);
    q.append(card.q.slice(0, i), gapBox, pm ? post.slice(pm[0].length) : post);
    q.setAttribute("aria-label", card.q.replace("___", "пропуск"));
  }
  show("hint", true);
  $("hint").textContent = card.tap ? "Нажми на сосуд на схеме, затем «Проверить»" : "Выбери вариант";
  show("back", false);
  if (card.tap){
    $("opts").textContent = "";
    shownOpts = [];
    show("opts", false);
    $("check").disabled = true;
    show("actCheck", true);
  } else {
    renderOpts(card);
    show("opts", true);
    show("actCheck", false);
  }
  show("actNext", false);
  show("actDone", false);
  const prefix = mode === "topic" ? "Тема " + topicN + " · " : mode === "mixed" ? "Всё вместе · " : "";
  $("status").textContent = prefix + "Карточка " + (index + 1) + " из " + queue.length;
  setBar(index, queue.length);
}

''' + s[b:]
rep('''function renderDone(){
  show("kind", false);''', '''function renderDone(){
  renderFig(null);
  show("actCheck", false);
  show("kind", false);''')
rep('''  const q = $("q");
  q.textContent = "";
  q.removeAttribute("aria-label");
  const p = split(card, card.a);
  if (p.word) q.append(p.pre, el("span", "good", p.word), p.post);
  else q.append(p.pre, el("span", "zero", "∅"), p.post);
''', '''  if (!card.tap){
    const q = $("q");
    q.textContent = "";
    q.removeAttribute("aria-label");
    const p = split(card, card.a);
    if (p.word) q.append(p.pre, el("span", "good", p.word), p.post);
    else q.append(p.pre, el("span", "zero", "∅"), p.post);
  }
  revealFig(card, opt, ok);
''')
rep('''  if (exact){
    v.className = "verdict ok";
    v.append("Верно");
  }''', '''  if (exact){
    v.className = "verdict ok";
    if (card.tap) v.append("Верно: это ", el("b", null, segName(card.a)));
    else v.append("Верно");
  }''')
rep('''    v.className = "verdict bad";
    v.append("Нужно ", el("b", "good", label(card.a)), " · твой ответ: ", el("b", null, label(opt)));''',
    '''    v.className = "verdict bad";
    if (card.tap) v.append("Нужно: ", el("b", "good", segName(card.a)), " · ты показал: ", el("b", null, segName(opt)));
    else v.append("Нужно ", el("b", "good", label(card.a)), " · твой ответ: ", el("b", null, label(opt)));''')
rep('''  show("hint", false);
  show("back", true);
  show("opts", false);
  show("actNext", true);''', '''  show("hint", false);
  show("back", true);
  show("opts", false);
  show("actCheck", false);
  show("actNext", true);''')

# ——— атлас
ATLAS_JS = r'''// ——— Атлас: схемы, выбор сосуда, окраска по показаниям к ВСТЭ, счёт ASPECTS
const VIEW_BY = {};
VIEWS.forEach(v => { VIEW_BY[v.id] = v; });
let atlasView = "willis", atlasSel = null, evtOn = false, aspOn = false;
const aspX = new Set();
function segNodes(root, key){ return Array.from(root.querySelectorAll('.seg[data-seg="' + key + '"]')); }
function calm(){ try{ return window.matchMedia("(prefers-reduced-motion: reduce)").matches; }catch(e){ return true; } }
// Сосуды «прорисовываются» от начала к ветвям, области проявляются
function drawIn(svg){
  if (calm() || !svg) return;
  try{
    let i = 0;
    const wOf = p => { const m = (p.getAttribute("class") || "").match(/w(\d)/); return m ? +m[1] : 2; };
    Array.from(svg.querySelectorAll(".ln")).sort((a, b) => wOf(b) - wOf(a)).forEach(p => {
      if (typeof p.animate !== "function") return;
      p.setAttribute("pathLength", "1");
      p.animate([{ strokeDasharray: "1 2", strokeDashoffset: 1.01 }, { strokeDasharray: "1 2", strokeDashoffset: 0 }],
                { duration: 700, delay: Math.min(i++ * 24, 520), easing: "ease-out", fill: "backwards" });
    });
    let j = 0;
    svg.querySelectorAll(".area").forEach(p => {
      if (typeof p.animate !== "function") return;
      p.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 450, delay: Math.min(j++ * 45, 450), easing: "ease-out", fill: "backwards" });
    });
  }catch(e){}
}
function renderInfo(k){
  const box = $("info");
  box.textContent = "";
  const v = VIEW_BY[atlasView];
  if (!k || !SEG[k]){ box.append(el("p", "i-intro", v.intro)); return; }
  const x = SEG[k];
  box.append(el("h3", "i-name", x.name));
  if (x.evt) box.append(el("span", "badge b-" + x.evt.c, EVT_LABEL[x.evt.c]));
  const dl = el("dl", "i-rows");
  x.rows.forEach(r => { dl.append(el("dt", null, r[0]), el("dd", null, r[1])); });
  box.append(dl);
  if (x.evt){
    const ev = el("dl", "i-rows i-evt");
    x.evt.rows.forEach(r => { ev.append(el("dt", null, r[0]), el("dd", null, r[1])); });
    box.append(ev);
  }
}
function selectSeg(k){
  atlasSel = k;
  const stage = $("stage");
  stage.querySelectorAll(".seg.on").forEach(n => n.classList.remove("on"));
  if (k && !(atlasView === "aspects" && aspOn)) segNodes(stage, k).forEach(n => n.classList.add("on"));
  document.querySelectorAll(".schip").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.seg === k)));
  renderInfo(k);
}
function paintAsp(){
  $("stage").querySelectorAll(".reg").forEach(g => g.classList.toggle("x", aspX.has(g.dataset.seg)));
  $("aspScore").querySelector("b").textContent = String(10 - aspX.size);
  $("aspTog").setAttribute("aria-pressed", String(aspOn));
  $("aspReset").disabled = aspX.size === 0;
}
function tapAtlas(k){
  if (atlasView === "aspects" && aspOn){
    if (aspX.has(k)) aspX.delete(k); else aspX.add(k);
    paintAsp();
  }
  selectSeg(k);
}
function showInfo(){
  try{ $("info").scrollIntoView({ block: "nearest", behavior: calm() ? "auto" : "smooth" }); }catch(e){}
}
function renderAtlas(){
  const v = VIEW_BY[atlasView];
  document.querySelectorAll(".vchip").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.view === atlasView)));
  $("vCap").textContent = v.cap;
  const stage = $("stage");
  stage.innerHTML = v.svg;
  stage.classList.toggle("evt", evtOn && v.evt);
  const svg = stage.querySelector("svg");
  svg.querySelectorAll(".seg").forEach(g => {
    if (!g.classList.contains("a-off")) g.addEventListener("click", () => tapAtlas(g.dataset.seg));
  });
  const asp = v.id === "aspects";
  $("tools").hidden = !(v.evt || asp);
  $("evtTog").hidden = !v.evt;
  $("evtTog").setAttribute("aria-pressed", String(evtOn));
  $("evtLegend").hidden = !(v.evt && evtOn);
  $("aspTog").hidden = !asp; $("aspScore").hidden = !asp; $("aspReset").hidden = !asp;
  if (asp) paintAsp();
  const box = $("schips");
  box.textContent = "";
  box.classList.toggle("evt-on", evtOn && v.evt);
  v.segs.forEach(k => {
    const b = el("button", "schip", SEG[k].chip);
    b.type = "button";
    b.dataset.seg = k;
    const g = svg.querySelector('.seg[data-seg="' + k + '"]');
    if (g && g.dataset.evt) b.dataset.evt = g.dataset.evt;
    b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", () => { selectSeg(k); showInfo(); });
    box.append(b);
  });
  selectSeg(atlasSel && v.segs.indexOf(atlasSel) >= 0 ? atlasSel : null);
  drawIn(svg);
}
function initAtlas(){
  const box = $("vchips");
  VIEWS.forEach(v => {
    const b = el("button", "vchip", v.chip);
    b.type = "button";
    b.dataset.view = v.id;
    b.addEventListener("click", () => {
      if (atlasView === v.id) return;
      atlasView = v.id;
      lsSet(LS_VIEW, v.id);
      renderAtlas();
    });
    box.append(b);
  });
  const saved = lsGet(LS_VIEW);
  if (saved && VIEW_BY[saved]) atlasView = saved;
  $("evtTog").addEventListener("click", () => {
    evtOn = !evtOn;
    const v = VIEW_BY[atlasView];
    $("evtTog").setAttribute("aria-pressed", String(evtOn));
    $("stage").classList.toggle("evt", evtOn && v.evt);
    $("schips").classList.toggle("evt-on", evtOn && v.evt);
    $("evtLegend").hidden = !(evtOn && v.evt);
  });
  $("aspTog").addEventListener("click", () => {
    aspOn = !aspOn;
    paintAsp();
    selectSeg(atlasSel);
  });
  $("aspReset").addEventListener("click", () => { aspX.clear(); paintAsp(); });
  renderAtlas();
}

// ——— События
'''
rep("// ——— События\n", ATLAS_JS)
rep('$("next").addEventListener("click", next);', '$("next").addEventListener("click", next);\n$("check").addEventListener("click", () => { if (tapPick) choose(tapPick); });')
rep('''  if (e.target && e.target.closest && e.target.closest("button")) return;
  if (!answered){
    const i = parseInt(e.key, 10) - 1;
    if (i >= 0 && i < shownOpts.length && queue[index]) choose(shownOpts[i]);
  }''', '''  if (e.target && e.target.closest && e.target.closest("button, .seg")) return;
  const card = queue[index];
  if (!answered){
    if (card && card.tap){
      if ((e.key === "Enter" || e.key === " ") && tapPick){ e.preventDefault(); choose(tapPick); }
      return;
    }
    const i = parseInt(e.key, 10) - 1;
    if (i >= 0 && i < shownOpts.length && card) choose(shownOpts[i]);
  }''')
rep('''  buildMain();
  render();
  const saved = lsGet(LS_TAB);''', '''  initAtlas();
  buildMain();
  render();
  const saved = lsGet(LS_TAB);''')
for bad in ["ctp:state", "autoSpeak", "LS_SPEAK", "playClip", "speechSynthesis", "PLAY_SVG", "new Audio", 'id="sound"', 'id="say"', "Перфузия", "КТ-перфузия"]:
    assert bad not in s, bad
pathlib.Path("art/template.html").write_text(s)
print("ok", len(s))
