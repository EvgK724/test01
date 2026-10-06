# Шаблон «КТ-перфузия» собираю из шаблона «remember»: тренажёр тот же, но на русском и без озвучки.
# Вкладка правил: четыре карты (таблица), ядро/пенумбра/олигемия (таблица), как читать карту (шаги),
# справа — одна картина с разным смыслом, ловушки, темы.
import pathlib
s = pathlib.Path("vm/template.html").read_text()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:70], s.count(a))
    s = s.replace(a, b)

rep("<title>remember</title>", "<title>КТ-перфузия</title>")
rep("  .vt.sv col.v{width:40%}\n",
    "  .vt.sv col.v{width:40%}\n"
    "  .q{font-size:26px}\n"
    "  .md{grid-template-columns:minmax(0,1fr)}\n"
    "  .ex{grid-template-columns:minmax(0,1fr)}\n"
    "  .mt.cp col.rh{width:64px}\n"
    "  .mt.cp thead th{padding:2px 4px 8px;font-size:13px;letter-spacing:0;text-transform:none}\n"
    "  .mt.cp tbody th{font-size:20px}\n"
    "  .mt.cp td{padding:12px 4px}\n"
    "  .mt.cp td .f{font-size:20px}\n"
    "  .mt.cp .c-core{color:var(--accent)}\n"
    "  .mt.cp .c-pen{color:var(--yes-text)}\n"
    "  .mt.cp .c-olig{color:var(--blue)}\n"
    "  .algo-note b{color:var(--text);font-weight:600}\n")

# ——— без озвучки: убираю кнопки звука и записи
a = s.index('    <button class="icon" id="sound"'); b = s.index('    </button>\n', a) + len('    </button>\n')
s = s[:a] + s[b:]
a = s.index('      <button class="say" id="say"'); b = s.index('      </button>\n', a) + len('      </button>\n')
s = s[:a] + s[b:]
rep('<p class="q" id="q" lang="en"></p>', '<p class="q" id="q"></p>')
rep('      b.lang = "en";\n', '      if (!/[а-яё]/i.test(o)) b.lang = "en";\n')
rep('  preloadClip(card.id);\n', '')
rep('  if (autoSpeak) playClip(card.id, fullText(card));\n', '')
rep('let autoSpeak = true;', 'let autoSpeak = false;   // озвучки в этом приложении нет')
rep('''        const en = el("p", "ex-en"); en.lang = "en"; en.append(marked(ex.en));
        const play = el("button", "ex-play");
        play.type = "button";
        play.setAttribute("aria-label", "Прослушать пример");
        play.innerHTML = PLAY_SVG;
        play.addEventListener("click", () => playClip("r" + t.n + "-" + (i + 1), exText(ex.en), 0.9));
        row.append(en, play, el("p", "ex-ru", ex.ru));''',
    '''        const en = el("p", "ex-en"); en.append(marked(ex.en));
        row.append(en, el("p", "ex-ru", ex.ru));''')
rep('''$("say").addEventListener("click", () => {
  const c = queue[index];
  if (c) playClip(c.id, fullText(c));
});
$("sound").addEventListener("click", () => {
  autoSpeak = !autoSpeak;
  $("sound").setAttribute("aria-pressed", String(autoSpeak));
  lsSet(LS_SPEAK, autoSpeak ? "1" : "0");
  if (!autoSpeak) stopAudio();
});
''', '')
rep('''  const s = lsGet(LS_SPEAK);
  if (s !== null) autoSpeak = s === "1";
  $("sound").setAttribute("aria-pressed", String(autoSpeak));
''', '')

def step(n, title, formula):
    return f'          <li><span class="sn">{n}</span><div><p class="s-t">{title}</p><p class="s-f">{formula}</p></div></li>\n'
P = lambda t: f'<span class="pr">{t.replace(" ", "&nbsp;")}</span>'
D = ' <span class="sep">·</span> '
nw = lambda t: f'<span class="nw">{t}</span>'
steps = (step(1, "Проверь качество", "движение" + D + nw("кривые AIF и VOF"))
         + step(2, "Очерти зону риска", nw(P("Tmax > 6 с")) + D + "объём и&nbsp;бассейн")
         + step(3, "Найди ядро", nw(P("rCBF < 30%")) + D + "объём")
         + step(4, "Посчитай mismatch", "пенумбра&nbsp;— разница" + D + nw("ratio&nbsp;— отношение"))
         + step(5, "Сверь", "КТ, КТА, NIHSS, время"))

