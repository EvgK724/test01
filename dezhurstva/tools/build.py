#!/usr/bin/env python3
"""Сборка: data/schedule.json + data/config.json + tools/template.html → index.html,
календари cal/<врач>.ics и cal/all.ics, файлы files/<месяц>.xlsx (без телефонов).
Запуск из корня репозитория: python3 dezhurstva/tools/build.py (import_xlsx.py вызывает её сам)."""
import datetime as dt, hashlib, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import make_xlsx, ru_calendar

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Цвета врачей — только синие и голубые оттенки
COLORS = ["#3BE8FF", "#4D9BFF", "#8FD3FF", "#62B6FF", "#8A9BFF", "#5CC8FF", "#B8E6FF", "#5B7DFF", "#6FF0FF", "#A0B4FF"]
# Версия оформления Excel: поменяли make_xlsx.py — увеличьте, чтобы файлы пересобрались
XLSX_FORMAT = 3
# Напоминания: накануне в 19:00 и за час до начала
EVE_HOUR = 19


def fold(line):
    """Строки .ics — не длиннее 75 байт, перенос с пробелом; UTF-8 не режем посреди символа."""
    out, cur = [], b""
    for ch in line:
        b = ch.encode()
        if len(cur) + len(b) > (75 if not out else 74):
            out.append(cur)
            cur = b""
        cur += b
    out.append(cur)
    return b"\r\n ".join(out).decode()


def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\;").replace(",", "\\,").replace("\n", "\\n")


def hm(s):
    h, m = s.split(":")
    return int(h), int(m)


def dur_text(mins):
    h, m = divmod(mins, 60)
    return f"{h} ч {m} мин" if m else f"{h} ч"


def shifts(data):
    """Все смены: (дата, врач, начало, конец, выходной ли)."""
    for mk, m in data["months"].items():
        off = set(m["off"])
        for day, who in m["duty"].items():
            d = dt.date.fromisoformat(day)
            a, b = m["shift"]["off" if day in off else "work"]
            start = dt.datetime.combine(d, dt.time(*hm(a)))
            end = dt.datetime.combine(d, dt.time(*hm(b)))
            if end <= start:
                end += dt.timedelta(days=1)
            for w in who:
                yield d, w, start, end, day in off


def ics(data, name, items, alarms, color):
    stamp = data["updated"].replace("-", "").replace(":", "")
    tz = data["tz"]
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//evgk724//dezhurstva//RU", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", f"X-WR-CALNAME:{esc(name)}", f"X-WR-TIMEZONE:{tz}", f"X-APPLE-CALENDAR-COLOR:{color}",
             "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H",
             "BEGIN:VTIMEZONE", f"TZID:{tz}", "BEGIN:STANDARD", "DTSTART:19700101T000000",
             "TZOFFSETFROM:+0500", "TZOFFSETTO:+0500", "TZNAME:+05", "END:STANDARD", "END:VTIMEZONE"]
    for d, who, start, end, off in sorted(items, key=lambda x: (x[2], x[1])):
        mins = int((end - start).total_seconds() // 60)
        kind = ("праздник" if d.weekday() < 5 else "выходной") if off else "будний день"
        t = f"{start:%H:%M}–{end:%H:%M}"
        summary = "Дежурство ПСО" + ("" if alarms else f": {data['doctors'][who]['name']}")
        lines += ["BEGIN:VEVENT", f"UID:{d.isoformat()}-{who}@dezhurstva.evgk724.github.io", f"DTSTAMP:{stamp}",
                  f"DTSTART;TZID={tz}:{start:%Y%m%dT%H%M%S}", f"DTEND;TZID={tz}:{end:%Y%m%dT%H%M%S}",
                  f"SUMMARY:{esc(summary)}", f"DESCRIPTION:{esc(f'{kind.capitalize()}, {t} ({dur_text(mins)}).')}",
                  "TRANSP:OPAQUE"]
        if alarms:
            eve = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(EVE_HOUR))
            before = int((start - eve).total_seconds() // 60)
            h, m = divmod(before, 60)
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{esc(f'Завтра дежурство ПСО, {start:%H:%M}')}",
                      f"TRIGGER:-PT{h}H{m}M" if m else f"TRIGGER:-PT{h}H", "END:VALARM",
                      "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{esc(f'Через час дежурство ПСО, {start:%H:%M}')}",
                      "TRIGGER:-PT1H", "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


def main():
    data = json.loads((ROOT / "data" / "schedule.json").read_text())
    ids = list(data["doctors"])
    all_items = list(shifts(data))
    cal = ROOT / "cal"
    cal.mkdir(exist_ok=True)
    for i, did in enumerate(ids):
        mine = [x for x in all_items if x[1] == did]
        (cal / f"{did}.ics").write_bytes(ics(data, f"Дежурства ПСО — {data['doctors'][did]['name']}", mine, True,
                                             COLORS[i % len(COLORS)]).encode())
    (cal / "all.ics").write_bytes(ics(data, "Дежурства ПСО — все", all_items, False, COLORS[0]).encode())
    # Excel для вкладки «Excel»: пересобираем только изменившиеся месяцы
    hp = ROOT / "files" / "hashes.json"
    hashes = json.loads(hp.read_text()) if hp.exists() else {}
    files = {}
    for mk, m in data["months"].items():
        h = hashlib.sha1(json.dumps([XLSX_FORMAT, m, {i: data["doctors"][i]["name"] for i in m["order"]}], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
        path = ROOT / "files" / f"{mk}.xlsx"
        if hashes.get(mk) != h or not path.exists():
            make_xlsx.public(mk, data)
            hashes[mk] = h
        files[mk] = f"files/{mk}.xlsx?v={h}"
    hp.parent.mkdir(exist_ok=True)
    hp.write_text(json.dumps(hashes, indent=1, sort_keys=True) + "\n")
    # Производственный календарь: от первого опубликованного месяца на 15 месяцев вперёд от сегодняшнего
    start = min([*data["months"], dt.date.today().strftime("%Y-%m")])
    y, m = map(int, start.split("-"))
    end = dt.date.today().replace(day=1)
    end = (end.year + (end.month + 14) // 12, (end.month + 14) % 12 or 12)
    cal = {}
    while (y, m) <= end:
        r = ru_calendar.month(y, m)
        cal[f"{y}-{m:02d}"] = {k: r[k] for k in ("off", "hol", "work", "short", "verified")}
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    cfg_path = ROOT / "data" / "config.json"
    config = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    tpl = (ROOT / "tools" / "template.html").read_text()
    payload = json.dumps({**data, "colors": COLORS, "cal": cal, "files": files,
                          "config": {"form": config.get("form", {}), "deadline": config.get("deadline", 15),
                                     "weekHours": config.get("week_hours", 39)}},
                         ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (ROOT / "index.html").write_text(tpl.replace("__DATA__", payload))
    print(f"→ dezhurstva/index.html, cal/: {len(ids)} врачей + all.ics, смен {len(all_items)}, Excel: {', '.join(files)}")


if __name__ == "__main__":
    main()
