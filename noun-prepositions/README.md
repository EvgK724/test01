# Noun + preposition — существительные с предлогами

Веб-приложение для iPhone и iPad по листу с группами:

| at | for | in | into | of | to |
|---|---|---|---|---|---|
| age, attempt, point | need, reason, responsibility | changes, increase, differences | enquiry, investigation, research | cause, example, way, knowledge | approach, reaction, response |

- **Правило** — лист «существительные ) предлог» с логикой каждой группы, алгоритм выбора,
  примеры с контрастными парами (reason for / cause of, increase in / increase of, changes in / changes to), мнемоника.
- **Карточки** — 19 сочетаний, интервальное повторение (1 → 3 → 7 → 16 дней), свайпы, озвучка.
- **Тренировка** — 32 задания: собрать фразу из слов с лишними предлогами и быстрый выбор предлога.
- **Тест** — 10 заданий, ключ с объяснениями в конце.

Ссылка (GitHub Pages): https://evgk724.github.io/test01/noun-prepositions/

Поставить на экран «Домой»: открыть ссылку в Safari → «Поделиться» → «На экран „Домой“».

## Голос Microsoft Ryan

Записи (`audio/`) делает GitHub Actions (`.github/workflows/ryan-audio.yml`) после изменения `index.html`.
Локально: `node tools/extract_phrases.mjs`, затем `pip install edge-tts` и `python tools/make_audio.py`.

## Файлы

- `index.html` — всё приложение; слова, группы, примеры и задания — блок `DATA-START … DATA-END`.
- `tools/` — сбор фраз и генерация записей Ryan.
- `manifest.webmanifest`, `apple-touch-icon.png`, `icon-*.png`, `sw.js` — иконка, режим приложения, офлайн-кэш.
