# Шаблон «Антиагреганты при ИИ и ТИА» собираю из шаблона «КТ-перфузия», как «ПОАК» и «ВИТС»:
# тренажёр тот же, вкладка «Справочник» — калькулятор схемы и дат, схемы, дозы, сроки, перевод на монотерапию,
# сочетание с антикоагулянтами, лёгкие и тяжёлые пациенты, особые случаи, ловушки, темы, источники.
import pathlib, re
s = pathlib.Path("ctp/template.html").read_text()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:70], s.count(a))
    s = s.replace(a, b)

rep("<title>КТ-перфузия</title>", "<title>Антиагреганты при ИИ и ТИА</title>")
rep("  .opts.c1{grid-template-columns:1fr}\n  .opts.c2{grid-template-columns:1fr 1fr}\n  .opts.c3{grid-template-columns:repeat(3,1fr)}\n",
    "  .opts.c1{grid-template-columns:minmax(0,1fr)}\n  .opts.c2{grid-template-columns:repeat(2,minmax(0,1fr))}\n  .opts.c3{grid-template-columns:repeat(3,minmax(0,1fr))}\n")
rep("  body.wide #drill .opts.c2,body.wide #drill .opts.c3{grid-template-columns:1fr}",
    "  body.wide #drill .opts.c2,body.wide #drill .opts.c3{grid-template-columns:minmax(0,1fr)}")
rep("  const cols = longest > 9 ? 1 : (n === 3 ? 3 : 2);",
    "  const cols = longest > 8 ? 1 : (n === 3 ? (longest <= 5 ? 3 : 1) : 2);   // три в ряд — только короткие: 21, ≤ 3, 180; два — до 8 знаков")
rep("  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n",
    "  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n  [hidden]{display:none!important}\n")

exec(pathlib.Path("dapt/_oac_css.py").read_text())   # CSS — общий с «ПОАК» и «ВИТС»
CSS += r"""
  .mon{list-style:none;margin:2px 0 0;padding:0}
  .mon li{padding:10px 0;border-top:1px solid var(--line)}
  .mon li:first-child{border-top:0}
  .mon .sw-k{font-size:18px}
  .mon .sw-v{font-size:16px}
  .dzr .d.ok{color:var(--yes-text)}
  .rk + .dzr{margin-top:2px}
  .tv{text-wrap:balance}
  .calc-top{margin-top:0}
  .rl.lead .rv{font-size:25px}
  .q,.err s,.err .good,.err-note,.rv,.rn,.dv,.dk,.tv,.tk,.ad-v,.iv-v,.sw-k,.sw-v,.cp-en,.cp-ru,.t-rule,.ex-en,.ex-ru,.why,.dzr .n,.dzr .d,.abbr dd,.algo-note,.verdict,.back p{hyphens:auto;-webkit-hyphens:auto}
"""
rep("  /* ——— Планшет */\n", CSS + "\n  /* ——— Планшет */\n")
assert s.count('<div class="app"') == 1
s = s.replace('<div class="app"', '<div class="app" lang="ru"')   # переносы по-русски в Safari
rep("  body.wide #rule{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);column-gap:36px;align-items:start}",
    "  body.wide #rule{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:36px;align-items:start}")

rep('aria-controls="rule">Правила</button>', 'aria-controls="rule">Справочник</button>')
rep('<button class="big" id="toRule" type="button">Правила</button>', '<button class="big" id="toRule" type="button">Справочник</button>')

a = s.index("// ——— Озвучка:"); b = s.index("// ——— Очередь")
s = s[:a] + "function stopAudio(){}   // озвучки в этом приложении нет\n\n" + s[b:]
assert "speechSynthesis" not in s and "playClip" not in s

