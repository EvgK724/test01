# Шаблон «Ранняя антикоагуляция» собираю из шаблона «КТ-перфузия»: тренажёр тот же (русский, без озвучки),
# вкладка «Справочник» — сроки по ELAN с калькулятором дат, дозы ПОАК с калькулятором КК,
# переходы, антидоты, тромболизис на антикоагулянте, ловушки, темы, источники.
import pathlib
s = pathlib.Path("ctp/template.html").read_text()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:70], s.count(a))
    s = s.replace(a, b)

rep("<title>КТ-перфузия</title>", "<title>Ранняя антикоагуляция</title>")
# ——— без наслоений: колонки вариантов не уже содержимого, длинные слова переносятся
rep("  .opts.c1{grid-template-columns:1fr}\n  .opts.c2{grid-template-columns:1fr 1fr}\n  .opts.c3{grid-template-columns:repeat(3,1fr)}\n",
    "  .opts.c1{grid-template-columns:minmax(0,1fr)}\n  .opts.c2{grid-template-columns:repeat(2,minmax(0,1fr))}\n  .opts.c3{grid-template-columns:repeat(3,minmax(0,1fr))}\n")
rep("  body.wide #drill .opts.c2,body.wide #drill .opts.c3{grid-template-columns:1fr}",
    "  body.wide #drill .opts.c2,body.wide #drill .opts.c3{grid-template-columns:minmax(0,1fr)}")
rep("  const cols = longest > 9 ? 1 : (n === 3 ? 3 : 2);",
    "  const cols = longest > 8 ? 1 : (n === 3 ? (longest <= 5 ? 3 : 1) : 2);   // три в ряд — только короткие: 48, 1,3, 6–7-й; два — до 8 знаков")
rep("  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n",
    "  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\n  [hidden]{display:none!important}\n")

