#!/usr/bin/env python3
"""Ответы Google Формы → пожелания на месяц (последняя отправка каждого врача до срока).

Запуск: python3 dezhurstva/tools/wishes.py 2026-12 ОТВЕТЫ.(csv|txt|xlsx) [ещё файлы…] > dezhurstva/private/2026-12-wishes.json
Источник — что угодно с текстом ответов: выгрузка таблицы ответов (CSV/XLSX) или текст, который отдаёт
Google Drive. В каждом ответе есть строка «#DEZH {…}» — её и читаем; остальное игнорируем.
Пожелания, присланные иначе (мессенджер, устно), допишите в итоговый JSON вручную в том же формате.
Результат НЕ коммитить: пожелания личные (папка private/ в .gitignore)."""
import csv, datetime as dt, io, json, pathlib, re, sys

MARK = "#DEZH"
TZ = dt.timezone(dt.timedelta(hours=5))  # Екатеринбург
DEADLINE_DAY = 15


def texts(path):
    p = pathlib.Path(path)
    if p.suffix.lower() == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                for v in row:
                    if isinstance(v, str):
                        yield v
        return
    raw = p.read_text(encoding="utf-8-sig", errors="replace")
    yield raw
    if p.suffix.lower() == ".csv":
        for row in csv.reader(io.StringIO(raw)):
            yield from row


def payloads(text):
    dec = json.JSONDecoder()
    variants = {text, text.replace('""', '"'), text.replace('\\"', '"')}
    for t in variants:
        for m in re.finditer(re.escape(MARK) + r"\s*", t):
            try:
                obj, _ = dec.raw_decode(t, m.end())
            except ValueError:
                continue
            if isinstance(obj, dict) and obj.get("v") == 1 and obj.get("who") and obj.get("m"):
                yield obj


def deadline(mk):
    y, m = map(int, mk.split("-"))
    py, pm = (y - 1, 12) if m == 1 else (y, m - 1)
    return dt.datetime(py, pm, DEADLINE_DAY, 23, 59, 59, tzinfo=TZ)


def collect(mk, paths):
    seen, late = {}, {}
    for path in paths:
        for t in texts(path):
            for w in payloads(t):
                if w["m"] != mk:
                    continue
                ts = dt.datetime.fromisoformat(w["ts"].replace("Z", "+00:00"))
                bucket = seen if ts <= deadline(mk) else late
                old = bucket.get(w["who"])
                if old is None or old["ts"] < w["ts"]:
                    bucket[w["who"]] = w
    return seen, late


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    mk = sys.argv[1]
    seen, late = collect(mk, sys.argv[2:])
    print(json.dumps({"month": mk, "deadline": deadline(mk).isoformat(), "wishes": seen,
                      "late": {k: v for k, v in late.items() if k not in seen or v["ts"] > seen[k]["ts"]}},
                     ensure_ascii=False, indent=1))
    print(f"{mk}: пожеланий {len(seen)} ({', '.join(w['name'] for w in seen.values())})"
          + (f"; после срока: {', '.join(w['name'] for w in late.values())}" if late else ""), file=sys.stderr)


if __name__ == "__main__":
    main()