a = s.index('    <div class="r-left">'); b = s.index('  </section>\n</div>')
s = s[:a] + '''    <div class="r-left">
      <h1 class="r-title">Антиагреганты при&nbsp;ИИ и&nbsp;ТИА</h1>
      <p class="r-sub">Ранняя вторичная профилактика: кому двойная антиагрегантная терапия, кому одна таблетка, нагрузочные дозы, когда начать и&nbsp;когда перейти на&nbsp;монотерапию, что делать с&nbsp;антикоагулянтами. Основа&nbsp;— <b>КР&nbsp;по&nbsp;ИИ&nbsp;2024</b>; рядом&nbsp;— <b>AHA/ASA&nbsp;2026</b>, <b>ESO</b> и&nbsp;новые РКИ <b>INSPIRES</b>, <b>ATAMIS</b>, <b>EAST</b>, <b>TAPIS</b>.</p>
      <section class="abbr" aria-labelledby="h-abbr">
        <h2 class="algo-h" id="h-abbr">Сокращения</h2>
        <dl>
          <div><dt>ДААТ</dt><dd>двойная антиагрегантная терапия: АСК + клопидогрел или АСК + тикагрелор; в&nbsp;КР&nbsp;— ДАТТ</dd></div>
          <div><dt>АСК</dt><dd>ацетилсалициловая кислота</dd></div>
          <div><dt>NIHSS</dt><dd>шкала инсульта NIH: ≤&nbsp;3&nbsp;— малый ИИ для&nbsp;ДААТ с&nbsp;клопидогрелом, ≤&nbsp;5&nbsp;— с&nbsp;тикагрелором</dd></div>
          <div><dt>ABCD2</dt><dd>риск инсульта после ТИА, 0–7 баллов: 0–3&nbsp;— низкий, 4–5&nbsp;— умеренный, 6–7&nbsp;— высокий; ≥&nbsp;4&nbsp;— показание к&nbsp;ДААТ</dd></div>
          <div><dt>ТЛТ, ТЭ</dt><dd>тромболизис, тромбэктомия</dd></div>
          <div><dt>ГТ</dt><dd>геморрагическая трансформация</dd></div>
          <div><dt>сВЧК</dt><dd>симптомное внутричерепное кровоизлияние</dd></div>
          <div><dt>CYP2C19 LoF</dt><dd>носители аллелей со&nbsp;сниженной функцией: клопидогрел хуже превращается в&nbsp;активный метаболит</dd></div>
          <div><dt>КР&nbsp;по&nbsp;ИИ&nbsp;2024</dt><dd>клинические рекомендации «Ишемический инсульт и&nbsp;транзиторная ишемическая атака»</dd></div>
          <div><dt>КР&nbsp;по&nbsp;ФП&nbsp;2025</dt><dd>клинические рекомендации «Фибрилляция и&nbsp;трепетание предсердий»</dd></div>
        </dl>
      </section>
      <nav class="jump" aria-label="Разделы справочника">
        <button type="button" data-to="s-calc">Подобрать</button>
        <button type="button" data-to="s-scheme">Схемы</button>
        <button type="button" data-to="s-dose">Дозы</button>
        <button type="button" data-to="s-time">Сроки</button>
        <button type="button" data-to="s-switch">Перевод</button>
        <button type="button" data-to="s-oac">С&nbsp;антикоагулянтами</button>
        <button type="button" data-to="s-sev">Лёгкие и&nbsp;тяжёлые</button>
        <button type="button" data-to="s-spec">Особые случаи</button>
        <button type="button" data-to="s-topics">Темы</button>
      </nav>
      <section class="algo" id="s-calc" aria-labelledby="h-calc">
        <h2 class="algo-h" id="h-calc">Подобрать схему</h2>
        <div class="calc calc-top" id="pcalc">
          <p class="calc-h">Пациент<small>Пример&nbsp;— замените данными пациента</small></p>
          <p class="fl" id="evLbl">Событие</p>
          <div class="seg s2" role="group" aria-labelledby="evLbl">
            <button type="button" class="chip" data-ev="is" aria-pressed="true">Инсульт</button>
            <button type="button" class="chip" data-ev="tia" aria-pressed="false">ТИА</button>
          </div>
          <div id="nihssBox"><label class="fl" for="nihss">NIHSS<small>сейчас</small></label><input class="inp" id="nihss" type="number" inputmode="numeric" min="0" max="42" step="1" value="3"></div>
          <div id="abcdBox" hidden><label class="fl" for="abcd">ABCD2<small>0–7</small></label><input class="inp" id="abcd" type="number" inputmode="numeric" min="0" max="7" step="1" value="5"></div>
          <label class="fl" for="onset">Начало симптомов<small>или когда видели здоровым</small></label>
          <input class="inp" id="onset" type="datetime-local">
          <p class="fl" id="repLbl">Реперфузия</p>
          <div class="seg s3" role="group" aria-labelledby="repLbl">
            <button type="button" class="chip" data-rep="none" aria-pressed="true">Нет</button>
            <button type="button" class="chip" data-rep="ivt" aria-pressed="false">ТЛТ</button>
            <button type="button" class="chip" data-rep="evt" aria-pressed="false">Только ТЭ</button>
          </div>
          <div id="ivtBox" hidden><label class="fl" for="ivt">Время ТЛТ</label><input class="inp" id="ivt" type="datetime-local"></div>
          <p class="fl" id="htLbl">Геморрагическая трансформация на&nbsp;КТ или МРТ</p>
          <div class="seg s2" role="group" aria-labelledby="htLbl">
            <button type="button" class="chip" data-ht="no" aria-pressed="true">Нет</button>
            <button type="button" class="chip" data-ht="yes" aria-pressed="false">Есть</button>
          </div>
          <div class="flags" role="group" aria-label="Что ещё учесть">
            <button type="button" class="chip" data-flag="af" aria-pressed="false">ФП</button>
            <button type="button" class="chip" data-flag="sten" aria-pressed="false">Симптомный стеноз ≥&nbsp;50%</button>
            <button type="button" class="chip" data-flag="athero" aria-pressed="false">Атеросклеротический генез</button>
            <button type="button" class="chip" data-flag="icas" aria-pressed="false">Интракраниальный стеноз 70–99%</button>
            <button type="button" class="chip" data-flag="ich" aria-pressed="false">ВЧК в&nbsp;анамнезе</button>
            <button type="button" class="chip" data-flag="onclop" aria-pressed="false">Уже принимает клопидогрел</button>
            <button type="button" class="chip" data-flag="cyp" aria-pressed="false">Носитель CYP2C19 LoF</button>
          </div>
          <label class="fl" for="d1">Первая доза<small>день 1 для даты перевода</small></label>
          <input class="inp" id="d1" type="date">
          <div class="res" id="pres" aria-live="polite"></div>
        </div>
      </section>
      <section class="algo algo-2" id="s-scheme" aria-labelledby="h-scheme">
        <h2 class="algo-h" id="h-scheme">Кому какая схема</h2>
        <ul class="mon">
<!--__SCHEMES__-->
        </ul>
        <p class="algo-note">Перед любой ДААТ&nbsp;— КТ или МРТ без кровоизлияния. При&nbsp;показании к&nbsp;антикоагулянту ДААТ, как правило, не&nbsp;назначают (ESO&nbsp;2021).</p>
      </section>
      <section class="algo" id="s-dose" aria-labelledby="h-dose">
        <h2 class="algo-h" id="h-dose">Дозы</h2>
        <div class="dz">
<!--__DOSES__-->
        </div>
        <p class="algo-note">Правило «старше 75&nbsp;лет&nbsp;— клопидогрел без нагрузочной дозы» в&nbsp;инструкции относится к&nbsp;инфаркту миокарда с&nbsp;подъёмом&nbsp;ST, не&nbsp;к&nbsp;инсульту.</p>
      </section>
      <section class="algo algo-2" id="s-time" aria-labelledby="h-time">
        <h2 class="algo-h" id="h-time">Когда начинать</h2>
        <ul class="mon">
<!--__TIMING__-->
        </ul>
        <p class="algo-note">Раньше&nbsp;— лучше: в&nbsp;INSPIRES абсолютная польза ДААТ&nbsp;— 1,42% за&nbsp;первую неделю, 0,49% за&nbsp;вторую, 0,29% за&nbsp;третью.</p>
      </section>
      <div class="go-wrap"><button class="big primary" id="go" type="button">Начать тренировку</button></div>
    </div>
    <div class="r-right">
      <h2 class="lbl" id="s-switch">Перевод на&nbsp;монотерапию</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__SWITCH__-->
        </ul>
      </div>
      <h2 class="lbl" id="s-oac">С&nbsp;антикоагулянтами</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__OAC__-->
        </ul>
      </div>
      <h2 class="lbl" id="s-sev">Лёгкие и&nbsp;тяжёлые</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__SEVERITY__-->
        </ul>
      </div>
      <h2 class="lbl" id="s-spec">Особые случаи</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__SPECIAL__-->
        </ul>
      </div>
      <p class="mx-note">Ранняя ДААТ при&nbsp;ТЛТ: EAST (NIHSS&nbsp;0–5, клопидогрел + АСК в&nbsp;первые 6&nbsp;ч после ТЛТ)&nbsp;— пользы нет; TAPIS (NIHSS&nbsp;4–10, тикагрелор + АСК в&nbsp;первые 6&nbsp;ч от&nbsp;начала&nbsp;— до, во&nbsp;время или после ТЛТ, тикагрелор 7&nbsp;дней)&nbsp;— mRS&nbsp;0–1 68,7% против 62,0%. В&nbsp;КР по&nbsp;ИИ&nbsp;2024&nbsp;— антиагрегант через 24&nbsp;ч.</p>
      <h2 class="lbl">Одна ситуация&nbsp;— разное решение</h2>
      <div class="mx-wrap">
<!--__CONTRAST__-->
      </div>
      <h2 class="lbl">Ловушки</h2>
      <div class="mx-wrap">
        <ul class="errs">
<!--__ERRORS__-->
        </ul>
      </div>
      <h2 class="lbl" id="s-topics">Темы</h2>
      <div class="topics" id="topics"></div>
      <h2 class="lbl">Источники</h2>
      <ol class="src">
<!--__SOURCES__-->
      </ol>
      <p class="foot">Сверено 29&nbsp;сентября 2026&nbsp;г. Справочник для&nbsp;врача: решение принимают по&nbsp;клинической ситуации и&nbsp;протоколу отделения.</p>
    </div>
''' + s[b:]