CSS = r"""
  /* ——— Справочник: разделы, таблицы, калькуляторы */
  h2.algo-h{line-height:1.35}
  .algo,.lbl{scroll-margin-top:8px}
  .jump{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px}
  .jump button{min-height:44px;padding:0 14px;border-radius:999px;border:1px solid var(--line-2);background:transparent;color:var(--soft);font-size:15px;cursor:pointer}
  .jump button:active{background:var(--raise)}
  .tt,.dz{margin-top:2px}
  .tr,.dr{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:12px;row-gap:2px;padding:10px 0;border-top:1px solid var(--line)}
  .tr:first-child,.dr:first-child{border-top:0}
  .tk,.dk{flex:0 1 auto;min-width:0;overflow-wrap:break-word;font-family:var(--serif);font-size:21px;line-height:1.2;color:var(--accent)}
  .tv{flex:0 1 auto;margin-left:auto;min-width:0;font-family:var(--serif);font-size:20px;line-height:1.2;color:var(--yes-text);text-align:right}
  .dv{flex:0 1 auto;margin-left:auto;min-width:0;font-family:var(--serif);font-size:20px;line-height:1.2;color:var(--text);text-align:right}
  .td,.dd{flex:1 0 100%;margin-top:1px;font-size:14px;line-height:1.45;color:var(--soft)}
  .algo-note + .algo-note{margin-top:6px}

  .calc{margin-top:14px;padding:12px 14px 14px;border-radius:16px;background:var(--bg);border:1px solid var(--line);display:flex;flex-direction:column;gap:6px}
  .calc-h{margin:0 0 2px;font-size:15px;font-weight:600;color:var(--text)}
  .calc-h small{display:block;margin-top:1px;font-size:13px;font-weight:400;color:var(--muted)}
  .fl{margin:6px 0 0;font-size:13px;font-weight:600;letter-spacing:.03em;color:var(--muted)}
  .fl small{margin-left:5px;font-size:12px;font-weight:400;letter-spacing:0}
  .inp{display:block;width:100%;min-height:48px;padding:0 12px;border-radius:12px;border:1px solid var(--line-2);background:var(--surface);color:var(--text);font:inherit;font-size:17px;font-variant-numeric:tabular-nums;-webkit-appearance:none;appearance:none}
  .inp::placeholder{color:var(--muted)}
  .inp:focus{outline:2px solid var(--accent);outline-offset:1px}
  .inp-row{display:grid;grid-template-columns:minmax(0,1fr);gap:6px}
  .inp-row.has-x{grid-template-columns:minmax(0,1fr) 48px}
  .x{min-height:48px;border-radius:12px;border:1px solid var(--line-2);background:transparent;color:var(--muted);font-size:20px;line-height:1;cursor:pointer}
  .seg{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}
  .seg.s3{grid-template-columns:repeat(3,minmax(0,1fr))}
  .seg.s4{grid-template-columns:repeat(auto-fit,minmax(64px,1fr))}
  .seg.s4 .chip{font-size:14px}
  .chip{overflow-wrap:break-word}
  .err s,.err .good{min-width:0;overflow-wrap:break-word}
  .seg.s2{grid-template-columns:repeat(2,minmax(0,1fr))}
  .chip{min-height:44px;padding:0 2px;border-radius:12px;border:1px solid var(--line-2);background:transparent;color:var(--soft);font-size:15px;line-height:1.2;cursor:pointer}
  .chip[aria-pressed="true"]{background:var(--raise);color:var(--text);border-color:var(--accent)}
  .flags{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
  .flags .chip{padding:6px 12px;text-align:left}
  .g2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0 8px}
  .res{margin-top:8px;border-top:1px solid var(--line)}
  .rl{padding:10px 0;border-bottom:1px solid var(--line)}
  .rl:last-child{border-bottom:0;padding-bottom:0}
  .rk{margin:0;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--blue)}
  .rv{margin:2px 0 0;font-family:var(--serif);font-size:22px;line-height:1.25;color:var(--text);text-wrap:balance}
  .rn{margin:3px 0 0;font-size:14px;line-height:1.45;color:var(--muted)}
  .rl.warn .rv{color:var(--no-text)}
  .rl.ok .rv{color:var(--yes-text)}
  .pill{display:inline-block;margin-left:4px;padding:0 9px;border-radius:999px;font-size:12px;font-weight:600;line-height:20px;border:1px solid currentColor;white-space:nowrap;vertical-align:1px}
  .p-now{color:var(--yes-text);background:rgba(78,135,103,.14)}
  .p-wait{color:var(--blue);background:var(--blue-soft)}
  .p-late{color:var(--muted)}
  .crcl{margin:10px 0 0;font-size:15px;color:var(--soft)}
  .crcl b{margin:0 4px;font-family:var(--serif);font-weight:400;font-size:30px;line-height:1;color:var(--text);font-variant-numeric:tabular-nums}
  .dzr{list-style:none;margin:6px 0 0;padding:0}
  .dzr li{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:10px;row-gap:2px;padding:9px 0;border-top:1px solid var(--line)}
  .dzr .n{flex:0 1 auto;min-width:0;font-size:15px;font-weight:600;color:var(--soft)}
  .dzr .d{flex:0 1 auto;margin-left:auto;min-width:0;font-family:var(--serif);font-size:20px;line-height:1.2;color:var(--text);text-align:right}
  .dzr .d.low{color:var(--accent)}
  .dzr .d.no{color:var(--no-text)}
  .dzr .w{flex:1 0 100%;margin-top:0;font-size:13px;line-height:1.4;color:var(--muted)}
  .res-note{margin:8px 0 0;font-size:13px;line-height:1.45;color:var(--muted)}
  .q{overflow-wrap:break-word}
  .t-rule + .t-rule{margin-top:-4px}

  .lst{list-style:none;margin:0;padding:0}
  .lst li{padding:11px 14px 12px;border-top:1px solid var(--line)}
  .lst li:first-child{border-top:0}
  .sw-k{margin:0;font-family:var(--serif);font-size:20px;line-height:1.25;color:var(--accent)}
  .sw-v{margin:3px 0 0;font-size:16px;line-height:1.45;color:var(--text)}
  .sw-s{margin:3px 0 0;font-size:12px;font-weight:600;letter-spacing:.03em;color:var(--muted)}
  .ad-k{margin:0;font-size:14px;font-weight:600;line-height:1.35;color:var(--soft)}
  .ad-v{margin:2px 0 0;font-family:var(--serif);font-size:21px;line-height:1.25;color:var(--accent)}
  .ad-n{margin:3px 0 0;font-size:14px;line-height:1.45;color:var(--muted)}
  .iv-k{margin:0;font-size:14px;font-weight:600;line-height:1.35;color:var(--soft)}
  .iv-k span{font-weight:400;color:var(--muted)}
  .iv-v{margin:3px 0 0;font-family:var(--serif);font-size:19px;line-height:1.3}
  .iv-v::before{content:"";display:inline-block;width:9px;height:9px;margin-right:8px;border-radius:50%;background:currentColor;vertical-align:2px}
  .v-yes{color:var(--yes-text)}
  .v-maybe{color:#e5c07b}
  .v-no{color:var(--no-text)}
  .src{margin:0;padding:0 0 0 22px;font-size:13px;line-height:1.45;color:var(--soft)}
  .src li{margin:0 0 7px;padding-left:2px}
  .src a{color:var(--blue);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:2px;overflow-wrap:anywhere}
  .foot{margin:14px 0 6px;font-size:13px;line-height:1.45;color:var(--muted)}
  .r-title{font-size:min(40px,10vw);overflow-wrap:break-word;hyphens:auto}
  .t-title,.t-sub{overflow-wrap:break-word;hyphens:auto}
  .opt{min-width:0;overflow-wrap:break-word;hyphens:auto}
  label.fl{display:block}
  .fl small{margin-left:0}
  .abbr{margin:0 0 14px;padding:12px 14px 10px;border:1px solid var(--line);border-radius:16px}
  .abbr dl{margin:4px 0 0}
  .abbr dl div{display:grid;grid-template-columns:minmax(0,7.5em) minmax(0,1fr);column-gap:10px;padding:5px 0;border-top:1px solid var(--line)}
  .abbr dl div:first-child{border-top:0}
  .abbr dt{font-size:14px;font-weight:600;line-height:1.4;color:var(--text);overflow-wrap:break-word}
  .abbr dd{margin:0;font-size:14px;line-height:1.4;color:var(--soft);overflow-wrap:break-word}
  .mx-note{font-size:14px;color:var(--muted)}
"""
rep("  /* ——— Планшет */\n", CSS + "\n  /* ——— Планшет */\n")
rep("  body.wide #rule{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);column-gap:36px;align-items:start}",
    "  body.wide #rule{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:36px;align-items:start}")

