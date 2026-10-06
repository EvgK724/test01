# Шаблон «Антитромботики при тромбоцитопении» собираю из шаблона «КТ-перфузия», как «ПОАК», «ВИТС» и «ДААТ»:
# тренажёр тот же, вкладка «Справочник» — калькулятор тактики по уровню тромбоцитов, матрица препарат × уровень,
# три уровня подробно, пороги документов, ТЛТ и ТЭ, ГИТ со шкалой 4Ts, особые ситуации, ловушки, темы, источники.
import pathlib, re
s = pathlib.Path("ctp/template.html").read_text()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:70], s.count(a))
    s = s.replace(a, b)

rep("<title>КТ-перфузия</title>", "<title>Антитромботики при тромбоцитопении</title>")
rep("  .opts.c1{grid-template-columns:1fr}\n  .opts.c2{grid-template-columns:1fr 1fr}\n  .opts.c3{grid-template-columns:repeat(3,1fr)}\n",
    "  .opts.c1{grid-template-columns:minmax(0,1fr)}\n  .opts.c2{grid-template-columns:repeat(2,minmax(0,1fr))}\n  .opts.c3{grid-template-columns:repeat(3,minmax(0,1fr))}\n")
rep("  body.wide #drill .opts.c2,body.wide #drill .opts.c3{grid-template-columns:1fr}",
    "  body.wide #drill .opts.c2,body.wide #drill .opts.c3{grid-template-columns:minmax(0,1fr)}")
rep("  const cols = longest > 9 ? 1 : (n === 3 ? 3 : 2);",
    "  const cols = longest > 8 ? 1 : (n === 3 ? (longest <= 5 ? 3 : 1) : 2);   // три в ряд — только короткие: 25, 3-й; два — до 8 знаков")
rep("  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n",
    "  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n  [hidden]{display:none!important}\n")