a = s.index('    <div class="r-left">'); b = s.index('  </section>\n</div>')
s = s[:a] + '''    <div class="r-left">
      <h1 class="r-title">КТ-перфузия</h1>
      <p class="r-sub">За&nbsp;1–1,5 минуты после болюса контраста КТ‑перфузия показывает, как кровь проходит через мозг. Главная задача&nbsp;— отличить <b>ядро</b> (ткань уже погибла) от&nbsp;<b>пенумбры</b> (ткань страдает, но&nbsp;её можно спасти) и&nbsp;понять, есть&nbsp;ли что спасать.</p>
      <div class="algo">
        <p class="algo-h">Четыре карты</p>
        <table class="vt sv">
          <colgroup><col class="v"><col></colgroup>
          <tbody>
<!--__MAPS__-->
          </tbody>
        </table>
        <p class="algo-note">CBF, CBV и&nbsp;MTT связаны формулой <b>CBF&nbsp;=&nbsp;CBV&nbsp;/&nbsp;MTT</b>. Абсолютные цифры у&nbsp;программ разные&nbsp;— сравнивают больную сторону со&nbsp;здоровой.</p>
      </div>
      <div class="algo algo-2">
        <p class="algo-h">Ядро, пенумбра, олигемия</p>
        <table class="mt cp">
          <colgroup><col class="rh"><col><col><col></colgroup>
          <thead><tr><td></td><th scope="col" class="c-core">Ядро</th><th scope="col" class="c-pen">Пенумбра</th><th scope="col" class="c-olig">Олигемия</th></tr></thead>
          <tbody>
<!--__TISSUE__-->
          </tbody>
        </table>
        <p class="algo-m"><b class="pr">Ядро</b>&nbsp;— крови нет. <b class="good">Пенумбра</b>&nbsp;— кровь опаздывает.</p>
        <p class="algo-note">Пороги&nbsp;— как в&nbsp;RAPID: ядро <b>rCBF&nbsp;&lt;&nbsp;30%</b>, вся гипоперфузия <b>Tmax&nbsp;&gt;&nbsp;6&nbsp;с</b>. У&nbsp;других программ пороги свои.</p>
      </div>
      <div class="algo algo-2">
        <p class="algo-h">Как читать карту</p>
        <ol class="steps">
''' + steps + '''        </ol>
      </div>
      <div class="go-wrap"><button class="big primary" id="go" type="button">Начать тренировку</button></div>
    </div>
    <div class="r-right">
      <h2 class="lbl">Одна картина&nbsp;— разный смысл</h2>
      <div class="mx-wrap">
<!--__CONTRAST__-->
      </div>
      <h2 class="lbl">Ловушки</h2>
      <div class="mx-wrap">
        <ul class="errs">
<!--__ERRORS__-->
        </ul>
      </div>
      <h2 class="lbl">Темы</h2>
      <div class="topics" id="topics"></div>
    </div>
''' + s[b:]

rep('const LS_STATE = "vm:state";\nconst LS_SPEAK = "vm:autospeak";\nconst LS_TAB = "vm:tab";\nconst LS_OPEN = "vm:open";',
    'const LS_STATE = "ctp:state";\nconst LS_SPEAK = "ctp:autospeak";\nconst LS_TAB = "ctp:tab";\nconst LS_OPEN = "ctp:open";')
rep('["apple-mobile-web-app-title", "remember"],', '["apple-mobile-web-app-title", "Перфузия"],')
rep("// Новые карточки идут вперемешку по темам: remember, forget, regret, try, stop, go on, need, see и afraid чередуются.",
    "// Новые карточки идут вперемешку по темам: метод, карты, ядро и пенумбра, коллатерали, отбор, ловушки и отчёт чередуются.")
assert "vm:state" not in s and 'id="sound"' not in s and 'id="say"' not in s and '$("sound")' not in s and '$("say")' not in s
pathlib.Path("ctp/template.html").write_text(s)
print("ok", len(s))