# ——— вкладки
rep('aria-controls="rule">Правила</button>', 'aria-controls="rule">Справочник</button>')
rep('<button class="big" id="toRule" type="button">Правила</button>', '<button class="big" id="toRule" type="button">Справочник</button>')

# ——— без озвучки: блок записей и синтеза речи заменяю пустой остановкой
a = s.index("// ——— Озвучка:"); b = s.index("// ——— Очередь")
s = s[:a] + "function stopAudio(){}   // озвучки в этом приложении нет\n\n" + s[b:]
assert "speechSynthesis" not in s and "playClip" not in s

# ——— вкладка «Справочник»
a = s.index('    <div class="r-left">'); b = s.index('  </section>\n</div>')
s = s[:a] + '''    <div class="r-left">
      <h1 class="r-title">Ранняя антикоагуляция</h1>
      <p class="r-sub">ПОАК и&nbsp;варфарин после ишемического инсульта при&nbsp;ФП: когда начинать, в&nbsp;какой дозе, как переходить с&nbsp;препарата на&nbsp;препарат и&nbsp;чем нейтрализовать. Сроки&nbsp;— по&nbsp;<b>ELAN</b>; в&nbsp;мета‑анализе <b>CATALYST</b> старт в&nbsp;первые 4&nbsp;дня снизил риск повторного инсульта без прибавки кровоизлияний.</p>
      <section class="abbr" aria-labelledby="h-abbr">
        <h2 class="algo-h" id="h-abbr">Сокращения</h2>
        <dl>
          <div><dt>КПК</dt><dd>концентрат протромбинового комплекса: факторы свёртывания II, VII, IX и&nbsp;X (например, Протромплекс&nbsp;600)</dd></div>
          <div><dt>аКПК</dt><dd>активированный КПК</dd></div>
          <div><dt>сВЧК</dt><dd>симптомное внутричерепное кровоизлияние</dd></div>
          <div><dt>ГТ</dt><dd>геморрагическая трансформация: HI&nbsp;— геморрагический инфаркт, PH&nbsp;— паренхиматозная гематома</dd></div>
          <div><dt>КК</dt><dd>клиренс креатинина по&nbsp;Кокрофту–Голту</dd></div>
          <div><dt>КР по&nbsp;ИИ&nbsp;2024</dt><dd>клинические рекомендации «Ишемический инсульт и&nbsp;транзиторная ишемическая атака»</dd></div>
          <div><dt>КР по&nbsp;ФП&nbsp;2025</dt><dd>клинические рекомендации «Фибрилляция и&nbsp;трепетание предсердий»</dd></div>
        </dl>
      </section>
      <nav class="jump" aria-label="Разделы справочника">
        <button type="button" data-to="s-when">Сроки</button>
        <button type="button" data-to="s-dose">Дозы</button>
        <button type="button" data-to="s-switch">Переходы</button>
        <button type="button" data-to="s-anti">Антидоты</button>
        <button type="button" data-to="s-ivt">Тромболизис</button>
        <button type="button" data-to="s-topics">Темы</button>
      </nav>
      <section class="algo" id="s-when" aria-labelledby="h-when">
        <h2 class="algo-h" id="h-when">Когда начинать</h2>
        <div class="tt">
<!--__TIMING__-->
        </div>
        <p class="algo-note">Малый, средний и&nbsp;большой&nbsp;— по&nbsp;ELAN. Отсчёт&nbsp;— от&nbsp;начала симптомов. После тромболизиса&nbsp;— не&nbsp;раньше 24&nbsp;ч и&nbsp;после контрольной КТ/МРТ. Россыпь мелких очагов&nbsp;— малый инсульт, два малых&nbsp;— средний, два средних&nbsp;— большой.</p>
        <p class="algo-note"><b>Кровоизлияние.</b> HI1–HI2 без ухудшения&nbsp;— по&nbsp;схеме (ELAN, КР по&nbsp;ФП&nbsp;2025; КР по&nbsp;ИИ&nbsp;2024 без отсрочки допускают только ГТ 1‑го типа). PH1–PH2&nbsp;— срок индивидуально, КТ в&nbsp;динамике; КР по&nbsp;ИИ&nbsp;2024&nbsp;— через 4–8&nbsp;недель.</p>
        <p class="algo-note"><b>КР по&nbsp;ИИ&nbsp;2024.</b> Низкий риск геморрагической трансформации&nbsp;— старт на&nbsp;3–14‑е&nbsp;сутки; большой инфаркт (<span class="nw">NIHSS&nbsp;&gt;&nbsp;15</span> или весь бассейн)&nbsp;— через 14&nbsp;дней. Схема из&nbsp;комментария: ТИА&nbsp;— в&nbsp;течение суток; <span class="nw">NIHSS&nbsp;&lt;&nbsp;8</span>&nbsp;— через 3&nbsp;дня; 8–16&nbsp;— через 6–8&nbsp;дней; <span class="nw">&gt;&nbsp;16</span>&nbsp;— через 12–14&nbsp;дней, перед стартом КТ/МРТ.</p>
        <p class="algo-note"><b>До&nbsp;старта ПОАК.</b> АСК (КР по&nbsp;ИИ&nbsp;2024, УУР&nbsp;C; в&nbsp;их алгоритме&nbsp;— АСК или клопидогрел). Лечебный гепарин «мостом» не&nbsp;назначают (КР по&nbsp;ФП&nbsp;2025, ЕОК&nbsp;IIIB); профилактические дозы НМГ или НФГ у&nbsp;обездвиженных&nbsp;— можно (КР по&nbsp;ИИ&nbsp;2024, УУР&nbsp;A).</p>
        <p class="algo-note"><b>Почему по&nbsp;ELAN.</b> КР по&nbsp;ФП&nbsp;2025 уже ссылаются на&nbsp;ELAN, TIMING, START и&nbsp;OPTIMAS и&nbsp;советуют решать индивидуально; ESO&nbsp;2025 и&nbsp;AHA/ASA&nbsp;2026 поддерживают ранний старт.</p>
        <div class="calc" id="tcalc">
          <p class="calc-h">Посчитать даты<small>Пример&nbsp;— укажите время пациента</small></p>
          <label class="fl" for="onset">Начало симптомов<small>или когда видели здоровым</small></label>
          <input class="inp" id="onset" type="datetime-local">
          <p class="fl" id="sizeLbl">Размер инфаркта по КТ/МРТ</p>
          <div class="seg s4" role="group" aria-labelledby="sizeLbl">
            <button type="button" class="chip" data-size="tia" aria-pressed="false">ТИА</button>
            <button type="button" class="chip" data-size="minor" aria-pressed="true">Малый</button>
            <button type="button" class="chip" data-size="moderate" aria-pressed="false">Средний</button>
            <button type="button" class="chip" data-size="major" aria-pressed="false">Большой</button>
          </div>
          <p class="fl" id="htLbl">Геморрагическая трансформация</p>
          <div class="seg s3" role="group" aria-labelledby="htLbl">
            <button type="button" class="chip" data-ht="none" aria-pressed="true">Нет</button>
            <button type="button" class="chip" data-ht="hi" aria-pressed="false">HI1–HI2</button>
            <button type="button" class="chip" data-ht="ph" aria-pressed="false">PH1–PH2</button>
          </div>
          <label class="fl" for="nihss">NIHSS<small>для схемы КР по&nbsp;ИИ&nbsp;2024</small></label>
          <input class="inp" id="nihss" type="number" inputmode="numeric" min="0" max="42" step="1" placeholder="не указан">
          <label class="fl" for="ivt">Тромболизис<small>время, если был</small></label>
          <div class="inp-row">
            <input class="inp" id="ivt" type="datetime-local">
            <button type="button" class="x" id="ivtClear" aria-label="Тромболизиса не было" hidden>×</button>
          </div>
          <div class="res" id="tres" aria-live="polite"></div>
        </div>
      </section>
      <section class="algo algo-2" id="s-dose" aria-labelledby="h-dose">
        <h2 class="algo-h" id="h-dose">Дозы ПОАК</h2>
        <div class="dz">
<!--__DOSES__-->
        </div>
        <p class="algo-note">КК&nbsp;— по&nbsp;Кокрофту–Голту. Сниженная доза без критериев хуже защищает от&nbsp;инсульта.</p>
        <div class="calc" id="dcalc">
          <p class="calc-h">Подобрать дозу<small>Пример&nbsp;— замените данными пациента</small></p>
          <div class="g2">
            <div><label class="fl" for="age">Возраст, лет</label><input class="inp" id="age" type="number" inputmode="numeric" min="18" max="110" step="1" value="78"></div>
            <div><label class="fl" for="wt">Масса, кг</label><input class="inp" id="wt" type="number" inputmode="decimal" min="30" max="250" step="0.1" value="62"></div>
            <div><label class="fl" for="cr">Креатинин<small>мкмоль/л</small></label><input class="inp" id="cr" type="number" inputmode="decimal" min="20" max="2000" step="1" value="105"></div>
            <div><p class="fl" id="sexLbl">Пол</p><div class="seg s2" role="group" aria-labelledby="sexLbl"><button type="button" class="chip" data-sex="f" aria-pressed="true">Жен</button><button type="button" class="chip" data-sex="m" aria-pressed="false">Муж</button></div></div>
          </div>
          <div class="flags" role="group" aria-label="Что ещё учесть">
            <button type="button" class="chip" data-flag="verap" aria-pressed="false">Верапамил</button>
            <button type="button" class="chip" data-flag="pgp" aria-pressed="false">Циклоспорин, эритромицин или кетоконазол</button>
            <button type="button" class="chip" data-flag="gi" aria-pressed="false">Высокий риск ЖКК</button>
          </div>
          <div class="res" id="dres" aria-live="polite"></div>
        </div>
      </section>
      <div class="go-wrap"><button class="big primary" id="go" type="button">Начать тренировку</button></div>
    </div>
    <div class="r-right">
      <h2 class="lbl" id="s-switch">Переходы</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__SWITCH__-->
        </ul>
      </div>
      <h2 class="lbl" id="s-anti">Антидоты</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__ANTIDOTES__-->
        </ul>
      </div>
      <h2 class="lbl" id="s-ivt">Тромболизис на&nbsp;антикоагулянте</h2>
      <div class="mx-wrap">
        <ul class="lst">
<!--__IVT__-->
        </ul>
      </div>
      <p class="mx-note">КР по&nbsp;ИИ&nbsp;2024 требуют определить МНО у&nbsp;принимающих варфарин, но&nbsp;порога не&nbsp;называют; <span class="nw">МНО&nbsp;&gt;&nbsp;1,3</span>&nbsp;— противопоказание в&nbsp;инструкциях алтеплазы и&nbsp;неиммуногенной стафилокиназы. КР по&nbsp;ФП&nbsp;2025 формально не&nbsp;рекомендуют тромболизис на&nbsp;фоне антикоагулянта (ЕОК&nbsp;IIIC), но&nbsp;допускают его при&nbsp;<span class="nw">МНО&nbsp;≤&nbsp;1,7</span> (выше порога инструкций), приёме ПОАК больше 48&nbsp;ч назад при&nbsp;сохранной функции почек или если препарат не&nbsp;определяется.</p>
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
      <p class="foot">Сверено 5&nbsp;октября 2026&nbsp;г. Справочник для&nbsp;врача: решение принимают по&nbsp;клинической ситуации и&nbsp;протоколу отделения.</p>
    </div>
''' + s[b:]

