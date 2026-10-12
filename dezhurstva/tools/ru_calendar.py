"""Производственный календарь РФ: выходные, праздники, переносы, сокращённые предпраздничные дни.

ТК РФ ст. 112: нерабочие праздники — 1–8 января, 23 февраля, 8 марта, 1 и 9 мая, 12 июня, 4 ноября;
праздник, совпавший с выходным (кроме январских), переносится на следующий рабочий день.
Ст. 95: рабочий день перед нерабочим праздником короче на 1 час.
Переносы на каждый год — постановлением Правительства (TRANSFERS). Год без записи в TRANSFERS считается
по одному ТК и помечается как непроверенный: найдите постановление «О переносе выходных дней в <год> году»
и добавьте переносы сюда."""
import datetime as dt

FIXED = [(1, d) for d in range(1, 9)] + [(2, 23), (3, 8), (5, 1), (5, 9), (6, 12), (11, 4)]
# (с какого дня, на какой): «на» становится выходным; «с» — рабочим, если сам не праздник
TRANSFERS = {
    # Постановление Правительства РФ от 24.09.2025 № 1466
    2026: [("2026-01-03", "2026-01-09"), ("2026-01-04", "2026-12-31")],
    # Постановление Правительства РФ от 17.09.2026 № 1187 (по сообщениям; сверить с pravo.gov.ru перед январём 2027):
    # нерабочие 1–10 января, 21–23 февраля, 6–8 марта, 1–3 и 8–10 мая, 12–14 июня, 4–7 ноября, 31 декабря;
    # суббота 20 февраля — рабочая
    2027: [("2027-01-02", "2027-11-05"), ("2027-01-03", "2027-12-31"), ("2027-02-20", "2027-02-22")],
}
# Годы, переносы которых взяты не из текста постановления, — сверить и убрать отсюда
UNCONFIRMED = {2027}


def year(y):
    """{'off': выходные и праздники, 'hol': праздники и перенесённые выходные в будни,
    'work': рабочие сб/вс, 'short': сокращённые дни, 'verified': есть ли переносы на этот год}."""
    days = [dt.date(y, 1, 1) + dt.timedelta(n) for n in range((dt.date(y + 1, 1, 1) - dt.date(y, 1, 1)).days)]
    holidays = {dt.date(y, m, d) for m, d in FIXED}
    off = {d for d in days if d.weekday() >= 5} | holidays
    work = set()
    for a, b in TRANSFERS.get(y, []):
        a, b = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
        off.add(b)
        if a not in holidays:
            off.discard(a)
            work.add(a)
    # Автоматический перенос (кроме январских праздников)
    for h in sorted(holidays):
        if h.month == 1 or h.weekday() < 5:
            continue
        d = h + dt.timedelta(1)
        while d in off:
            d += dt.timedelta(1)
        if d.year == y:
            off.add(d)
    short = set()
    for h in holidays:
        d = h - dt.timedelta(1)
        if d.year == y and d not in off:
            short.add(d)
    hol = {d for d in off if d.weekday() < 5}
    return {"off": off, "hol": hol, "work": work, "short": short, "verified": y in TRANSFERS and y not in UNCONFIRMED}


_cache = {}


def info(d):
    if d.year not in _cache:
        _cache[d.year] = year(d.year)
    return _cache[d.year]


def is_off(d):
    return d in info(d)["off"]


def month(y, m):
    """Сводка месяца: даты выходных/праздников, сокращённых, рабочих сб/вс, число рабочих дней."""
    first = dt.date(y, m, 1)
    n = ((first.replace(year=y + (m == 12), month=m % 12 + 1)) - first).days
    ds = [first + dt.timedelta(i) for i in range(n)]
    i = info(first)
    return {
        "off": [d.isoformat() for d in ds if d in i["off"]],
        "hol": [d.isoformat() for d in ds if d in i["hol"]],
        "work": [d.isoformat() for d in ds if d in i["work"]],
        "short": [d.isoformat() for d in ds if d in i["short"]],
        "workdays": sum(d not in i["off"] for d in ds),
        "verified": i["verified"],
    }


if __name__ == "__main__":
    import sys
    for y in map(int, sys.argv[1:] or ["2026", "2027"]):
        r = year(y)
        print(y, "проверен" if r["verified"] else "НЕ ПРОВЕРЕН")
        print("  праздники и переносы в будни:", ", ".join(d.strftime("%d.%m") for d in sorted(r["hol"])))
        print("  рабочие сб/вс:", ", ".join(d.strftime("%d.%m") for d in sorted(r["work"])) or "—")
        print("  сокращённые:", ", ".join(d.strftime("%d.%m") for d in sorted(r["short"])))
        print("  рабочих дней по месяцам:", [month(y, m)["workdays"] for m in range(1, 13)],
              "всего", sum(month(y, m)["workdays"] for m in range(1, 13)))
