#!/usr/bin/env python3
"""Подтверждения предварительного графика: ответы Google Формы → data/schedule.json → сборка.

  python3 dezhurstva/tools/confirm.py dezhurstva/private/answers.csv [ещё файлы…]
Врач в приложении нажимает «Согласен» или «Не согласен» (с причиной) — в форму уходит «#DEZH {"kind": "ack", …}».
Для каждого предварительного месяца берётся последний ответ каждого врача на ТЕКУЩУЮ версию.
Согласны все из списка — месяц становится окончательным. Печатает отчёт для организатора: кто согласен,
кто нет и почему (причины — только в отчёте, в приложение и репозиторий не попадают), кто ещё не ответил.
Код выхода: 0 — данные изменились (нужны commit и push), 3 — изменений нет."""
import datetime as dt, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build, wishes

ROOT = pathlib.Path(__file__).resolve().parent.parent


def acks(paths):
    out = []
    for p in paths:
        for t in wishes.texts(p):
            out += [w for w in wishes.payloads(t, kind="ack")]
    seen, uniq = set(), []
    for a in sorted(out, key=lambda a: a["ts"]):
        k = (a["who"], a["m"], a.get("ver"), a["ts"])
        if k not in seen:
            seen.add(k)
            uniq.append(a)
    return uniq


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = ROOT / "data" / "schedule.json"
    data = json.loads(path.read_text())
    answers = acks(sys.argv[1:])
    changed = False
    for mk, m in data["months"].items():
        if m.get("status") != "preliminary":
            continue
        c = m["confirm"]
        ver = c["version"]
        last = {}
        for a in answers:
            if a["m"] == mk and a.get("ver") == ver and a["who"] in c["need"]:
                last[a["who"]] = a
        ok = set(c["confirmed"]) | {w for w, a in last.items() if a.get("ok")}
        ok -= {w for w, a in last.items() if not a.get("ok")}
        bad = {w: a for w, a in last.items() if not a.get("ok")}
        name = lambda w: data["doctors"].get(w, {}).get("name", w)
        print(f"{m['title']}, версия {ver}: согласны {len(ok & set(c['need']))} из {len(c['need'])}")
        for w in c["need"]:
            if w in ok:
                print(f"  ✓ {name(w)}")
        for w, a in bad.items():
            when = dt.datetime.fromisoformat(a["ts"].replace("Z", "+00:00")).astimezone(dt.timezone(dt.timedelta(hours=5)))
            print(f"  ✗ {name(w)} ({when:%d.%m %H:%M}): {a.get('note') or 'без комментария'}")
        wait = [w for w in c["need"] if w not in ok and w not in bad]
        if wait:
            print("  … не ответили:", ", ".join(name(w) for w in wait))
        new_conf = [w for w in c["need"] if w in ok]
        if new_conf != c["confirmed"] or len(bad) != c.get("disagreed", 0):
            c["confirmed"], c["disagreed"] = new_conf, len(bad)
            changed = True
        if set(c["need"]) <= ok:
            m["status"] = "final"
            m["final_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            changed = True
            print(f"  → все согласны: {m['title']} — ОКОНЧАТЕЛЬНЫЙ")
    if not changed:
        print("изменений нет")
        sys.exit(3)
    data["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    build.main()


if __name__ == "__main__":
    main()