rep('const LS_STATE = "ctp:state";\nconst LS_SPEAK = "ctp:autospeak";\nconst LS_TAB = "ctp:tab";\nconst LS_OPEN = "ctp:open";',
    'const LS_STATE = "oac:state";\nconst LS_TAB = "oac:tab";\nconst LS_OPEN = "oac:open";')
rep('["apple-mobile-web-app-title", "Перфузия"],', '["apple-mobile-web-app-title", "ПОАК"],')
rep("// Новые карточки идут вперемешку по темам: метод, карты, ядро и пенумбра, коллатерали, отбор, ловушки и отчёт чередуются.",
    "// Новые карточки идут вперемешку по темам: доказательства, размер, сроки, дозы, варфарин, переходы и антидоты чередуются.")

CALC = r"""
// ——— Переход к разделам справочника
document.querySelectorAll(".jump button").forEach(b => b.addEventListener("click", () => {
  const t = document.getElementById(b.dataset.to);
  if (!t) return;
  const smooth = !(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  try{ t.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" }); }catch(e){ t.scrollIntoView(); }
}));

// ——— Калькулятор дат старта (ELAN, OPTIMAS/CATALYST, КР по ИИ 2024)
const NB = " ";
const HOUR = 3600000;
const calc = { size: "minor", ht: "none", sex: "f", verap: false, pgp: false, gi: false };
const fmtD = new Intl.DateTimeFormat("ru-RU", { weekday: "short", day: "numeric", month: "long" });
const fmtDM = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long" });
function pad2(n){ return String(n).padStart(2, "0"); }
function toInput(d){ return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate()) + "T" + pad2(d.getHours()) + ":" + pad2(d.getMinutes()); }
function fromInput(v){
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(v || "");
  return m ? new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]) : null;
}
function hm(d){ return pad2(d.getHours()) + ":" + pad2(d.getMinutes()); }
function whenT(d){ return fmtD.format(d) + ", " + hm(d); }
function dayOf(onset, n){ return new Date(onset.getFullYear(), onset.getMonth(), onset.getDate() + n); }
function dayEnd(d){ return new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1); }
function span(a, b){
  const x = fmtDM.format(a), y = fmtDM.format(b);
  if (a.getMonth() === b.getMonth()) return a.getDate() + "–" + y;
  return x + " – " + y;
}
// неразрывные пробелы и тире в строках калькуляторов: «75–80 лет», «КК 30–50», «3–4 октября» не рвутся
function tp(s){
  return String(s)
    .replace(/(\d)–(\d)/g, "$1–\u2060$2")
    .replace(/(\d) (?=(?:мг|мл|мин|лет|ч(?![а-яё])|дн|сут|кг|мкмоль|недел|янв|фев|мар|апр|ма[яй]|июн|июл|авг|сен|окт|ноя|дек))/g, "$1\u00a0")
    .replace(/ ([×<>≤≥=+]) /g, "\u00a0$1\u00a0")
    .replace(/(КК|NIHSS|МНО|ОШ|день) (?=[\d<>≤≥=])/g, "$1\u00a0")
    .replace(/(^|[\s(«])(не|в|с|к|и|а|о|у|на|по|за|из|от|до|со|но|же|ли|при|без|для) /g, "$1$2\u00a0")
    .replace(/ — /g, "\u00a0— ");
}
function pill(now, from, to){
  if (now < from) return ["ещё рано", "p-wait"];
  if (to && now >= to) return ["срок прошёл", "p-late"];
  return ["сейчас", "p-now"];
}
function line(k, v, n, cls, p){
  const box = el("div", "rl" + (cls ? " " + cls : ""));
  box.append(el("p", "rk", tp(k)));
  const vv = el("p", "rv", tp(v));
  box.append(vv);
  if (n || p){
    const nn = el("p", "rn", tp(n || ""));
    if (p) nn.append(n ? " " : "", el("span", "pill " + p[1], p[0]));
    box.append(nn);
  }
  return box;
}
function ago(ms){
  const h = Math.floor(ms / HOUR);
  if (h < 1) return "меньше часа";
  if (h < 48) return h + NB + "ч";
  return Math.floor(h / 24) + NB + "сут " + (h % 24) + NB + "ч";
}
function renderTiming(){
  const box = $("tres");
  box.textContent = "";
  const onset = fromInput($("onset").value);
  if (!onset){ box.append(line("Даты", "Укажите начало симптомов", "")); return; }
  const now = new Date();
  if (onset - now > 5 * 60000){ box.append(line("Даты", "Время начала позже текущего", "Проверьте дату и время.", "warn")); return; }
  const ivt = fromInput($("ivt").value);
  $("ivtClear").hidden = !$("ivt").value;
  $("ivt").parentElement.classList.toggle("has-x", !!$("ivt").value);
  const after = ivt && ivt >= onset ? new Date(ivt.getTime() + 24 * HOUR) : null;
  const size = calc.size, ht = calc.ht;
  const nihssRaw = $("nihss").value.trim();
  const nihss = nihssRaw === "" ? null : Number(nihssRaw);

  // ELAN
  if (ht === "ph"){
    const w4 = dayOf(onset, 28), w8 = dayOf(onset, 56);
    box.append(line("Гематома PH1–PH2", "Срок индивидуально, КТ в динамике",
      "Протокол ELAN PH исключал; у 56 включённых её всё же нашли — у них ранний старт мог ухудшать исход. КР по ИИ 2024: 4–8 недель — " + span(w4, w8) + ".", "warn"));
  } else if (size === "tia"){
    const end = new Date(onset.getTime() + 24 * HOUR);
    box.append(line("ТИА · КР по ИИ 2024", "до " + whenT(end), "в первые сутки, после КТ/МРТ без кровоизлияния; в алгоритме КР по ИИ 2024 — «ПОАК сразу же»; КР по ФП 2025: при остром очаге — через 1–3 суток", "", pill(now, onset, end)));
  } else if (size === "major"){
    const d6 = dayOf(onset, 6), d7 = dayOf(onset, 7);
    box.append(line("ELAN · большой инфаркт", "6–7-й день: " + span(d6, d7), "день 6 = дата начала + 6 суток", "", pill(now, d6, dayEnd(d7))));
  } else {
    const end = new Date(onset.getTime() + 48 * HOUR);
    const from = after && after > onset ? after : onset;
    if (after && after >= end){
      box.append(line("ELAN · " + (size === "minor" ? "малый" : "средний") + " инфаркт", "после " + whenT(after),
        "48 ч закончатся раньше, чем пройдут 24 ч после тромболизиса: старт — после контрольной КТ/МРТ", "", pill(now, after, null)));
    } else {
      box.append(line("ELAN · " + (size === "minor" ? "малый" : "средний") + " инфаркт", "до " + whenT(end),
        after ? "не раньше " + whenT(after) + " — 24 ч после тромболизиса и контрольная КТ/МРТ" : "первые 48 ч от начала симптомов", "", pill(now, from, end)));
    }
  }
  if (ht === "hi" && size !== "tia") box.append(line("HI1–HI2", "Без ухудшения — по схеме", "ELAN и КР по ФП 2025. КР по ИИ 2024 без отсрочки допускают только ГТ 1-го типа.", "ok"));

  // OPTIMAS · CATALYST: первые 4 суток при любом размере
  if (size !== "tia" && ht !== "ph"){
    const end4 = new Date(onset.getTime() + 96 * HOUR);
    const from4 = after && after > onset ? after : onset;
    box.append(line("OPTIMAS · CATALYST", "до " + whenT(end4), "первые 4 суток; в OPTIMAS эффект не зависел от объёма инфаркта (инфарктов > 50 мл — 187)", "", pill(now, from4, end4)));
  }

  // КР по ИИ 2024: формальная рекомендация при высоком риске ГТ — 14 дней
  if (size !== "tia" && ht !== "ph" && (size === "major" || (nihss !== null && nihss > 15 && nihss <= 42))){
    const d14 = dayOf(onset, 14);
    box.append(line("КР по ИИ 2024 · высокий риск ГТ", "через 14 дней: " + fmtD.format(d14), "большой инфаркт: NIHSS > 15 или весь бассейн артерии", "", pill(now, d14, null)));
  }
  // КР по ИИ 2024: схема по NIHSS из комментария (при гематоме не применяется)
  if (size === "tia" || ht === "ph"){
    // для ТИА КР по ИИ 2024 уже показаны выше, при PH — 4–8 недель
  } else if (nihss === null || !isFinite(nihss) || nihss < 0 || nihss > 42){
    box.append(line("КР по ИИ 2024 · схема по NIHSS", nihss === null ? "Введите NIHSS" : "NIHSS — от 0 до 42", "< 8 — через 3 дня · 8–16 — через 6–8 дней · > 16 — через 12–14 дней"));
  } else if (nihss < 8){
    const d3 = dayOf(onset, 3);
    box.append(line("КР по ИИ 2024 · схема, NIHSS " + nihss, "через 3 дня: " + fmtD.format(d3), "лёгкий инсульт", "", pill(now, d3, null)));
  } else if (nihss <= 16){
    const a6 = dayOf(onset, 6), a8 = dayOf(onset, 8);
    box.append(line("КР по ИИ 2024 · схема, NIHSS " + nihss, "6–8 дней: " + span(a6, a8), "средний инсульт; перед стартом КТ/МРТ", "", pill(now, a6, dayEnd(a8))));
  } else {
    const a12 = dayOf(onset, 12), a14 = dayOf(onset, 14);
    box.append(line("КР по ИИ 2024 · схема, NIHSS " + nihss, "12–14 дней: " + span(a12, a14), "тяжёлый инсульт; перед стартом КТ/МРТ", "", pill(now, a12, dayEnd(a14))));
  }
  box.append(el("p", "res-note", tp("Прошло от начала: " + ago(now - onset) + ".")));
}

// ——— Калькулятор дозы: КК по Кокрофту–Голту и дозы ПОАК по КР по ФП 2025
function num(id){ const v = String($(id).value).replace(",", ".").trim(); return v === "" ? NaN : Number(v); }
function doseRow(name, dose, cls, why){
  const li = el("li");
  li.append(el("span", "n", tp(name)), el("span", "d" + (cls ? " " + cls : ""), tp(dose)));
  if (why) li.append(el("span", "w", tp(why)));
  return li;
}
function joinRu(a){ return a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " и " + a[a.length - 1]; }
function renderDose(){
  const box = $("dres");
  box.textContent = "";
  const age = num("age"), kg = num("wt"), cr = num("cr");
  if (!(age >= 18 && age <= 110) || !(kg >= 30 && kg <= 250) || !(cr >= 20 && cr <= 2000)){
    box.append(el("p", "res-note", "Введите возраст (18–110 лет), массу (30–250 кг) и креатинин (20–2000 мкмоль/л)."));
    return;
  }
  const male = calc.sex === "m";
  const cl = Math.round((140 - age) * kg * (male ? 1.23 : 1.04) / cr);
  const p = el("p", "crcl");
  p.append("КК", el("b", null, String(Math.max(cl, 0))), "мл/мин · Кокрофт–Голт");
  box.append(p);
  const ul = el("ul", "dzr");

  // апиксабан
  const apiSigns = [];
  if (age >= 80) apiSigns.push("80 лет и старше");
  if (kg <= 60) apiSigns.push("масса ≤ 60 кг");
  if (cr >= 133) apiSigns.push("креатинин ≥ 133");
  if (cl < 15) ul.append(doseRow("Апиксабан", "не применять", "no", "КК < 15"));
  else if (cl < 30) ul.append(doseRow("Апиксабан", "2,5 мг × 2", "low", "КК 15–29"));
  else if (apiSigns.length >= 2) ul.append(doseRow("Апиксабан", "2,5 мг × 2", "low", "признаки: " + joinRu(apiSigns)));
  else ul.append(doseRow("Апиксабан", "5 мг × 2", "", apiSigns.length ? "признак один (" + apiSigns[0] + ") — доза полная" : "признаков для снижения нет"));

  // дабигатран
  if (cl < 30) ul.append(doseRow("Дабигатран", "противопоказан", "no", "КК < 30"));
  else {
    const must = [];
    if (age >= 80) must.push("80 лет и старше");
    if (calc.verap) must.push("верапамил");
    const may = [];
    if (age >= 75 && age < 80) may.push("75–80 лет");
    if (cl <= 50) may.push("КК 30–50");
    if (calc.gi) may.push("риск ЖКК");
    if (must.length) ul.append(doseRow("Дабигатран", "110 мг × 2", "low", joinRu(must)));
    else if (may.length) ul.append(doseRow("Дабигатран", "150 мг × 2", "", "или 110 мг × 2 — на усмотрение врача: " + joinRu(may)));
    else ul.append(doseRow("Дабигатран", "150 мг × 2", "", "критериев для снижения нет"));
  }

  // ривароксабан
  if (cl < 15) ul.append(doseRow("Ривароксабан", "не применять", "no", "КК < 15"));
  else if (cl < 50) ul.append(doseRow("Ривароксабан", "15 мг × 1", "low", "КК 15–49 · во время еды"));
  else ul.append(doseRow("Ривароксабан", "20 мг × 1", "", "во время еды"));

  // эдоксабан
  if (cl < 15) ul.append(doseRow("Эдоксабан", "не применять", "no", "КК < 15"));
  else {
    const e = [];
    if (cl < 50) e.push("КК 15–49");
    if (kg <= 60) e.push("масса ≤ 60 кг");
    if (calc.pgp) e.push("ингибитор P-gp");
    const hi = cl > 95 ? "КК > 95: эффективность эдоксабана ниже" : "";
    if (e.length) ul.append(doseRow("Эдоксабан", "30 мг × 1", "low", joinRu(e) + (hi ? " · " + hi : "")));
    else ul.append(doseRow("Эдоксабан", "60 мг × 1", "", hi || "критериев для снижения нет"));
  }

  // варфарин
  ul.append(doseRow("Варфарин", "МНО 2,0–3,0", "", cl < 15 ? "при КК < 15 — единственный ОАК, одобренный в РФ" : "если ПОАК противопоказаны"));
  box.append(ul);
  if (calc.pgp) box.append(el("p", "res-note", tp("Эти препараты важны и для остальных ПОАК: с кетоконазолом и циклоспорином дабигатран противопоказан — сверьтесь с инструкцией.")));
  box.append(el("p", "res-note", tp("Масса — фактическая. Креатинин в мг/дл × 88,4 = мкмоль/л.")));
}

function pressOne(sel, attr, val){
  document.querySelectorAll(sel).forEach(b => b.setAttribute("aria-pressed", String(b.dataset[attr] === val)));
}
function initCalc(){
  const d = new Date(Date.now() - 6 * HOUR);
  d.setMinutes(Math.floor(d.getMinutes() / 5) * 5, 0, 0);
  $("onset").value = toInput(d);
  document.querySelectorAll("[data-size]").forEach(b => b.addEventListener("click", () => { calc.size = b.dataset.size; pressOne("[data-size]", "size", calc.size); renderTiming(); }));
  document.querySelectorAll("[data-ht]").forEach(b => b.addEventListener("click", () => { calc.ht = b.dataset.ht; pressOne("[data-ht]", "ht", calc.ht); renderTiming(); }));
  ["onset", "ivt", "nihss"].forEach(id => { $(id).addEventListener("input", renderTiming); $(id).addEventListener("change", renderTiming); });
  $("ivtClear").addEventListener("click", () => { $("ivt").value = ""; renderTiming(); });
  document.querySelectorAll("[data-sex]").forEach(b => b.addEventListener("click", () => { calc.sex = b.dataset.sex; pressOne("[data-sex]", "sex", calc.sex); renderDose(); }));
  document.querySelectorAll("[data-flag]").forEach(b => b.addEventListener("click", () => {
    const k = b.dataset.flag; calc[k] = !calc[k]; b.setAttribute("aria-pressed", String(calc[k])); renderDose();
  }));
  ["age", "wt", "cr"].forEach(id => { $(id).addEventListener("input", renderDose); $(id).addEventListener("change", renderDose); });
  renderTiming();
  renderDose();
  setInterval(() => { if (!$("rule").hidden) renderTiming(); }, 60000);
}
"""
rep("function boot(){\n", CALC + "\nfunction boot(){\n")
rep('      const rule = el("p", "t-rule"); rule.append(richText(t.rule)); body.append(rule);',
    '      String(t.rule).split("\\n\\n").forEach(par => { const rule = el("p", "t-rule"); rule.append(richText(par)); body.append(rule); });')
rep("  connectCloud();\n}\nboot();", "  initCalc();\n  connectCloud();\n}\nboot();")
assert "ctp:" not in s and "Перфузия" not in s and "КТ-перфузия" not in s
import re
s, _n = re.subn(r'(<(?:label|p) class="fl"[^>]*>[^<]*?)<small>', r'\1 <small>', s)   # «Креатинин мкмоль/л» переносится
assert _n == 4, _n
pathlib.Path("oac/template.html").write_text(s)
print("ok", len(s))
