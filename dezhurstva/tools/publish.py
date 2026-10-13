#!/usr/bin/env python3
"""Публикация месяца, одобренного организатором: черновик compose.py → data/schedule.json → сборка.

Одобренный график становится ПРЕДВАРИТЕЛЬНЫМ: у всех врачей в приложении — уведомление «ознакомьтесь»,
каждый отвечает «Согласен» или «Не согласен» с причиной (ответы — в Google Форму, их сводит confirm.py).
Когда согласны все — график ОКОНЧАТЕЛЬНЫЙ (это делает confirm.py). Повторная публикация того же месяца после правок —
новая версия: подтверждения обнуляются, врачи получают новое уведомление.

Только после явного «утверждаю» организатора!
  python3 dezhurstva/tools/publish.py 2026-12 [dezhurstva/private/2026-12-draft.json]
  python3 dezhurstva/tools/publish.py 2026-12 --final      без согласования (сразу окончательный)
Если организатор прислал поправленный Excel: import_xlsx.py ФАЙЛ.xlsx, затем publish.py 2026-12 --again
(новая версия того месяца, что уже в данных). Затем commit и push в main."""
import datetime as dt, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build

ROOT = pathlib.Path(__file__).resolve().parent.parent


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        sys.exit(__doc__)
    mk = args[0]
    path = ROOT / "data" / "schedule.json"
    data = json.loads(path.read_text())
    cfg_path = ROOT / "data" / "config.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    old = data["months"].get(mk, {})
    if "--again" in flags:
        if not old:
            sys.exit(f"месяца {mk} ещё нет в data/schedule.json")
        month = dict(old)
    else:
        src = pathlib.Path(args[1]) if len(args) > 1 else ROOT / "private" / f"{mk}-draft.json"
        month = json.loads(src.read_text())
    unknown = {w for v in month["duty"].values() for w in v} - set(data["doctors"])
    if unknown:
        sys.exit(f"неизвестные врачи: {unknown} — добавьте их в data/schedule.json → doctors")
    if "--final" in flags:
        month["status"] = "final"
        month["final_at"] = now()
        month.pop("confirm", None)
    else:
        ver = int(old.get("version", 0)) + 1 if old.get("status") == "preliminary" or "--again" in flags else 1
        org = cfg.get("organizer")
        month["status"] = "preliminary"
        month["version"] = ver
        month["confirm"] = {"version": ver, "published": now(), "need": list(month["order"]),
                            "confirmed": [org] if org in month["order"] else [], "disagreed": 0}
    data["months"][mk] = month
    data["months"] = dict(sorted(data["months"].items()))
    data["updated"] = now()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    st = "окончательный" if month["status"] == "final" else f"предварительный, версия {month['version']}"
    print(f"→ {month['title']} в data/schedule.json ({st})")
    build.main()


if __name__ == "__main__":
    main()
