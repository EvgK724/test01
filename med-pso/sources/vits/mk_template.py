# Шаблон «ВИТС после инсульта» собираю из шаблона «КТ-перфузия» так же, как «Раннюю антикоагуляцию»:
# тренажёр тот же (русский, без озвучки), вкладка «Справочник» — дозы с калькулятором режима, цели,
# сроки контроля с калькулятором дат, печень и мышцы, снижение дозы, особые ситуации, ловушки, темы, источники.
import pathlib, re
s = pathlib.Path("ctp/template.html").read_text()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:70], s.count(a))
    s = s.replace(a, b)

rep("<title>КТ-перфузия</title>", "<title>ВИТС после инсульта</title>")
rep("  .opts.c1{grid-template-columns:1fr}\n  .opts.c2{grid-template-columns:1fr 1fr}\n  .opts.c3{grid-template-columns:repeat(3,1fr)}\n",
    "  .opts.c1{grid-template-columns:minmax(0,1fr)}\n  .opts.c2{grid-template-columns:repeat(2,minmax(0,1fr))}\n  .opts.c3{grid-template-columns:repeat(3,minmax(0,1fr))}\n")
rep("  body.wide #drill .opts.c2,body.wide #drill .opts.c3{grid-template-columns:1fr}",
    "  body.wide #drill .opts.c2,body.wide #drill .opts.c3{grid-template-columns:minmax(0,1fr)}")
rep("  const cols = longest > 9 ? 1 : (n === 3 ? 3 : 2);",
    "  const cols = longest > 8 ? 1 : (n === 3 ? (longest <= 5 ? 3 : 1) : 2);   // три в ряд — только короткие: 48, < 1,4, 21; два — до 8 знаков")
rep("  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n",
    "  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n  [hidden]{display:none!important}\n")

exec(pathlib.Path("vits/_oac_css.py").read_text())   # CSS — общий с «Ранней антикоагуляцией»
CSS += r"""
  .mon{list-style:none;margin:2px 0 0;padding:0}
  .mon li{padding:10px 0;border-top:1px solid var(--line)}
  .mon li:first-child{border-top:0}
  .mon .sw-k{font-size:19px}
  .mon .sw-v{font-size:15px}
  .dzr .d.ok{color:var(--yes-text)}
  .dzr .d.now{color:var(--text)}
  .rk + .dzr{margin-top:2px}
  .tv{text-wrap:balance}
  .q,.err s,.err .good,.err-note,.rv,.rn,.dv,.dk,.tv,.tk,.ad-v,.iv-v,.sw-k,.sw-v,.cp-en,.cp-ru,.t-rule,.ex-en,.ex-ru,.why,.dzr .n,.dzr .d,.abbr dd,.algo-note{hyphens:auto;-webkit-hyphens:auto}
"""
rep("  /* ——— Планшет */\n", CSS + "\n  /* ——— Планшет */\n")
assert s.count('<div class="app"') == 1
s = s.replace('<div class="app"', '<div class="app" lang="ru"')   # переносы по-русски в Safari
rep("  body.wide #rule{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);column-gap:36px;align-items:start}",
    "  body.wide #rule{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:36px;align-items:start}")

# ——— вкладки
rep('aria-controls="rule">Правила</button>', 'aria-controls="rule">Справочник</button>')
rep('<button class="big" id="toRule" type="button">Правила</button>', '<button class="big" id="toRule" type="button">Справочник</button>')

# ——— без озвучки
a = s.index("// ——— Озвучка:"); b = s.index("// ——— Очередь")
s = s[:a] + "function stopAudio(){}   // озвучки в этом приложении нет\n\n" + s[b:]
assert "speechSynthesis" not in s and "playClip" not in s

