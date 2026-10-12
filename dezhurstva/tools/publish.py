#!/usr/bin/env python3
"""Публикация утверждённого месяца: черновик compose.py → data/schedule.json → сборка (приложение, календари, Excel).

Только после явного подтверждения организатора («утверждаю»)!
  python3 dezhurstva/tools/publish.py 2026-12 [dezhurstva/private/2026-12-draft.json]
Если организатор прислал поправленный Excel — вместо этого: python3 dezhurstva/tools/import_xlsx.py ФАЙЛ.xlsx
Затем commit и push в main — у всех обновятся приложение и календари."""
import datetime as dt, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    mk = sys.argv[1]
    src = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "private" / f"{mk}-draft.json"
    month = json.loads(src.read_text())
    path = ROOT / "data" / "schedule.json"
    data = json.loads(path.read_text())
    unknown = {w for v in month["duty"].values() for w in v} - set(data["doctors"])
    if unknown:
        sys.exit(f"неизвестные врачи: {unknown} — добавьте их в data/schedule.json → doctors")
    data["months"][mk] = month
    data["months"] = dict(sorted(data["months"].items()))
    data["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"→ {month['title']} в data/schedule.json")
    build.main()


if __name__ == "__main__":
    main()
