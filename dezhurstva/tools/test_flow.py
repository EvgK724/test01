#!/usr/bin/env python3
"""Проверка цикла согласования на временной копии (без сети):
черновик → одобрение (предварительный, версия 1) → часть согласна, один не согласен → правка (версия 2) →
все согласны → окончательный. Запуск из корня репозитория: python3 dezhurstva/tools/test_flow.py"""
import csv, json, pathlib, shutil, subprocess, sys, tempfile

SRC = pathlib.Path(__file__).resolve().parent.parent
tmp = pathlib.Path(tempfile.mkdtemp()) / "dezhurstva"
shutil.copytree(SRC, tmp, ignore=shutil.ignore_patterns("private", "shots", "__pycache__"))
T = tmp / "tools"
fails = []


def check(cond, msg):
    print(("ok  " if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)


def run(*args, ok=(0,)):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
    if r.returncode not in ok:
        print(r.stdout, r.stderr)
        raise SystemExit(f"{args[0]} → {r.returncode}")
    return r


def answers(rows):
    path = tmp / "private" / "answers.csv"
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Timestamp", "Пожелания"])
        for who, ver, ok, note, ts in rows:
            p = {"v": 1, "kind": "ack", "m": "2026-12", "ver": ver, "who": who, "name": who, "ok": ok, "note": note, "ts": ts}
            w.writerow([ts, ("Согласен" if ok else "Не согласен") + "\n#DEZH " + json.dumps(p, ensure_ascii=False)])
    return path


data = lambda: json.loads((tmp / "data" / "schedule.json").read_text())
cal = lambda who: (tmp / "cal" / f"{who}.ics").read_bytes().decode().replace("\r\n ", "")
(tmp / "private").mkdir(exist_ok=True)
(tmp / "private" / "w.json").write_text(json.dumps({"wishes": {}}))
run(T / "compose.py", "2026-12", tmp / "private" / "w.json", "--seed", "1")
run(T / "publish.py", "2026-12")
m = data()["months"]["2026-12"]
need = m["confirm"]["need"]
check(m["status"] == "preliminary" and m["version"] == 1 and m["confirm"]["confirmed"] == ["klepikov"], "одобрено → предварительный, версия 1, организатор уже согласен")
ics = cal("omutov")
check("(предварительно)" in ics and "подтвердите график на декабрь 2026" in ics, "календарь: «(предварительно)» и напоминание подтвердить")
check("подтвердите" not in cal("klepikov"), "у организатора напоминания нет")
import openpyxl
check("ПРЕДВАРИТЕЛЬНЫЙ" in openpyxl.load_workbook(tmp / "files" / "2026-12.xlsx").worksheets[0]["A1"].value, "в Excel пометка «предварительный»")
others = [w for w in need if w != "klepikov"]
rows = [(w, 1, True, "", f"2026-11-17T0{i}:00:00Z") for i, w in enumerate(others[:-1])]
rows.append((others[-1], 1, False, "Не могу 24-го, конференция", "2026-11-17T09:00:00Z"))
rows.append(("wishes-noise", 1, True, "", "2026-11-17T09:30:00Z"))
r = run(T / "confirm.py", answers(rows))
m = data()["months"]["2026-12"]
check(m["status"] == "preliminary" and len(m["confirm"]["confirmed"]) == len(need) - 1 and m["confirm"]["disagreed"] == 1,
      f"не все согласны → остаётся предварительным ({len(m['confirm']['confirmed'])} из {len(need)}, 1 против)")
check("Не могу 24-го, конференция" in r.stdout and "Не могу" not in (tmp / "data" / "schedule.json").read_text(),
      "причина несогласия — в отчёте организатору, но не в данных приложения")
r = run(T / "confirm.py", answers(rows), ok=(3,))
check(r.returncode == 3, "повторная проверка без новых ответов — «изменений нет»")
# Правка организатора → версия 2: подтверждения обнуляются
run(T / "publish.py", "2026-12", "--again")
m = data()["months"]["2026-12"]
check(m["version"] == 2 and m["confirm"]["confirmed"] == ["klepikov"] and m["status"] == "preliminary", "правка → версия 2, подтверждения сначала")
check("v2-omutov" in cal("omutov") or "omutov" not in need, "новое напоминание в календаре на версию 2")
rows2 = rows + [(w, 2, True, "", f"2026-11-18T0{i}:00:00Z") for i, w in enumerate(others)]
run(T / "confirm.py", answers(rows2))
m = data()["months"]["2026-12"]
check(m["status"] == "final" and "final_at" in m, "все согласны с версией 2 → окончательный")
check("предварительно" not in cal("omutov") and "подтвердите" not in cal("omutov"),
      "после окончательного — в календаре без пометок и напоминаний")
# Исправленный Excel организатора: импорт сохраняет версию, --again даёт следующую (старые «согласен» не засчитываются)
run(T / "publish.py", "2026-12", "--again")
v_before = data()["months"]["2026-12"]["version"]
run(T / "make_xlsx.py", "2026-12", "--full", tmp / "private" / "edited.xlsx")
run(T / "import_xlsx.py", tmp / "private" / "edited.xlsx")
check(data()["months"]["2026-12"]["version"] == v_before, "импорт исправленного Excel сохраняет номер версии")
run(T / "publish.py", "2026-12", "--again")
m = data()["months"]["2026-12"]
run(T / "confirm.py", answers(rows2), ok=(0, 3))
m = data()["months"]["2026-12"]
check(m["version"] == v_before + 1 and m["status"] == "preliminary" and m["confirm"]["confirmed"] == ["klepikov"],
      f"после исправленного Excel — версия {v_before + 1}, прошлые согласия не считаются")
# Пожелания не путаются с подтверждениями
sys.path.insert(0, str(T))
import wishes
check(wishes.collect("2026-12", [tmp / "private" / "answers.csv"])[0] == {}, "ответы «согласен» не считаются пожеланиями")
shutil.rmtree(tmp.parent)
print("ПРОВАЛОВ:", len(fails))
sys.exit(1 if fails else 0)