exec(pathlib.Path("thrombo/_oac_css.py").read_text())   # CSS — общий с «ПОАК», «ВИТС», «ДААТ»
CSS += r"""
  .mon{list-style:none;margin:2px 0 0;padding:0}
  .mon li{padding:10px 0;border-top:1px solid var(--line)}
  .mon li:first-child{border-top:0}
  .dzr .d.ok{color:var(--yes-text)}
  .calc-top{margin-top:0}
  .rl.lead .rv{font-size:25px}
  .calc-hint{margin:8px 0 0;font-size:13px;line-height:1.45;color:var(--muted)}
  .mxg{margin-top:2px}
  .mxr{padding:10px 0 12px;border-top:1px solid var(--line)}
  .mxr:first-child{border-top:0;padding-top:2px}
  .mxr-k{margin:0 0 6px;font-size:15px;font-weight:600;line-height:1.3;color:var(--text)}
  .mxr-c{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
  .mxr-c span{display:block;min-width:0;padding:5px 7px 6px;border-radius:10px;font-family:var(--serif);font-size:16px;line-height:1.2;overflow-wrap:break-word}
  .mxr-c small{display:block;margin-bottom:1px;font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.03em;color:var(--muted)}
  .c-yes{color:var(--yes-text);background:rgba(78,135,103,.14)}
  .c-maybe{color:#e5c07b;background:rgba(229,192,123,.10)}
  .c-no{color:var(--no-text);background:rgba(233,167,160,.10)}
  .lvl{margin-top:14px;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:var(--bg)}
  .lvl-h{margin:0;padding:11px 14px 10px;font-family:var(--serif);font-weight:400;font-size:24px;line-height:1.2;border-bottom:1px solid var(--line)}
  .lvl-h small{display:block;margin-top:3px;font-family:var(--sans);font-size:13px;line-height:1.35;letter-spacing:.01em;color:var(--muted)}
  .lvl-hi .lvl-h{color:var(--yes-text)}
  .lvl-mid .lvl-h{color:#e5c07b}
  .lvl-lo .lvl-h{color:var(--no-text)}
  .iv-n{margin:3px 0 0;font-size:13px;line-height:1.45;color:var(--muted)}
  .seg.s1{grid-template-columns:minmax(0,1fr)}
  .seg.s1 .chip{padding:8px 12px;text-align:left;line-height:1.3}
  .seg.s1 .chip b{display:inline-block;min-width:1.1em;margin-right:6px;font-family:var(--serif);font-weight:400;font-size:18px;color:var(--accent)}
  .tcalc{margin-top:0}
  .q,.err s,.err .good,.err-note,.rv,.rn,.dv,.dk,.ad-v,.iv-k,.iv-v,.iv-n,.sw-k,.sw-v,.sw-s,.cp-en,.cp-ru,.t-rule,.ex-en,.ex-ru,.why,.dzr .n,.dzr .d,.dzr .w,.abbr dd,.algo-note,.calc-hint,.mxr-k,.lvl-h small,.verdict,.back p{hyphens:auto;-webkit-hyphens:auto}
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
      <h1 class="r-title">Антитромботики при&nbsp;тромбоцитопении</h1>
      <p class="r-sub">НМГ, ПОАК, АСК и&nbsp;клопидогрел при&nbsp;тромбоцитах меньше 20, 20–50 и&nbsp;больше 50&nbsp;×&nbsp;10⁹/л: что оставить, что снизить, что отменить; ТЛТ, тромбэктомия, ГИТ. <b>КР&nbsp;по&nbsp;ИИ&nbsp;2024</b> порогов для&nbsp;антиагрегантов и&nbsp;ПОАК не&nbsp;дают&nbsp;— они из&nbsp;<b>EHA&nbsp;2022</b>, <b>EHRA&nbsp;2021</b>, <b>ISTH&nbsp;2018</b> и&nbsp;<b>ESC&nbsp;2022</b>; рядом&nbsp;— <b>AHA/ASA&nbsp;2026</b>, <b>ASH&nbsp;2018</b>, <b>AABB&nbsp;2025</b> и&nbsp;новые когорты.</p>
      <section class="abbr" aria-labelledby="h-abbr">
        <h2 class="algo-h" id="h-abbr">Сокращения</h2>
        <dl>
          <div><dt>ТЦП</dt><dd>тромбоцитопения: меньше 150&nbsp;×&nbsp;10⁹/л; в&nbsp;EHA&nbsp;2022&nbsp;— 100 и&nbsp;меньше, степени 1–4. 50&nbsp;×&nbsp;10⁹/л&nbsp;= 50&nbsp;000/мкл</dd></div>
          <div><dt>НМГ, НФГ</dt><dd>низкомолекулярный и&nbsp;нефракционированный гепарин</dd></div>
          <div><dt>ПОАК</dt><dd>прямые пероральные антикоагулянты: апиксабан, ривароксабан, дабигатран, эдоксабан</dd></div>
          <div><dt>АСК, ДААТ</dt><dd>ацетилсалициловая кислота; двойная антиагрегантная терапия</dd></div>
          <div><dt>ВТЭ</dt><dd>венозная тромбоэмболия: ТГВ и&nbsp;ТЭЛА</dd></div>
          <div><dt>ППК</dt><dd>перемежающаяся пневмокомпрессия</dd></div>
          <div><dt>ГИТ, ИТП</dt><dd>гепарин-индуцированная и&nbsp;иммунная тромбоцитопения</dd></div>
          <div><dt>ТЛТ, ТЭ</dt><dd>тромболизис, тромбэктомия; сВЧК&nbsp;— симптомное внутричерепное кровоизлияние</dd></div>
          <div><dt>EHA</dt><dd>European Hematology Association: руководство 2022&nbsp;г. для&nbsp;онкобольных с&nbsp;ТЦП</dd></div>
          <div><dt>EHRA</dt><dd>European Heart Rhythm Association: практическое руководство по&nbsp;ПОАК 2021&nbsp;г.</dd></div>
          <div><dt>ISTH</dt><dd>International Society on Thrombosis and Haemostasis</dd></div>
          <div><dt>КР&nbsp;по&nbsp;ИИ&nbsp;2024</dt><dd>клинические рекомендации «Ишемический инсульт и&nbsp;транзиторная ишемическая атака»</dd></div>
        </dl>
      </section>
      <nav class="jump" aria-label="Разделы справочника">
        <button type="button" data-to="s-calc">Подобрать</button>
        <button type="button" data-to="s-levels">Три уровня</button>
        <button type="button" data-to="s-thr">Пороги</button>
        <button type="button" data-to="s-rep">ТЛТ и&nbsp;ТЭ</button>
        <button type="button" data-to="s-hit">ГИТ</button>
        <button type="button" data-to="s-spec">Особые случаи</button>
        <button type="button" data-to="s-topics">Темы</button>
      </nav>
      <section class="algo" id="s-calc" aria-labelledby="h-calc">
        <h2 class="algo-h" id="h-calc">Подобрать тактику</h2>
        <div class="calc calc-top" id="pcalc">
          <p class="calc-h">Пациент<small>Пример&nbsp;— замените данными пациента</small></p>
          <label class="fl" for="plt">Тромбоциты<small>×&nbsp;10⁹/л</small></label>
          <input class="inp" id="plt" type="number" inputmode="decimal" min="0" max="1500" step="1" value="35">
          <p class="fl" id="trLbl">Динамика</p>
          <div class="seg s2" role="group" aria-labelledby="trLbl">
            <button type="button" class="chip" data-tr="st" aria-pressed="true">Стабильно</button>
            <button type="button" class="chip" data-tr="fall" aria-pressed="false">Снижаются</button>
          </div>
          <div class="flags" role="group" aria-label="Что ещё учесть">
            <button type="button" class="chip" data-flag="vhr" aria-pressed="false">Очень высокий тромботический риск</button>
            <button type="button" class="chip" data-flag="bleed" aria-pressed="false">Другие факторы кровотечения</button>
            <button type="button" class="chip" data-flag="icas" aria-pressed="false">Симптомный интракраниальный стеноз</button>
            <button type="button" class="chip" data-flag="hit" aria-pressed="false">Подозрение на&nbsp;ГИТ</button>
          </div>
          <p class="calc-hint">Снижаются&nbsp;— в&nbsp;ближайшие дни ожидается падение ниже 50, а&nbsp;при 25–50&nbsp;— ниже 25 (EHA&nbsp;2022). Очень высокий риск (EHA&nbsp;2022): для&nbsp;трансфузии и&nbsp;полной дозы НМГ&nbsp;— механический клапан, острая ТЭЛА или проксимальный ТГВ, ОКС, ФП с&nbsp;эмболией в&nbsp;последний месяц; для&nbsp;НМГ 50% при&nbsp;ФП&nbsp;— ещё эмболия в&nbsp;последние 3&nbsp;месяца или CHA2DS2-VASc&nbsp;≥&nbsp;6. Сроки антикоагуляции после текущего инсульта EHA не&nbsp;разбирает&nbsp;— по&nbsp;протоколу отделения. Факторы кровотечения: недавнее большое кровотечение, ХБП III&nbsp;стадии и&nbsp;тяжелее, поражение костного мозга, опухоль мозга, ДВС.</p>
          <div class="res" id="pres" aria-live="polite"></div>
        </div>
      </section>
      <section class="algo algo-2" id="s-levels" aria-labelledby="h-levels">
        <h2 class="algo-h" id="h-levels">Три уровня: коротко</h2>
        <div class="mxg">
<!--__MATRIX__-->
        </div>
<!--__LEVELS__-->
        <p class="algo-note">Динамика важнее одного числа: при&nbsp;падающих тромбоцитах выбирают НМГ, а&nbsp;не&nbsp;ПОАК, и&nbsp;контролируют анализ чаще. EHA&nbsp;2022 написаны для&nbsp;онкобольных; при&nbsp;другой причине ТЦП их применяют по&nbsp;аналогии.</p>
      </section>
      <div class="go-wrap"><button class="big primary" id="go" type="button">Начать тренировку</button></div>
    </div>
    <div class="r-right">
      <h2 class="lbl" id="s-thr">Пороги разных документов</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__THRESH__-->
        </ul>
      </div>
      <h2 class="lbl" id="s-rep">ТЛТ и&nbsp;тромбэктомия</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__REPERF__-->
        </ul>
      </div>
      <p class="mx-note">TRISP: при&nbsp;тромбоцитах меньше 150 сВЧК после ТЛТ чаще (ОШ&nbsp;1,73), но&nbsp;у&nbsp;44 пациентов с&nbsp;меньше 100&nbsp;— ОШ&nbsp;1,56, незначимо. Тромбэктомия при&nbsp;ТЦП: сВЧК не&nbsp;чаще (ОШ&nbsp;1,20), летальность выше (ОШ&nbsp;1,76)&nbsp;— мета-анализ Toruno&nbsp;2024.</p>
      <h2 class="lbl" id="s-hit">ГИТ: шкала 4Ts</h2>
      <div class="calc tcalc" id="tcalc">
        <p class="calc-h">Вероятность ГИТ<small>ASH&nbsp;2018: по&nbsp;4Ts, а&nbsp;не&nbsp;«на&nbsp;глаз». Пример&nbsp;— замените данными пациента</small></p>
<!--__T4__-->
        <div class="res" id="tres" aria-live="polite"></div>
      </div>
      <h2 class="lbl">ГИТ: что делать</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__HIT__-->
        </ul>
      </div>
      <h2 class="lbl" id="s-spec">Особые ситуации</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__SPECIAL__-->
        </ul>
      </div>
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
      <p class="foot">Сверено 30&nbsp;сентября 2026&nbsp;г. Справочник для&nbsp;врача: решение принимают по&nbsp;клинической ситуации, вместе с&nbsp;гематологом и&nbsp;по&nbsp;протоколу отделения.</p>
    </div>
''' + s[b:]

rep('const LS_STATE = "ctp:state";\nconst LS_SPEAK = "ctp:autospeak";\nconst LS_TAB = "ctp:tab";\nconst LS_OPEN = "ctp:open";',
    'const LS_STATE = "thrombo:state";\nconst LS_TAB = "thrombo:tab";\nconst LS_OPEN = "thrombo:open";')
rep('["apple-mobile-web-app-title", "Перфузия"],', '["apple-mobile-web-app-title", "Тромбоциты"],')
rep("// Новые карточки идут вперемешку по темам: метод, карты, ядро и пенумбра, коллатерали, отбор, ловушки и отчёт чередуются.",
    "// Новые карточки идут вперемешку по темам: уровни, КР, НМГ, ПОАК, АСК, ДААТ, ТЛТ, ГИТ чередуются.")

CALC = r"""
// ——— Переход к разделам справочника
document.querySelectorAll(".jump button").forEach(b => b.addEventListener("click", () => {
  const t = document.getElementById(b.dataset.to);
  if (!t) return;
  const smooth = !(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  try{ t.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" }); }catch(e){ t.scrollIntoView(); }
}));

// ——— Помощники
const pc = { tr: "st", vhr: false, bleed: false, icas: false, hit: false };
function tp(s){
  return String(s)
    .replace(/севдотромбоцитопени/g, "севдо\u00adтромбо\u00adцитопени").replace(/ромбоцитопени/g, "ромбо\u00adцитопени")
    .replace(/рофилактическ/g, "рофилакти\u00adческ").replace(/невмокомпресси/g, "невмо\u00adкомпресси")
    .replace(/нтракраниальн/g, "нтра\u00adкраниальн")
    .replace(/10⁹\/л/g, "10⁹/\u2060л").replace(/½ /g, "½\u00a0")
    .replace(/(\d)–(\d)/g, "$1–⁠$2")
    .replace(/(\d) (?=(?:мг|мл|мин|лет|ч(?![а-яё])|дн|сут|кг|недел|месяц|балл|000|%))/g, "$1 ")
    .replace(/ ([×<>≤≥=≈−→]) /g, " $1 ")
    .replace(/ \+ /g, " + ")
    .replace(/(^|[\s(])([<>≤≥≈]) (?=\d)/g, "$1$2 ")
    .replace(/(ОР|ОШ|КР по|EHA|EHRA|ESC|ISTH|SCAI|ASH|AABB|AHA\/ASA|рек\.) (?=[\d<>≤≥=≈А-ЯA-Z])/g, "$1 ")
    .replace(/(^|[\s(«])(не|в|с|к|и|а|о|у|на|по|за|из|от|до|со|но|же|ли|при|без|для) /g, "$1$2 ")
    .replace(/ — /g, " — ");
}
function line(k, v, n, cls){
  const box = el("div", "rl" + (cls ? " " + cls : ""));
  box.append(el("p", "rk", tp(k)));
  box.append(el("p", "rv", tp(v)));
  if (n) box.append(el("p", "rn", tp(n)));
  return box;
}
function row(name, dose, cls, why){
  const li = el("li");
  li.append(el("span", "n", tp(name)), el("span", "d" + (cls ? " " + cls : ""), tp(dose)));
  if (why) li.append(el("span", "w", tp(why)));
  return li;
}
function numv(id){ const v = String($(id).value).replace(",", ".").trim(); return v === "" ? NaN : Number(v); }
function fmtN(p){ return (Math.round(p * 10) / 10).toLocaleString("ru-RU"); }
function ehaGrade(p){
  if (p > 100) return "не ТЦП (> 100)";
  if (p >= 75) return "1-я степень (75–100)";
  if (p >= 50) return "2-я степень (50–75)";
  if (p >= 25) return "3-я степень (25–50)";
  return "4-я степень (< 25)";
}
function ehraBand(p){ return p > 50 ? "> 50 — с осторожностью" : p >= 20 ? "20–50 — с большой осторожностью" : "< 20 — избегать ПОАК"; }

// ——— Решение: EHA 2022, EHRA 2021, ISTH 2018, ESC 2022, ASH 2018, КР по ИИ 2024, AHA/ASA 2026
function plan(p, st){
  const R = [], notes = [];
  const add = (n, d, c, w) => R.push([n, d, c, w]);
  const { hit, vhr, bleed, icas } = pc;
  // НМГ, профилактика ТГВ
  if (hit) add("НМГ профилактически", "отменить", "no", "подозрение на ГИТ: все гепарины отменить (ASH 2018)");
  else if (p >= 50) add("НМГ профилактически", "стандартная доза", "ok", "у обездвиженных, если польза выше риска — КР по ИИ 2024, УУР A" + (p < 100 ? "; EHA 2022 — и при 50–100" : ""));
  else if (p >= 25){
    if (bleed) add("НМГ профилактически", "нет — пневмокомпрессия", "no", "другие факторы кровотечения — EHA 2022; КР по ИИ 2024: < 50 — довод за ППК");
    else add("НМГ профилактически", "можно рассмотреть", "low", "EHA 2022: только НМГ в стандартной профилактической дозе, при стабильных тромбоцитах или частом контроле; КР по ИИ 2024: < 50 — довод за ППК");
  } else add("НМГ профилактически", "нет — пневмокомпрессия", "no", "EHA 2022: < 25 — без медикаментозной профилактики");
  // лечебная антикоагуляция
  if (hit) add("Лечебная антикоагуляция", "негепариновый антикоагулянт", "low", bleed ? "высокий риск кровотечения — аргатробан или бивалирудин (ASH 2018)" : "стабильным — фондапаринукс или ПОАК; критическое состояние или возможна срочная процедура — аргатробан или бивалирудин (ASH 2018)");
  else if (p >= 50) add("НМГ лечебно при ВТЭ", "полная доза", "ok", "ISTH 2018, EHA 2022" + (!st && p < 100 ? "; тромбоциты падают — НМГ лучше ПОАК (EHA)" : ""));
  else if (p >= 25){
    if (vhr) add("НМГ лечебно при ВТЭ", "полная доза + трансфузия до 40–50", "low", "высокий риск по ISTH 2018, очень высокий по EHA 2022: не дольше 14 дней, не рутинно; без трансфузии — 50% дозы");
    else add("НМГ лечебно при ВТЭ", "50% дозы или профилактическая", "low", "EHA 2022, ISTH 2018");
  } else {
    if (vhr) add("НМГ лечебно при ВТЭ", "только с трансфузией до 40–50", "low", "EHA 2022: очень высокий риск — трансфузии и полная доза НМГ не дольше 14 дней, не рутинно; иначе — пауза");
    else add("НМГ лечебно при ВТЭ", "пауза", "no", "ISTH 2018, EHA 2022: < 25 — пауза; полная доза — снова при > 50");
  }
  // ПОАК
  if (hit) add("ПОАК", bleed ? "лучше аргатробан" : "вариант лечения ГИТ", "low", bleed ? "ASH 2018: при высоком риске кровотечения — аргатробан или бивалирудин" : "ASH 2018; дозы экстраполированы с лечения ВТЭ; при тяжёлой дисфункции печени — без ПОАК");
  else if (p >= 100) add("ПОАК", "обычная доза", "ok", "тромбоциты не ограничивают");
  else if (p === 50) add("ПОАК", "на границе — осторожно", "low", "EHA 2022: 50 — ещё 2-я степень; EHRA 2021: 20–50 — ½ дозы и консилиум");
  else if (p > 50){
    if (st) add("ПОАК", "обычная доза, частый контроль", "ok", "EHA 2022: стабильные 50–100 и неклапанная ФП; EHRA 2021 — с осторожностью");
    else add("ПОАК", "временно НМГ", "low", "тромбоциты падают — EHA 2022: при острой ВТЭ НМГ лучше ПОАК, при ФП НМГ — временный вариант");
  } else if (p >= 20){
    add("ПОАК", p >= 25 ? "не назначать" : "отменить", "no", (p >= 25 ? "EHA 2022 (25–50): против ПОАК при ВТЭ и ФП" : "EHA 2022: < 25 — отменить") + "; EHRA 2021 (20–50): ½ дозы — только решением консилиума");
    if (vhr && p >= 25 && st) notes.push("ФП с очень высоким риском при стабильных 25–50 — можно рассмотреть НМГ 50% лечебной дозы вместо ПОАК (EHA 2022)");
  } else add("ПОАК", "отменить", "no", "EHRA 2021: < 20 — избегать, риск спонтанных кровотечений");
  // АСК
  if (p >= 50) add("АСК", "75–100 мг", "ok", "EHA 2022: продолжать" + (p < 75 && bleed ? "; при факторах кровотечения — АСК без ДААТ" : ""));
  else if (p >= 25) add("АСК", "низкая доза", "low", "EHA 2022: после ИИ или ТИА в последний месяц — монотерапия низкой дозой АСК");
  else if (p >= 10) add("АСК", "пауза до > 25", "no", "EHA 2022 после ИИ и ТИА; при > 10 АСК допускают только при очень высоком риске, например ОКС (EHA, ESC 2022, SCAI 2016)");
  else add("АСК", "отменить", "no", "< 10 — EHA 2022, ESC 2022, SCAI 2016");
  // клопидогрел
  if (p >= 50) add("Клопидогрел", "75 мг", "ok", "ESC 2022 (ОКС и ЧКВ): избегать только при < 30");
  else if (p >= 30) add("Клопидогрел", "допустим", "low", "ESC 2022 (ОКС и ЧКВ): избегать при < 30; после ИИ и ТИА EHA 2022 при 25–50 выбирает АСК");
  else add("Клопидогрел", "нет", "no", "ESC 2022 (ОКС и ЧКВ): < 30 — избегать" + (icas && p >= 25 ? "; EHA 2022 при стенозе допускает ДААТ с 25" : ""));
  // ДААТ
  const dn = icas ? "ДААТ при стенозе" : "ДААТ после малого ИИ или ТИА";
  if (icas){
    if (p >= 50) add(dn, "до 90 дней", "ok", "клопидогрел + АСК — EHA 2022, рек. 11a");
    else if (p >= 25) add(dn, bleed ? "только АСК" : "до 21 дня", bleed ? "no" : "low", bleed ? "факторы кровотечения — EHA 2022, рек. 11b" : "EHA 2022, рек. 11b: если нет дополнительных факторов кровотечения" + (p < 30 ? "; ESC 2022 (ОКС и ЧКВ) избегает клопидогрела при < 30 — решать индивидуально" : ""));
    else add(dn, "отменить", "no", "EHA 2022, рек. 11c: АСК — индивидуально, когда тромбоциты > 25");
  } else {
    if (p >= 100) add(dn, "по общим правилам", "ok", "тромбоциты не ограничивают");
    else if (p >= 75) add(dn, st ? "21 день" : "решать по динамике", st ? "ok" : "low", st ? "клопидогрел + АСК, затем АСК — EHA 2022, рек. 10a" : "тромбоциты падают — повтор через 1–2 дня; EHA 2022 рекомендует ДААТ при стабильной ТЦП 1-й степени");
    else if (p >= 50){
      if (bleed) add(dn, "только АСК", "no", "факторы кровотечения — EHA 2022, рек. 10b");
      else if (!st) add(dn, "решать по динамике", "low", "тромбоциты падают — повтор через 1–2 дня (EHA 2022); ДААТ — при стабильных");
      else add(dn, "21 день", "ok", "клопидогрел + АСК, затем АСК — EHA 2022, рек. 10b");
    }
    else if (p >= 25) add(dn, "только АСК", "no", "EHA 2022, рек. 10c");
    else add(dn, "нет", "no", "EHA 2022, рек. 10d: без антиагрегантов до > 25");
  }
  // тикагрелор
  if (p >= 100) add("Тикагрелор", "по общим показаниям", "ok", "тромбоциты не ограничивают");
  else if (p >= 75) add("Тикагрелор", "лучше клопидогрел", "low", "EHA 2022 при ТЦП называет только клопидогрел");
  else add("Тикагрелор", "нет", "no", p >= 50 ? "EHA 2022: < 75 — против ДААТ с тикагрелором" : "EHA 2022; ESC 2022 и SCAI 2016 — не при < 50");
  if (p < 50) add("Антиагрегант + антикоагулянт", "не сочетать", "no", "EHA 2022, рек. 13");
  // реперфузия
  if (p >= 100) add("ТЛТ", "тромбоциты не мешают", "ok", p < 150 ? "TRISP: при < 150 сВЧК чаще (ОШ 1,73), но ТЛТ не противопоказана" : "без подозрения на коагулопатию анализ не ждут — КР по ИИ 2024");
  else add("ТЛТ", "противопоказана", "no", "< 100 000/мкл — инструкция алтеплазы, AHA/ASA 2026; EHA 2022");
  if (p >= 50) add("Тромбэктомия", "по общим критериям", "ok", "EHA 2022: рассматривать всем подходящим");
  else if (p >= 25) add("Тромбэктомия", "можно рассмотреть", "low", "EHA 2022: по риску тромбоза и кровотечения");
  else add("Тромбэктомия", "по каждому случаю", "low", "EHA 2022: с трансфузией тромбоцитов или без");
  return { R, notes };
}

function renderPlan(){
  const box = $("pres");
  box.textContent = "";
  const p = numv("plt");
  if (!(p >= 0 && p <= 1500)){ box.append(line("Тромбоциты", "Введите число: 0–1500", "× 10⁹/л, как в анализе")); return; }
  const st = pc.tr === "st";
  const head = p >= 150 ? "норма" : fmtN(p) + " × 10⁹/л — " + (p < 20 ? "меньше 20" : p < 50 ? "20–50" : p === 50 ? "граница 50" : p <= 100 ? "больше 50" : "лёгкая ТЦП");
  const hn = p >= 150 ? "ограничений по тромбоцитам нет" : (p > 100 ? "EHA 2022: ещё не ТЦП (> 100)" : "EHA 2022: " + ehaGrade(p) + " · EHRA 2021: " + ehraBand(p)) + (st ? "" : " · тромбоциты снижаются");
  box.append(line("Уровень", head, hn, "lead" + (p < 20 ? " warn" : p >= 150 ? " ok" : "")));
  const r = plan(p, st);
  const list = el("ul", "dzr");
  for (const x of r.R) list.append(row(x[0], x[1], x[2], x[3]));
  const dw = el("div", "rl");
  dw.append(el("p", "rk", tp("Препараты и процедуры")));
  dw.append(list);
  box.append(dw);
  if (pc.hit) box.append(line("ГИТ", "Отменить все гепарины", "4Ts ≥ 4 — негепариновый антикоагулянт в лечебной дозе; при 4–5, высоком риске кровотечения и без других показаний — в профилактической; варфарин — после восстановления тромбоцитов; рутинно тромбоциты не переливать (ASH 2018)", "warn"));
  if (p < 150){
    const ctl = p >= 100 ? ["по клинической ситуации", ""] : p >= 50 ? ["через 1–2 дня", "EHA 2022; EHRA 2021 — частый контроль клиники и тромбоцитов"] : ["очень частый", "EHRA 2021: очень частый контроль клиники и тромбоцитов; решение — мультидисциплинарной командой"];
    box.append(line("Контроль тромбоцитов", ctl[0], ctl[1]));
  }
  if (p < 10 && !pc.hit) box.append(line("Трансфузия тромбоцитов", "обсудить профилактически", "AABB 2025: < 10 у некровоточащих на химиотерапии или после аллогенной трансплантации и при ТЦП потребления без большого кровотечения; при ИТП — с гематологом", "warn"));
  else if (pc.vhr && p < 50 && !pc.hit) box.append(line("Трансфузия тромбоцитов", "обсудить до 40–50", "только ради полной дозы НМГ при очень высоком риске, не дольше 14 дней (EHA 2022)"));
  if (p < 100){
    r.notes.push("неожиданный результат без кровоточивости — мазок и повторный подсчёт: псевдотромбоцитопения");
    r.notes.push("всем на антитромботиках при ТЦП — ИПП, с клопидогрелом — пантопразол; без НПВП (EHA 2022)");
    r.notes.push("EHA 2022 написаны для онкобольных; при другой причине ТЦП — по аналогии");
  }
  for (const n of r.notes) box.append(el("p", "res-note", tp(n.charAt(0).toUpperCase() + n.slice(1) + ".")));
}

// ——— 4Ts
const t4 = [2, 2, 0, 1];
function balls(n){ const m = n % 10, h = n % 100; return n + " " + (m === 1 && h !== 11 ? "балл" : m >= 2 && m <= 4 && (h < 12 || h > 14) ? "балла" : "баллов"); }
function render4T(){
  const box = $("tres");
  box.textContent = "";
  const sum = t4.reduce((a, b) => a + b, 0);
  let v, n, cls;
  if (sum <= 3){ v = "низкая вероятность ГИТ"; n = "лабораторные тесты не нужны; гепарин продолжают, если он показан (ASH 2018)"; cls = "ok"; }
  else if (sum <= 5){ v = "средняя вероятность ГИТ"; n = "отменить все гепарины, начать негепариновый антикоагулянт, иммуноанализ на антитела; при высоком риске кровотечения и без других показаний — профилактическая доза (ASH 2018)"; cls = "warn"; }
  else { v = "высокая вероятность ГИТ"; n = "отменить все гепарины, негепариновый антикоагулянт в лечебной дозе, иммуноанализ на антитела (ASH 2018)"; cls = "warn"; }
  box.append(line("4Ts", balls(sum) + " — " + v, n, "lead " + cls));
}

function pressOne(sel, attr, val){
  document.querySelectorAll(sel).forEach(b => b.setAttribute("aria-pressed", String(b.dataset[attr] === val)));
}
function initCalc(){
  document.querySelectorAll("[data-tr]").forEach(b => b.addEventListener("click", () => { pc.tr = b.dataset.tr; pressOne("[data-tr]", "tr", pc.tr); renderPlan(); }));
  document.querySelectorAll("[data-flag]").forEach(b => b.addEventListener("click", () => {
    const k = b.dataset.flag; pc[k] = !pc[k]; b.setAttribute("aria-pressed", String(pc[k])); renderPlan();
  }));
  ["input", "change"].forEach(ev => $("plt").addEventListener(ev, renderPlan));
  document.querySelectorAll("[data-tq]").forEach(b => b.addEventListener("click", () => {
    const q = +b.dataset.tq; t4[q] = +b.dataset.tv;
    document.querySelectorAll('[data-tq="' + q + '"]').forEach(x => x.setAttribute("aria-pressed", String(+x.dataset.tv === t4[q])));
    render4T();
  }));
  renderPlan();
  render4T();
}
"""
rep("function boot(){\n", CALC + "\nfunction boot(){\n")
rep('      const rule = el("p", "t-rule"); rule.append(richText(t.rule)); body.append(rule);',
    '      String(t.rule).split("\\n\\n").forEach(par => { const rule = el("p", "t-rule"); rule.append(richText(par)); body.append(rule); });')
rep("  connectCloud();\n}\nboot();", "  initCalc();\n  connectCloud();\n}\nboot();")
assert "ctp:" not in s and "Перфузия" not in s and "КТ-перфузия" not in s
s, _n = re.subn(r'(<(?:label|p) class="fl"[^>]*>[^<]*?)<small>', r'\1 <small>', s)
assert _n >= 1, _n
pathlib.Path("thrombo/template.html").write_text(s)
print("ok", len(s), _n)