# ——— вкладка «Справочник»
a = s.index('    <div class="r-left">'); b = s.index('  </section>\n</div>')
s = s[:a] + '''    <div class="r-left">
      <h1 class="r-title">ВИТС после инсульта</h1>
      <p class="r-sub">Высокоинтенсивная терапия статинами в&nbsp;ранней вторичной профилактике ИИ и&nbsp;ТИА: препараты и&nbsp;дозы, возраст, сроки старта, контроля и&nbsp;снижения дозы. Основа&nbsp;— <b>КР&nbsp;по&nbsp;ИИ&nbsp;2024</b>; рядом&nbsp;— новые РКИ <b>INSPIRES</b> (2024) и&nbsp;<b>STAREE</b> (2026), мета‑анализ <b>CTT</b> (2026).</p>
      <section class="abbr" aria-labelledby="h-abbr">
        <h2 class="algo-h" id="h-abbr">Сокращения</h2>
        <dl>
          <div><dt>ВИТС</dt><dd>высокоинтенсивная терапия статинами: аторвастатин 40–80&nbsp;мг или розувастатин 20–40&nbsp;мг, снижает ХС&nbsp;ЛНП на&nbsp;50% и&nbsp;больше</dd></div>
          <div><dt>ХС ЛНП</dt><dd>холестерин липопротеинов низкой плотности, ммоль/л <span class="nw">(мг/дл&nbsp;÷&nbsp;38,7)</span></dd></div>
          <div><dt>ВГН</dt><dd>верхняя граница нормы</dd></div>
          <div><dt>КФК</dt><dd>креатинфосфокиназа</dd></div>
          <div><dt>КК</dt><dd>клиренс креатинина по&nbsp;Кокрофту–Голту</dd></div>
          <div><dt>иPCSK9</dt><dd>алирокумаб, эволокумаб, инклисиран</dd></div>
          <div><dt>УУР</dt><dd>уровень убедительности рекомендаций: A&nbsp;— сильная, C&nbsp;— слабая</dd></div>
          <div><dt>КР&nbsp;по&nbsp;ИИ&nbsp;2024</dt><dd>клинические рекомендации «Ишемический инсульт и&nbsp;транзиторная ишемическая атака»</dd></div>
          <div><dt>КР&nbsp;по&nbsp;ДЛП&nbsp;2023</dt><dd>клинические рекомендации «Нарушения липидного обмена»</dd></div>
          <div><dt>Приказ 168н</dt><dd>порядок диспансерного наблюдения за&nbsp;взрослыми, Минздрав РФ, 2022; цитируется в&nbsp;КР&nbsp;по&nbsp;ИИ&nbsp;2024</dd></div>
        </dl>
      </section>
      <nav class="jump" aria-label="Разделы справочника">
        <button type="button" data-to="s-dose">Дозы</button>
        <button type="button" data-to="s-target">Цель</button>
        <button type="button" data-to="s-ctrl">Контроль</button>
        <button type="button" data-to="s-safe">Печень и&nbsp;мышцы</button>
        <button type="button" data-to="s-red">Снижение дозы</button>
        <button type="button" data-to="s-spec">Особые случаи</button>
        <button type="button" data-to="s-topics">Темы</button>
      </nav>
      <section class="algo" id="s-dose" aria-labelledby="h-dose">
        <h2 class="algo-h" id="h-dose">Кому и&nbsp;в&nbsp;какой дозе</h2>
        <div class="dz">
<!--__DOSES__-->
        </div>
        <p class="algo-note"><b>Кому.</b> ВИТС в&nbsp;максимально переносимых дозах&nbsp;— большинству взрослых с&nbsp;ИИ и&nbsp;ТИА (КР&nbsp;по&nbsp;ИИ&nbsp;2024, УУР&nbsp;A). Исходный ЛНП на&nbsp;показание не&nbsp;влияет.</p>
        <p class="algo-note"><b>Когда.</b> Не&nbsp;позднее 48&nbsp;ч от&nbsp;развития ИИ, при&nbsp;ТИА&nbsp;— сразу. Принимал статин до&nbsp;инсульта&nbsp;— продолжить без перерыва. Лечение пожизненное.</p>
        <p class="algo-note"><b>Новые данные.</b> INSPIRES (2024): аторвастатин 80&nbsp;мг в&nbsp;первые 72&nbsp;ч против старта на&nbsp;4‑й день&nbsp;— инсультов поровну, функциональный исход лучше (ОШ&nbsp;0,83). STAREE (2026): аторвастатин 40&nbsp;мг у&nbsp;людей от&nbsp;70&nbsp;лет без ССЗ, СД и&nbsp;деменции&nbsp;— сердечно‑сосудистых событий на&nbsp;30% меньше; серьёзных нежелательных явлений поровну, мышечные, печёночные и&nbsp;связанные с&nbsp;СД&nbsp;— чаще.</p>
        <div class="calc" id="pcalc">
          <p class="calc-h">Подобрать режим<small>Пример&nbsp;— замените данными пациента</small></p>
          <div class="g2">
            <div><label class="fl" for="age">Возраст, лет</label><input class="inp" id="age" type="number" inputmode="numeric" min="18" max="110" step="1" value="68"></div>
            <div><label class="fl" for="kk">КК<small>мл/мин</small></label><input class="inp" id="kk" type="number" inputmode="numeric" min="5" max="250" step="1" placeholder="не указан"></div>
          </div>
          <label class="fl" for="ldl">ХС ЛНП сейчас<small>ммоль/л</small></label>
          <input class="inp" id="ldl" type="number" inputmode="decimal" min="0.3" max="20" step="0.1" value="3.2">
          <p class="fl" id="curLbl">Что принимает сейчас</p>
          <div class="seg s2" role="group" aria-labelledby="curLbl">
            <button type="button" class="chip" data-cur="none" aria-pressed="true">Статина нет</button>
            <button type="button" class="chip" data-cur="mod" aria-pressed="false">Умеренная</button>
            <button type="button" class="chip" data-cur="high" aria-pressed="false">ВИТС</button>
            <button type="button" class="chip" data-cur="highez" aria-pressed="false">ВИТС + эзетимиб</button>
          </div>
          <div class="flags" role="group" aria-label="Что ещё учесть">
            <button type="button" class="chip" data-flag="extreme" aria-pressed="false">Экстремальный риск</button>
            <button type="button" class="chip" data-flag="asian" aria-pressed="false">Азиатская раса</button>
            <button type="button" class="chip" data-flag="hypo" aria-pressed="false">Гипотиреоз</button>
            <button type="button" class="chip" data-flag="fibr" aria-pressed="false">Фибраты</button>
            <button type="button" class="chip" data-flag="myo" aria-pressed="false">Миопатия на&nbsp;статине в&nbsp;анамнезе</button>
            <button type="button" class="chip" data-flag="cyclo" aria-pressed="false">Циклоспорин</button>
            <button type="button" class="chip" data-flag="amio" aria-pressed="false">Амиодарон или верапамил</button>
            <button type="button" class="chip" data-flag="warf" aria-pressed="false">Варфарин</button>
          </div>
          <div class="res" id="pres" aria-live="polite"></div>
        </div>
      </section>
      <section class="algo algo-2" id="s-target" aria-labelledby="h-target">
        <h2 class="algo-h" id="h-target">Цель ХС ЛНП, ммоль/л</h2>
        <div class="tt">
<!--__TARGETS__-->
        </div>
        <p class="algo-note">КР&nbsp;по&nbsp;ИИ&nbsp;2024: <span class="nw">&lt;&nbsp;1,4</span> или как минимум снижение на&nbsp;50%. КР&nbsp;по&nbsp;ДЛП&nbsp;2023 требуют обоих условий, и&nbsp;тогда берут более строгое: при&nbsp;исходном ЛНП 2,4 цель&nbsp;— <span class="nw">≤&nbsp;1,2</span>, при&nbsp;3,6&nbsp;— <span class="nw">&lt;&nbsp;1,4</span>. TST: выигрыш был при&nbsp;снижении ЛНП больше чем на&nbsp;50% (ОР&nbsp;0,61), а&nbsp;не&nbsp;меньше (ОР&nbsp;0,96). ESO&nbsp;2022 ставят цель мягче&nbsp;— <span class="nw">&lt;&nbsp;1,8</span>.</p>
      </section>
      <section class="algo" id="s-ctrl" aria-labelledby="h-ctrl">
        <h2 class="algo-h" id="h-ctrl">Сроки контроля</h2>
        <ul class="mon">
<!--__MONITOR__-->
        </ul>
        <p class="algo-note">Инструкции строже: аторвастатин&nbsp;— печёночные пробы через 6 и&nbsp;12&nbsp;недель, розувастатин&nbsp;— через 3&nbsp;месяца. Раньше 4&nbsp;недель ЛНП не&nbsp;оценивают: максимум эффекта&nbsp;— к&nbsp;4‑й неделе.</p>
        <div class="calc" id="mcalc">
          <p class="calc-h">Посчитать даты контроля<small>Пример&nbsp;— укажите даты пациента</small></p>
          <label class="fl" for="start">Старт или смена дозы</label>
          <input class="inp" id="start" type="date">
          <label class="fl" for="dis">Выписка<small>для диспансерных визитов</small></label>
          <div class="inp-row">
            <input class="inp" id="dis" type="date">
            <button type="button" class="x" id="disClear" aria-label="Без даты выписки" hidden>×</button>
          </div>
          <div class="res" id="mres" aria-live="polite"></div>
        </div>
      </section>
      <div class="go-wrap"><button class="big primary" id="go" type="button">Начать тренировку</button></div>
    </div>
    <div class="r-right">
      <h2 class="lbl" id="s-safe">Печень и&nbsp;мышцы</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__SAFETY__-->
        </ul>
      </div>
      <p class="mx-note">Больше 90% мышечных жалоб на&nbsp;статине&nbsp;— не&nbsp;от&nbsp;статина (CTT&nbsp;2022); в&nbsp;SAMSON 90% симптомов вызывала и&nbsp;таблетка‑плацебо. Непереносимость по&nbsp;КР&nbsp;— побочные эффекты после отмены и&nbsp;рестарта, в&nbsp;том числе другим статином или в&nbsp;меньшей дозе.</p>
      <h2 class="lbl" id="s-red">Когда снижать дозу</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__REDUCE__-->
        </ul>
      </div>
      <h2 class="lbl" id="s-spec">Особые ситуации</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__SPECIAL__-->
        </ul>
      </div>
      <p class="mx-note">Кровоизлияния: в&nbsp;SPARCL геморрагических инсультов на&nbsp;аторвастатине 80&nbsp;мг&nbsp;— 55 против 33, ишемических&nbsp;— 218 против 274. В&nbsp;TST внутричерепные кровоизлияния с&nbsp;низким ЛНП не&nbsp;были связаны; предикторы&nbsp;— неконтролируемая АГ и&nbsp;антикоагулянты.</p>
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
    'const LS_STATE = "vits:state";\nconst LS_TAB = "vits:tab";\nconst LS_OPEN = "vits:open";')
rep('["apple-mobile-web-app-title", "Перфузия"],', '["apple-mobile-web-app-title", "ВИТС"],')
rep("// Новые карточки идут вперемешку по темам: метод, карты, ядро и пенумбра, коллатерали, отбор, ловушки и отчёт чередуются.",
    "// Новые карточки идут вперемешку по темам: цель, дозы, возраст, старт, контроль, эскалация и безопасность чередуются.")

CALC = r"""
// ——— Переход к разделам справочника
document.querySelectorAll(".jump button").forEach(b => b.addEventListener("click", () => {
  const t = document.getElementById(b.dataset.to);
  if (!t) return;
  const smooth = !(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  try{ t.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" }); }catch(e){ t.scrollIntoView(); }
}));

// ——— Общие помощники калькуляторов
const plan = { cur: "none", extreme: false, asian: false, hypo: false, fibr: false, myo: false, cyclo: false, amio: false, warf: false };
const fmtD = new Intl.DateTimeFormat("ru-RU", { weekday: "short", day: "numeric", month: "long" });
const fmtDM = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long" });
const fmtDMY = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long", year: "numeric" });
function pad2(n){ return String(n).padStart(2, "0"); }
function toDateInput(d){ return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate()); }
function fromDate(v){
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(v || "");
  return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null;
}
function today0(){ const d = new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
function addDays(d, n){ return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n); }
function addMonths(d, n){
  const y = d.getFullYear(), m = d.getMonth() + n;
  const last = new Date(y, m + 1, 0).getDate();
  return new Date(y, m, Math.min(d.getDate(), last));
}
function span(a, b){
  const x = fmtDM.format(a), y = fmtDM.format(b);
  if (a.getMonth() === b.getMonth() && a.getFullYear() === b.getFullYear()) return a.getDate() + "–" + y;
  return x + " – " + y;
}
// неразрывные пробелы и тире в строках калькуляторов: «40–80 мг», «4–12 недель», «< 1,4» не рвутся
function tp(s){
  return String(s)
    .replace(/(\d)–(\d)/g, "$1–⁠$2")
    .replace(/(\d) (?=(?:мг|мл|мин|лет|ч(?![а-яё])|дн|сут|кг|ммоль|мкмоль|недел|месяц|ВГН|янв|фев|мар|апр|ма[яй]|июн|июл|авг|сен|окт|ноя|дек))/g, "$1 ")
    .replace(/ ([×<>≤≥=≈−±÷]) /g, " $1 ")
    .replace(/ \+ /g, " + ")
    .replace(/ХС ЛНП/g, "ХС ЛНП").replace(/КР по /g, "КР по ")
    .replace(/(^|[\s(])([<>≤≥≈]) (?=\d)/g, "$1$2 ")
    .replace(/(КК|ЛНП|КФК|АЛТ|ОР|ОШ) (?=[\d<>≤≥=≈])/g, "$1 ")
    .replace(/(^|[\s(«])(не|в|с|к|и|а|о|у|на|по|за|из|от|до|со|но|же|ли|при|без|для) /g, "$1$2 ")
    .replace(/ — /g, " — ");
}
function pillD(now, from, to){
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
function num(id){ const v = String($(id).value).replace(",", ".").trim(); return v === "" ? NaN : Number(v); }
function row(name, dose, cls, why){
  const li = el("li");
  li.append(el("span", "n", tp(name)), el("span", "d" + (cls ? " " + cls : ""), tp(dose)));
  if (why) li.append(el("span", "w", tp(why)));
  return li;
}
function joinRu(a){ return a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " и " + a[a.length - 1]; }
function dec(x){ return String(Math.round(x * 100) / 100).replace(".", ","); }
function dec1(x){ return (Math.round(x * 10) / 10).toFixed(1).replace(".", ","); }

// ——— Калькулятор режима: цель ЛНП (КР по ИИ 2024), ожидаемый ЛНП (табл. А3.11 КР по ДЛП 2023), дозы по инструкциям
const CUT = { none: 0, mod: 0.30, high: 0.50, highez: 0.65 };
const CUR_NAME = { none: "статина нет", mod: "умеренная терапия", high: "ВИТС", highez: "ВИТС + эзетимиб" };
function renderPlan(){
  const box = $("pres");
  box.textContent = "";
  const age = num("age"), ldl = num("ldl");
  const kkRaw = String($("kk").value).trim(), kk = kkRaw === "" ? null : num("kk");
  if (!(age >= 18 && age <= 110) || !(ldl >= 0.3 && ldl <= 20)){
    box.append(el("p", "res-note", tp("Введите возраст (18–110 лет) и ХС ЛНП (0,3–20 ммоль/л).")));
    return;
  }
  if (kk !== null && !(kk >= 5 && kk <= 250)){
    box.append(el("p", "res-note", tp("КК — от 5 до 250 мл/мин или оставьте поле пустым.")));
    return;
  }
  const cur = plan.cur, old = age > 75;
  const base = ldl / (1 - CUT[cur]);          // исходный без терапии: сейчас или расчётно
  const half = base / 2;
  const lim = plan.extreme ? 1.0 : 1.4;
  const atGoal = cur !== "none" && ldl < lim - 1e-9;                       // КР по ИИ 2024: < 1,4 (экстремальный риск — < 1,0)
  const strictGap = !plan.extreme && half < 1.4 && ldl > half + 1e-9;      // КР по ДЛП 2023: ещё и снижение ≥ 50%

  // цель
  let tv, tn;
  if (plan.extreme){ tv = "< 1,0 ммоль/л"; tn = "экстремальный риск — КР по ИИ 2024, УУР B"; }
  else if (half < 1.4){ tv = "< 1,4; по КР по ДЛП 2023 — ≤ " + dec(half); tn = "КР по ИИ 2024: < 1,4 или хотя бы −50%; КР по ДЛП 2023 требуют обоих — здесь строже −50%"; }
  else { tv = "< 1,4 ммоль/л"; tn = "КР по ИИ 2024: < 1,4 или хотя бы −50% (≤ " + dec(half) + "); КР по ДЛП 2023 — оба условия, строже < 1,4"; }
  if (cur !== "none") tn += " · исходный без терапии — расчётно ≈ " + dec1(base) + " (табл. А3.11 КР по ДЛП 2023)";
  box.append(line("Цель ХС ЛНП", tv, tn));

  // что делать
  let av, an, acls = "";
  if (plan.cyclo && !atGoal){
    av = "ВИТС недоступна: аторвастатин не выше 10 мг + эзетимиб"; an = "розувастатин с циклоспорином противопоказан; нет цели — иPCSK9 (КР по ИИ 2024, УУР A)";
  } else if (cur === "none"){
    if (old){ av = "Умеренная интенсивность: аторвастатин 10–20 мг или розувастатин 5–10 мг"; an = "старше 75 лет, статина не было — КР по ИИ 2024, УУР C; дальше титровать до цели — КР по ДЛП 2023"; }
    else { av = "ВИТС: аторвастатин 40–80 мг или розувастатин 20–40 мг"; an = "не позднее 48 ч от развития ИИ; нет цели — до максимально переносимой дозы"; }
  } else if (atGoal){
    av = "Цель достигнута — та же терапия"; an = "дозу не снижают; липиды раз в год" + (old && cur === "high" ? "; старше 75 лет — интенсивность не снижать (КР по ИИ 2024)" : "") + (strictGap ? "; по КР по ДЛП 2023 ещё нужно ≤ " + dec(half) : ""); acls = "ok";
  } else if (cur === "mod"){
    if (old){ av = "Продолжить без перерыва и усилить"; an = "титровать дозу или добавить эзетимиб к низкой дозе статина — КР по ДЛП 2023"; }
    else { av = "Перевести на ВИТС: аторвастатин 40–80 мг или розувастатин 20–40 мг"; an = "статин не прерывать ни на день"; }
  } else if (cur === "high"){
    av = "Продолжить ВИТС без перерыва"; an = "доза уже максимальная переносимая — + эзетимиб 10 мг; нет — сначала повысить" + (old ? "; старше 75 лет интенсивность не снижать (КР по ИИ 2024)" : "");
  } else {
    av = "Продолжить и добавить иPCSK9"; an = "алирокумаб, эволокумаб или инклисиран — КР по ИИ 2024, УУР A";
  }
  if (cur !== "none" && !atGoal) an += " · решение — по анализу через 4–12 недель на максимально переносимой дозе";
  box.append(line("Что делать · " + CUR_NAME[cur], av, an, acls));
  if (cur !== "none") box.append(line("При поступлении", "Не прерывать статин", "отмена на 3 дня: mRS > 2 у 60% против 39% (Blanco 2007)", "ok"));
  if (cur === "none" && base > 5.0) box.append(line("ЛНП > 5,0", "Можно сразу статин + эзетимиб + иPCSK9", "КР по ДЛП 2023, экстремальный или очень высокий риск"));
  else if (cur === "none" && base > 4.0) box.append(line("ЛНП > 4,0", "Можно сразу статин + эзетимиб", "лучше в одной таблетке — КР по ДЛП 2023"));

  // ожидаемый ЛНП по ступеням
  const steps = [["Умеренная терапия", 0.30, "mod"], ["ВИТС", 0.50, "high"], ["ВИТС + эзетимиб", 0.65, "highez"], ["ВИТС + эзетимиб + иPCSK9", 0.85, "all"]];
  const shown = steps.filter(st => st[2] !== "mod" || old || cur === "mod");
  const wrap = el("div", "rl");
  wrap.append(el("p", "rk", tp("Ожидаемый ЛНП · табл. А3.11 КР по ДЛП 2023")));
  const ul = el("ul", "dzr");
  let first = true;
  for (const [name, r, key] of shown){
    const v = base * (1 - r);
    const ok = v < lim - 1e-9;
    const notes = ["−" + Math.round(r * 100) + "%"];
    if (key === cur) notes.push("сейчас");
    if (ok && first){ notes.push("первая ступень с ЛНП < " + (plan.extreme ? "1,0" : "1,4") + (!plan.extreme && half < 1.4 && v > half + 1e-9 ? "; для −50% по КР по ДЛП 2023 — дальше" : "")); first = false; }
    ul.append(row(name, "≈ " + dec1(v), ok ? "ok" : "low", notes.join(" · ")));
  }
  wrap.append(ul);
  box.append(wrap);

  // препараты
  const dw = el("div", "rl");
  dw.append(el("p", "rk", tp("Препараты · инструкции")));
  const dl = el("ul", "dzr");
  const newOld = old && cur === "none";
  // аторвастатин
  const an2 = [];
  let ad = newOld ? "10–20 мг" : "40–80 мг", acl2 = "";
  if (plan.cyclo){ ad = "не выше 10 мг"; acl2 = "low"; an2.push("циклоспорин"); }
  if (plan.amio){ if (!plan.cyclo){ acl2 = "low"; } an2.push("амиодарон или верапамил — снизить максимальную дозу"); }
  if (plan.warf) an2.push("варфарин — протромбиновое время до старта");
  if (!an2.length) an2.push("по КК и возрасту не корректируют");
  dl.append(row("Аторвастатин", ad, acl2, an2.join(" · ")));
  // розувастатин
  const contra = [], rlim = [], start5 = [];
  if (kk !== null && kk < 30) contra.push("КК < 30");
  if (plan.cyclo) contra.push("циклоспорин");
  if (kk !== null && kk < 60 && kk >= 30){ rlim.push("КК < 60"); start5.push("КК < 60"); }
  if (plan.asian){ rlim.push("азиатская раса"); start5.push("азиатская раса"); }
  if (plan.hypo){ rlim.push("гипотиреоз"); start5.push("гипотиреоз"); }
  if (plan.fibr){ rlim.push("фибраты"); start5.push("фибраты"); }
  if (plan.myo){ rlim.push("миотоксичность статинов или фибратов в анамнезе"); start5.push("миотоксичность"); }
  const rn2 = [];
  let rd, rcl = "";
  if (contra.length){ rd = "противопоказан"; rcl = "no"; rn2.push(joinRu(contra)); }
  else {
    if (newOld) rd = "5–10 мг";
    else if (rlim.length){ rd = "не выше 20 мг"; rcl = "low"; }
    else { rd = "20–40 мг"; rn2.push("инструкция: старт 5–10 мг, 20 мг — через 4 недели, 40 мг — если на 20 мг нет цели"); }
    if (rlim.length) rn2.push("40 мг нельзя: " + joinRu(rlim));
    if (start5.length) rn2.push("старт — 5 мг");
    else if (age > 70) rn2.push("старше 70 лет — в ряде инструкций старт 5 мг");
    if (plan.warf) rn2.push("варфарин — МНО при старте, смене дозы и отмене");
  }
  dl.append(row("Розувастатин", rd, rcl, rn2.join(" · ")));
  // эзетимиб
  if (cur === "highez") dl.append(row("Эзетимиб", "10 мг", "", "уже принимает"));
  else dl.append(row("Эзетимиб", "10 мг", "", "если за 4–12 недель на максимально переносимом статине нет цели — КР по ИИ 2024, УУР C"));
  dw.append(dl);
  box.append(dw);
  const notes = [];
  if (kk === null) notes.push("КК не указан — почечные ограничения розувастатина не учтены.");
  notes.push("Проценты — ориентир КР по ДЛП 2023 (≈ 30, 50, 65, 85%), ответ у пациента индивидуален. ЛНП в мг/дл ÷ 38,7 = ммоль/л.");
  box.append(el("p", "res-note", tp(notes.join(" "))));
}

// ——— Калькулятор дат контроля: КР по ИИ 2024, КР по ДЛП 2023, Приказ 168н, инструкции
function renderCtrl(){
  const box = $("mres");
  box.textContent = "";
  $("disClear").hidden = !$("dis").value;
  $("dis").parentElement.classList.toggle("has-x", !!$("dis").value);
  const st = fromDate($("start").value);
  if (!st){ box.append(line("Даты", "Укажите дату старта или смены дозы", "")); return; }
  const now = today0();
  const w4 = addDays(st, 28), w6 = addDays(st, 42), w12 = addDays(st, 84), m3 = addMonths(st, 3);
  box.append(line("Приказ 168н", "АЛТ, АСТ, КФК — " + fmtD.format(w4), "через 4 недели от начала терапии, для смены дозы — по аналогии; раньше — при мышечных симптомах", "", pillD(now, w4, addDays(w4, 7))));
  box.append(line("КР по ИИ 2024", "Липиды натощак, АЛТ, АСТ: " + span(w4, w12), "через 4–12 недель; КР по ДЛП 2023 — 8 ± 4 недели, то же окно", "", pillD(now, w4, addDays(w12, 1))));
  box.append(line("Решение по анализу", "Цель есть — та же доза, липиды раз в год", "нет — до максимально переносимой дозы или + эзетимиб 10 мг, затем снова через 4–12 недель; после ОНМК КР по ДЛП 2023 — ХС ЛНП дважды в год", "ok"));
  box.append(line("Инструкции · печёночные пробы", "Аторвастатин — " + fmtDM.format(w6) + " и " + fmtDM.format(w12), "через 6 и 12 недель; розувастатин — через 3 месяца: " + fmtDM.format(m3)));
  const dis = fromDate($("dis").value);
  if (!dis){ box.append(el("p", "res-note", tp("Укажите дату выписки — появятся даты диспансерных визитов по Приказу 168н."))); return; }
  const wrap = el("div", "rl");
  wrap.append(el("p", "rk", tp("Приказ 168н · диспансерные визиты")));
  wrap.append(el("p", "rn", tp("24 месяца: в первый год — не реже раза в 3 месяца, затем — раз в 6 месяцев; ХС ЛНП, АД, ЧСС, ЭКГ")));
  const ul = el("ul", "dzr");
  let next = true;
  for (const mo of [3, 6, 9, 12, 18, 24]){
    const d = addMonths(dis, mo);
    const soon = next && d >= now;
    if (soon) next = false;
    ul.append(row(mo + " мес", fmtDMY.format(d), soon ? "now" : "", soon ? "ближайший" : ""));
  }
  wrap.append(ul);
  box.append(wrap);
}

function pressOne(sel, attr, val){
  document.querySelectorAll(sel).forEach(b => b.setAttribute("aria-pressed", String(b.dataset[attr] === val)));
}
function initCalc(){
  const t = today0();
  $("start").value = toDateInput(t);
  $("dis").value = toDateInput(addDays(t, 10));
  document.querySelectorAll("[data-cur]").forEach(b => b.addEventListener("click", () => { plan.cur = b.dataset.cur; pressOne("[data-cur]", "cur", plan.cur); renderPlan(); }));
  document.querySelectorAll("[data-flag]").forEach(b => b.addEventListener("click", () => {
    const k = b.dataset.flag; plan[k] = !plan[k]; b.setAttribute("aria-pressed", String(plan[k])); renderPlan();
  }));
  ["age", "kk", "ldl"].forEach(id => { $(id).addEventListener("input", renderPlan); $(id).addEventListener("change", renderPlan); });
  ["start", "dis"].forEach(id => { $(id).addEventListener("input", renderCtrl); $(id).addEventListener("change", renderCtrl); });
  $("disClear").addEventListener("click", () => { $("dis").value = ""; renderCtrl(); });
  renderPlan();
  renderCtrl();
}
"""
rep("function boot(){\n", CALC + "\nfunction boot(){\n")
rep('      const rule = el("p", "t-rule"); rule.append(richText(t.rule)); body.append(rule);',
    '      String(t.rule).split("\\n\\n").forEach(par => { const rule = el("p", "t-rule"); rule.append(richText(par)); body.append(rule); });')
rep("  connectCloud();\n}\nboot();", "  initCalc();\n  connectCloud();\n}\nboot();")
assert "ctp:" not in s and "Перфузия" not in s and "КТ-перфузия" not in s
s, _n = re.subn(r'(<(?:label|p) class="fl"[^>]*>[^<]*?)<small>', r'\1 <small>', s)   # «КК мл/мин» переносится
assert _n == 3, _n
pathlib.Path("vits/template.html").write_text(s)
print("ok", len(s))