rep('const LS_STATE = "ctp:state";\nconst LS_SPEAK = "ctp:autospeak";\nconst LS_TAB = "ctp:tab";\nconst LS_OPEN = "ctp:open";',
    'const LS_STATE = "dapt:state";\nconst LS_TAB = "dapt:tab";\nconst LS_OPEN = "dapt:open";')
rep('["apple-mobile-web-app-title", "Перфузия"],', '["apple-mobile-web-app-title", "ДААТ"],')
rep("// Новые карточки идут вперемешку по темам: метод, карты, ядро и пенумбра, коллатерали, отбор, ловушки и отчёт чередуются.",
    "// Новые карточки идут вперемешку по темам: кому ДААТ, схемы, нагрузка, сроки, перевод, особые пациенты чередуются.")

CALC = r"""
// ——— Переход к разделам справочника
document.querySelectorAll(".jump button").forEach(b => b.addEventListener("click", () => {
  const t = document.getElementById(b.dataset.to);
  if (!t) return;
  const smooth = !(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  try{ t.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" }); }catch(e){ t.scrollIntoView(); }
}));

// ——— Помощники
const HOUR = 3600000;
const pc = { ev: "is", rep: "none", ht: "no", af: false, sten: false, athero: false, icas: false, ich: false, onclop: false, cyp: false };
const fmtD = new Intl.DateTimeFormat("ru-RU", { weekday: "short", day: "numeric", month: "long" });
const fmtDM = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long" });
function pad2(n){ return String(n).padStart(2, "0"); }
function toInput(d){ return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate()) + "T" + pad2(d.getHours()) + ":" + pad2(d.getMinutes()); }
function toDateInput(d){ return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate()); }
function fromInput(v){
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(v || "");
  return m ? new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]) : null;
}
function fromDate(v){
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(v || "");
  return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null;
}
function addDays(d, n){ return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n); }
function hm(d){ return pad2(d.getHours()) + ":" + pad2(d.getMinutes()); }
function whenT(d){ return fmtD.format(d) + ", " + hm(d); }
function tp(s){
  return String(s)
    .replace(/(\d)–(\d)/g, "$1–⁠$2")
    .replace(/(\d) (?=(?:мг|мл|мин|лет|ч(?![а-яё])|дн|сут|кг|недел|месяц|янв|фев|мар|апр|ма[яй]|июн|июл|авг|сен|окт|ноя|дек))/g, "$1 ")
    .replace(/ ([×<>≤≥=≈−→]) /g, " $1 ")
    .replace(/ \+ /g, " + ")
    .replace(/(^|[\s(])([<>≤≥≈]) (?=\d)/g, "$1$2 ")
    .replace(/(NIHSS|ABCD2|ОР|ОШ|КР по) (?=[\d<>≤≥=≈А-ЯA-Z])/g, "$1 ")
    .replace(/(^|[\s(«])(не|в|с|к|и|а|о|у|на|по|за|из|от|до|со|но|же|ли|при|без|для) /g, "$1$2 ")
    .replace(/ — /g, " — ");
}
function pill(now, from, to){
  if (now < from) return ["ещё рано", "p-wait"];
  if (to && now >= to) return ["срок прошёл", "p-late"];
  return ["сейчас", "p-now"];
}
function line(k, v, n, cls, p){
  const box = el("div", "rl" + (cls ? " " + cls : ""));
  box.append(el("p", "rk", tp(k)));
  box.append(el("p", "rv", tp(v)));
  if (n || p){
    const nn = el("p", "rn", tp(n || ""));
    if (p) nn.append(n ? " " : "", el("span", "pill " + p[1], p[0]));
    box.append(nn);
  }
  return box;
}
function row(name, dose, cls, why){
  const li = el("li");
  li.append(el("span", "n", tp(name)), el("span", "d" + (cls ? " " + cls : ""), tp(dose)));
  if (why) li.append(el("span", "w", tp(why)));
  return li;
}
function numv(id){ const v = String($(id).value).replace(",", ".").trim(); return v === "" ? NaN : Number(v); }
function ago(ms){
  const h = Math.floor(ms / HOUR);
  if (h < 1) return "меньше часа";
  if (h < 48) return h + " ч";
  return Math.floor(h / 24) + " сут " + (h % 24) + " ч";
}

// ——— Решение: схема по КР по ИИ 2024 (текст и алгоритм рис. 5), AHA/ASA 2026, ESO 2021, РКИ
function decide(ev, score, hrs){
  // kind: clop | tic | cyp | icas | mono | late | severe | poac | asa_af | ivt | evt | ht
  const notes = [];
  const done = r => { r.notes = notes; return r; };
  if (pc.ht === "yes") return done({ kind: "ht", why: "алгоритм КР по ИИ 2024: при ГТ — отсроченное назначение; точного срока в КР нет" });
  if (pc.af){
    if (ev === "tia") return done({ kind: "poac", why: "алгоритм КР по ИИ 2024: ТИА и ФП — ПОАК сразу" });
    return done({ kind: "asa_af", why: "АСК до старта ПОАК — КР по ИИ 2024 (УУР C), КР по ФП 2025 (ЕОК IIaB); с первой дозы ПОАК — без АСК" });
  }
  if (pc.rep === "ivt") return done({ kind: "ivt", why: "алгоритм КР по ИИ 2024: после тромболизиса — АСК или клопидогрел через 24 ч" });
  if (pc.rep === "evt") return done({ kind: "evt", why: "алгоритм КР по ИИ 2024: только тромбэктомия без ГТ — в первые 24 ч" });
  const in24 = hrs <= 24, in72 = hrs <= 72, in7d = hrs <= 168;
  const athero = pc.sten || pc.athero;
  let r = null;
  if (ev === "tia"){
    const tic = (score >= 6 || pc.sten) && in24;
    const clop = score >= 4 && in7d;
    if (tic && clop) r = { kind: "tic", why: score >= 6 ? "ТИА с ABCD2 ≥ 6 — КР по ИИ 2024, УУР B" : "ТИА со стенозом ≥ 50% — КР по ИИ 2024, УУР B", alt: "или клопидогрел + АСК 21 день — УУР A" + (in24 ? ", по инструкции" : "") };
    else if (tic) r = { kind: "tic", why: score >= 6 ? "ТИА с ABCD2 ≥ 6 — КР по ИИ 2024, УУР B" : "ТИА со стенозом ≥ 50% — КР по ИИ 2024, УУР B" };
    else if (clop) r = { kind: "clop", why: "ТИА с ABCD2 ≥ 4 — КР по ИИ 2024, УУР A" + (in24 ? "; инструкция клопидогрела" : "") };
    else if (score >= 4 || pc.sten) r = { kind: "late", why: score >= 4 ? "больше 7 суток — ДААТ по КР уже не начинают" : "ТИА со стенозом: ДААТ с тикагрелором — только в первые 24 ч" };
    else r = { kind: "mono", why: "ТИА низкого риска — алгоритм КР по ИИ 2024; ESO: ДААТ не нужна" };
  } else if (score <= 3){
    if (in7d){
      r = { kind: "clop", why: "малый ИИ, NIHSS ≤ 3 — КР по ИИ 2024, УУР A" + (in24 ? "; инструкция клопидогрела" : "") };
      if (in24) r.alt = "или тикагрелор + АСК 30 дней — КР, УУР B, вне инструкции";
    } else r = { kind: "late", why: "больше 7 суток — ДААТ по КР уже не начинают" };
  } else if (score <= 5){
    if (in24){
      r = { kind: "tic", why: "ИИ с NIHSS ≤ 5, первые 24 ч — КР по ИИ 2024, УУР B" };
      if (athero) r.alt = "или клопидогрел + АСК 21 день — INSPIRES";
    } else if (athero && in72) r = { kind: "clop", why: "атеросклеротический ИИ с NIHSS ≤ 5, до 72 ч — INSPIRES, AHA/ASA 2026 (2a)" };
    else if (in7d){
      r = { kind: "mono", why: "NIHSS 4–5 позже 24 ч без атеросклероза: по тексту КР и РКИ — один препарат" };
      notes.push("рис. 5 КР допускает ДААТ при NIHSS ≤ 5 до 7 суток, но текст КР и РКИ — только тикагрелор в первые 24 ч или атеросклероз до 72 ч (INSPIRES)");
    } else r = { kind: "late", why: "больше 7 суток — ДААТ по КР уже не начинают" };
  } else if (score <= 10){
    r = { kind: "mono", why: "NIHSS > 5 — по КР один препарат" };
    notes.push("ATAMIS (NIHSS 4–10): клопидогрел + АСК 14 дней — раннее ухудшение 4,8% против 6,7%; польза — при старте в первые 24 ч; в КР пока нет");
  } else {
    r = { kind: "severe", why: "тяжёлый ИИ — IST, CAST; AHA/ASA 2026 (1A)" };
  }
  // CHANCE-2: носитель CYP2C19 LoF при показании к ДААТ с клопидогрелом в первые 24 ч
  if (pc.cyp && r.kind === "clop" && in24 && (ev === "tia" ? score >= 4 : score <= 3)){
    r = { kind: "cyp", why: "носитель CYP2C19 LoF — CHANCE-2; AHA/ASA 2026 (2b); в РФ вне инструкции", alt: "или клопидогрел + АСК 21 день — если тикагрелор недоступен" };
  } else if (pc.cyp && r.kind === "clop") notes.push("носитель CYP2C19 LoF: клопидогрел работает хуже; схема CHANCE-2 — только в первые 24 ч");
  // интракраниальный стеноз 70–99%: клопидогрел к АСК до 90 дней (КР, УУР B); SAMMPRIS — ТИА и неинвалидизирующий инсульт
  if (pc.icas){
    if (r.kind === "clop"){ r.icas = true; r.alt = ""; }
    else if (r.kind === "tic") notes.push("интракраниальный стеноз 70–99%: после этой ДААТ — клопидогрел к АСК до 90 дней по КР (УУР B)");
    else if (r.kind === "severe") notes.push("интракраниальный стеноз 70–99%: вопрос о клопидогреле к АСК — после стабилизации; при тяжёлом ИИ данных нет (SAMMPRIS включал ТИА и неинвалидизирующий инсульт)");
    else if (r.kind === "mono" || r.kind === "late"){
      r = { kind: "icas", why: "интракраниальный стеноз 70–99% — КР по ИИ 2024: АСК 325 мг (УУР A) + клопидогрел до 90 дней (УУР B)" };
      notes.push("в SAMMPRIS включали ТИА и неинвалидизирующий инсульт");
    }
  }
  // ВЧК в анамнезе: тикагрелор противопоказан, ДААТ в РКИ не изучена
  if (pc.ich && ["clop", "tic", "cyp", "icas"].includes(r.kind)){
    r = { kind: "mono", why: "ВЧК в анамнезе: тикагрелор противопоказан (инструкция); ДААТ не изучена — CHANCE, POINT, THALES и INSPIRES таких не включали" };
    notes.push("по умолчанию — один препарат; ДААТ — индивидуально, с оценкой риска кровотечения");
  }
  return done(r);
}

function renderPlan(){
  const box = $("pres");
  box.textContent = "";
  const ev = pc.ev;
  $("nihssBox").hidden = ev !== "is";
  $("abcdBox").hidden = ev !== "tia";
  $("ivtBox").hidden = pc.rep !== "ivt";
  const onset = fromInput($("onset").value);
  const score = ev === "is" ? numv("nihss") : numv("abcd");
  const smax = ev === "is" ? 42 : 7;
  if (!(score >= 0 && score <= smax && Math.round(score) === score)){
    box.append(line("Схема", ev === "is" ? "Введите NIHSS: 0–42" : "Введите ABCD2: 0–7", "")); return;
  }
  if (!onset){ box.append(line("Схема", "Укажите начало симптомов", "")); return; }
  const now = new Date();
  if (onset - now > 5 * 60000){ box.append(line("Схема", "Время начала позже текущего", "Проверьте дату и время.", "warn")); return; }
  const hrs = (now - onset) / HOUR;
  const d1 = fromDate($("d1").value) || new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const r = decide(ev, score, hrs);
  const loadC = pc.onclop ? "75 мг, без нагрузки — уже принимает (ESO)" : "300 мг, затем 75 мг × 1";
  const list = el("ul", "dzr");
  let head, win = null, sw = null, swWhat = "";

  if (r.kind === "clop"){
    head = r.icas ? "Клопидогрел + АСК до 90 дней" : "Клопидогрел + АСК 21 день";
    list.append(row("Клопидогрел", loadC, "", pc.onclop ? "" : "нагрузка 300 мг — инструкция, CHANCE, INSPIRES; 600 мг — POINT"));
    list.append(row("АСК", r.icas ? "325 мг × 1" : "75–100 мг × 1", "", r.icas ? "интракраниальный стеноз — КР, УУР A" : "первая доза в РКИ — до 300 мг"));
    win = [onset, new Date(onset.getTime() + 168 * HOUR), "как можно раньше после КТ; КР — не позже 7 суток; ESO — в первые 24 ч; INSPIRES — до 72 ч"];
    sw = addDays(d1, r.icas ? 90 : 21); swWhat = r.icas ? "с 91-го дня — один препарат" : "с 22-го дня — клопидогрел 75 мг или АСК 75–150 мг";
  } else if (r.kind === "tic"){
    head = "Тикагрелор + АСК 30 дней";
    list.append(row("Тикагрелор", "180 мг, затем 90 мг × 2", "", "в РФ при инсульте вне инструкции; при дисфагии — измельчить"));
    list.append(row("АСК", "300 мг, затем 75–100 мг × 1", "", "как в THALES; по инструкции тикагрелора — 75–150 мг, выше 300 мг нельзя"));
    win = [onset, new Date(onset.getTime() + 24 * HOUR), "только в первые 24 ч от начала"];
    sw = addDays(d1, 30); swWhat = "с 31-го дня — АСК 75–150 мг или клопидогрел 75 мг";
  } else if (r.kind === "cyp"){
    head = "Тикагрелор + АСК 21 день, затем тикагрелор до 90-го дня";
    list.append(row("Тикагрелор", "180 мг, затем 90 мг × 2", "", "до 90-го дня"));
    list.append(row("АСК", "75–300 мг, затем 75 мг × 1", "", "первые 21 день"));
    win = [onset, new Date(onset.getTime() + 24 * HOUR), "в первые 24 ч от начала"];
    sw = addDays(d1, 21); swWhat = "с 22-го дня — только тикагрелор, до 90-го дня";
  } else if (r.kind === "icas"){
    head = "АСК 325 мг + клопидогрел до 90 дней";
    list.append(row("АСК", "325 мг × 1", "", "КР, УУР A"));
    list.append(row("Клопидогрел", "75 мг × 1", "", "до 90 дней, КР, УУР B"));
    win = [onset, new Date(onset.getTime() + 24 * HOUR), "антиагрегант — в первые 24 ч (алгоритм КР)"];
    sw = addDays(d1, 90); swWhat = "с 91-го дня — один препарат";
  } else if (r.kind === "mono" || r.kind === "late"){
    head = r.kind === "late" ? "Один препарат" : "Один препарат: АСК или клопидогрел";
    list.append(row("АСК", "75–150 мг × 1", "", "первая доза — до 300 мг"));
    list.append(row("или клопидогрел", "75 мг × 1", "", "КР по ИИ 2024, УУР A"));
    win = [onset, new Date(onset.getTime() + 24 * HOUR), "в первые 24 ч; АСК — не позже 48 ч"];
  } else if (r.kind === "severe"){
    head = "АСК 160–300 мг, затем 75–150 мг";
    list.append(row("АСК", "160–300 мг × 1", "", "в первые 48 ч; дальше 75–150 мг"));
    list.append(row("ДААТ", "не назначают", "no", "у таких пациентов не изучали"));
    win = [onset, new Date(onset.getTime() + 48 * HOUR), "в первые 48 ч; per os — после скрининга глотания"];
  } else if (r.kind === "poac"){
    head = "ПОАК сразу";
    list.append(row("Антиагрегант", "не нужен", "", "ПОАК вместо него"));
  } else if (r.kind === "asa_af"){
    head = "АСК до старта ПОАК";
    list.append(row("АСК", "75–150 мг × 1", "", "до старта ПОАК; с первой дозы ПОАК — без АСК"));
    list.append(row("ПОАК + АСК", "не сочетать", "no", "КР по ИИ 2024 (УУР B), КР по ФП 2025"));
    const base = pc.rep === "ivt" ? fromInput($("ivt").value) : null;
    if (pc.rep === "ivt") win = base ? [new Date(base.getTime() + 24 * HOUR), null, "через 24 ч после тромболизиса"] : null;
    else win = [onset, new Date(onset.getTime() + 24 * HOUR), "в первые 24 ч"];
    r.notes.push("срок ПОАК — по размеру инфаркта и ГТ (ELAN; приложение «ПОАК»)");
  } else if (r.kind === "ivt"){
    head = "АСК или клопидогрел через 24 ч";
    list.append(row("АСК", "75–150 мг × 1", "", "при ГТ — отсроченно"));
    list.append(row("или клопидогрел", "75 мг × 1", "", ""));
    const t = fromInput($("ivt").value);
    if (t && t >= onset) win = [new Date(t.getTime() + 24 * HOUR), null, "через 24 ч после тромболизиса; раньше — решением врачебной комиссии"];
    r.notes.push("ранняя ДААТ при ТЛТ: CHANCE, POINT, THALES, INSPIRES таких пациентов не включали; EAST (NIHSS 0–5) — пользы нет; TAPIS (NIHSS 4–10, тикагрелор + АСК в первые 6 ч от начала, тикагрелор 7 дней) — mRS 0–1 лучше; в КР пока нет");
  } else if (r.kind === "evt"){
    head = "АСК или клопидогрел в первые 24 ч";
    list.append(row("АСК", "75–150 мг × 1", "", "если на КТ нет ГТ"));
    list.append(row("или клопидогрел", "75 мг × 1", "", ""));
    win = [onset, new Date(onset.getTime() + 24 * HOUR), "в первые 24 ч; при экстренном стентировании — по показаниям стента"];
  } else if (r.kind === "ht"){
    head = "Антиагрегант — отсроченно";
    list.append(row("АСК или клопидогрел", "после КТ в динамике", "low", "точного срока в КР нет"));
  }

  box.append(line("Схема", head, r.why + (r.alt ? " · " + r.alt : ""), "lead" + (r.kind === "ht" || r.kind === "late" ? " warn" : "")));
  const dw = el("div", "rl");
  dw.append(el("p", "rk", tp("Препараты и дозы")));
  dw.append(list);
  box.append(dw);
  if (win){
    const endTxt = win[1] ? "до " + whenT(win[1]) : "с " + whenT(win[0]);
    let pl = pill(now, win[0], win[1]);
    if (pl[1] === "p-late" && !["clop", "tic", "cyp"].includes(r.kind)) pl = ["начать сейчас", "p-now"];
    box.append(line("Когда начать", endTxt, win[2], "", pl));
  } else if (pc.rep === "ivt"){
    box.append(line("Когда начать", "Укажите время тромболизиса", "антиагрегант — через 24 ч после него"));
  }
  if (sw){
    box.append(line("Перевод на монотерапию", fmtD.format(sw), swWhat + "; день 1 — " + fmtDM.format(d1), "ok"));
  }
  for (const n of r.notes) box.append(el("p", "res-note", tp(n.charAt(0).toUpperCase() + n.slice(1) + ".")));
  const dapt = ["clop", "tic", "cyp", "icas"].includes(r.kind);
  box.append(el("p", "res-note", tp("Прошло от начала: " + ago(now - onset) + "." + (dapt ? " Перед ДААТ — КТ или МРТ без кровоизлияния." : ""))));
}

function pressOne(sel, attr, val){
  document.querySelectorAll(sel).forEach(b => b.setAttribute("aria-pressed", String(b.dataset[attr] === val)));
}
function initCalc(){
  const d = new Date(Date.now() - 10 * HOUR);
  d.setMinutes(Math.floor(d.getMinutes() / 5) * 5, 0, 0);
  $("onset").value = toInput(d);
  const t = new Date(Date.now() - 8 * HOUR); t.setMinutes(Math.floor(t.getMinutes() / 5) * 5, 0, 0);
  $("ivt").value = toInput(t);
  $("d1").value = toDateInput(new Date());
  const bind = (attr, key) => document.querySelectorAll("[data-" + attr + "]").forEach(b => b.addEventListener("click", () => { pc[key] = b.dataset[attr]; pressOne("[data-" + attr + "]", attr, pc[key]); renderPlan(); }));
  bind("ev", "ev"); bind("rep", "rep"); bind("ht", "ht");
  document.querySelectorAll("[data-flag]").forEach(b => b.addEventListener("click", () => {
    const k = b.dataset.flag; pc[k] = !pc[k]; b.setAttribute("aria-pressed", String(pc[k])); renderPlan();
  }));
  ["nihss", "abcd", "onset", "ivt", "d1"].forEach(id => { $(id).addEventListener("input", renderPlan); $(id).addEventListener("change", renderPlan); });
  renderPlan();
  setInterval(() => { if (!$("rule").hidden) renderPlan(); }, 60000);
}
"""
rep("function boot(){\n", CALC + "\nfunction boot(){\n")
rep('      const rule = el("p", "t-rule"); rule.append(richText(t.rule)); body.append(rule);',
    '      String(t.rule).split("\\n\\n").forEach(par => { const rule = el("p", "t-rule"); rule.append(richText(par)); body.append(rule); });')
rep("  connectCloud();\n}\nboot();", "  initCalc();\n  connectCloud();\n}\nboot();")
assert "ctp:" not in s and "Перфузия" not in s and "КТ-перфузия" not in s
s, _n = re.subn(r'(<(?:label|p) class="fl"[^>]*>[^<]*?)<small>', r'\1 <small>', s)
assert _n == 4, _n
pathlib.Path("dapt/template.html").write_text(s)
print("ok", len(s))
