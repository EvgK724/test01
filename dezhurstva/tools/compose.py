#!/usr/bin/env python3
"""Черновик графика дежурств на месяц по пожеланиям врачей.

Запуск из корня репозитория:
  python3 dezhurstva/tools/compose.py 2026-12 dezhurstva/private/2026-12-wishes.json
      [--exclude ID …] [--fix 2026-12-05=klepikov …] [--zero ID …] [--seed N]
Результат (папка private/, в git не попадает):
  2026-12-draft.json   — месяц в формате schedule.json (для make_xlsx.py --draft и publish.py)
  2026-12-report.txt   — отчёт для организатора: нагрузка, что из пожеланий не выполнено и почему
  2026-12-wishes-text.json — пожелания словами для второго листа Excel

Жёсткие правила: один дежурный в день; не два дня подряд (и не 1-го числа после дежурства в последний день
прошлого месяца); «не ставить», отпуск, дни недели «не ставить», «только в дни „Хочу“», «ровно 0».
Мягкие: количество (ровно / не больше / не меньше), сутки, свободные выходные, «хочу» по датам и дням недели,
поменьше дежурств через день, ровная нагрузка в часах у остальных. Выходные и праздники — календарь РФ.
Комментарии врачей программа не читает: их разбирает составитель (Claude) и переводит в даты или --fix."""
import argparse, calendar, collections, datetime as dt, json, math, pathlib, random, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ru_calendar

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRIV = ROOT / "private"
MON = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
GEN = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
WDN = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
MODE = {"eq": "ровно", "max": "не больше", "min": "не меньше"}
_cfg = ROOT / "data" / "config.json"
WEEK_HOURS = json.loads(_cfg.read_text()).get("week_hours", 39) if _cfg.exists() else 39
EMPTY = {"no": [], "vac": [], "yes": [], "noWd": [], "yesWd": [], "only": False,
         "total": {"mode": "any", "n": 0}, "full": {"mode": "any", "n": 0}, "freeWe": 0, "note": ""}


def minutes(a, b):
    h1, m1 = map(int, a.split(":"))
    h2, m2 = map(int, b.split(":"))
    m = h2 * 60 + m2 - h1 * 60 - m1
    return m if m > 0 else m + 1440


def compress(nums):
    nums, out, i = sorted(nums), [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"{nums[i]}–{nums[j]}" if j > i else str(nums[i]))
        i = j + 1
    return ", ".join(out)


def wish_text(w):
    """Пожелание словами — как в приложении."""
    day = lambda ks: compress(int(k[8:]) for k in ks)
    parts = []
    no = "; ".join(x for x in (", ".join(WDN[i] for i in w["noWd"]), day(w["no"])) if x)
    if no:
        parts.append("Не ставить: " + no)
    if w["vac"]:
        parts.append("Отпуск: " + day(w["vac"]))
    yes = "; ".join(x for x in (", ".join(WDN[i] for i in w["yesWd"]), day(w["yes"])) if x)
    if yes:
        parts.append("Хочу: " + yes + (" (только эти дни)" if w["only"] else ""))
    q = []
    if w["total"]["mode"] != "any":
        q.append(f"всего {MODE[w['total']['mode']]} {w['total']['n']}")
    if w["full"]["mode"] != "any":
        q.append(f"суток {MODE[w['full']['mode']]} {w['full']['n']}")
    if w.get("freeWe"):
        q.append(f"свободных выходных не меньше {w['freeWe']}")
    if q:
        parts.append("; ".join(q).capitalize())
    if w.get("note"):
        parts.append("«" + w["note"].strip() + "»")
    return ". ".join(parts) + "." if parts else "Без особых пожеланий."


class Problem:
    def __init__(self, mk, data, wishes, exclude=(), fixes=None, zero=()):
        self.mk = mk
        y, m = map(int, mk.split("-"))
        self.y, self.m = y, m
        n = calendar.monthrange(y, m)[1]
        self.days = [dt.date(y, m, i) for i in range(1, n + 1)]
        self.keys = [d.isoformat() for d in self.days]
        self.cal = ru_calendar.month(y, m)
        off = set(self.cal["off"])
        self.off = [k in off for k in self.keys]
        prev_mk = f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"
        prev = data["months"].get(prev_mk)
        self.prev = prev
        self.shift = (prev or {}).get("shift") or {"work": ["16:18", "08:00"], "off": ["08:00", "08:00"]}
        self.wmin, self.omin = minutes(*self.shift["work"]), minutes(*self.shift["off"])
        self.mins = [self.omin if o else self.wmin for o in self.off]
        order = list((prev or {}).get("order") or data["doctors"])
        for who in wishes:
            if who not in order and who in data["doctors"]:
                order.append(who)
        self.order = [d for d in order if d not in exclude]
        self.docs = self.order
        self.names = {d: data["doctors"][d]["name"] for d in self.docs}
        self.notes = []
        prev_cnt = collections.Counter(x for v in (prev or {}).get("duty", {}).values() for x in v)
        self.W = {}
        for d in self.docs:
            w = json.loads(json.dumps(EMPTY))
            if d in wishes:
                for k, v in wishes[d].items():
                    if k in w:
                        w[k] = v
            elif d in zero or (prev and prev_cnt[d] == 0):
                w["total"] = {"mode": "eq", "n": 0}
                self.notes.append(f"{self.names[d]}: пожеланий нет, в прошлом месяце без дежурств — без дежурств, как в прошлом месяце.")
            elif d not in wishes:
                self.notes.append(f"{self.names[d]}: пожеланий нет — поставлен на общих основаниях.")
            if d in zero:
                w["total"] = {"mode": "eq", "n": 0}
            self.W[d] = w
        # Доступность
        last_prev = None
        if prev:
            pk = max(prev["duty"]) if prev["duty"] else None
            if pk and pk == (self.days[0] - dt.timedelta(1)).isoformat():
                last_prev = prev["duty"][pk]
        self.avail = {}
        for d in self.docs:
            w = self.W[d]
            bad = set(w["no"]) | set(w["vac"])
            yes_k = set(w["yes"])
            a = []
            for i, k in enumerate(self.keys):
                wd = self.days[i].weekday()
                ok = k not in bad and wd not in w["noWd"]
                if w["only"] and (w["yes"] or w["yesWd"]):
                    ok = ok and (k in yes_k or wd in w["yesWd"])
                if w["total"]["mode"] == "eq" and w["total"]["n"] == 0:
                    ok = False
                if w["full"]["mode"] == "eq" and w["full"]["n"] == 0 and self.off[i]:
                    ok = False
                if i == 0 and last_prev and d in last_prev:
                    ok = False
                a.append(ok)
            self.avail[d] = a
        self.fixed = {}
        for k, who in (fixes or {}).items():
            i = self.keys.index(k)
            self.fixed[i] = who
        # Полные выходные (сб + вс внутри месяца)
        self.weekends = [(i, i + 1) for i, dd in enumerate(self.days[:-1]) if dd.weekday() == 5]
        self.yes_idx = {d: {self.keys.index(k) for k in self.W[d]["yes"] if k in self.keys} for d in self.docs}
        self.any_docs = [d for d in self.docs if self.W[d]["total"]["mode"] == "any" and any(self.avail[d])]

    # ---- стоимость ----
    def doc_cost(self, d, idx):
        w = self.W[d]
        cnt = len(idx)
        full = sum(self.off[i] for i in idx)
        c = 0.0
        t = w["total"]
        if t["mode"] == "eq":
            c += 400 * abs(cnt - t["n"])
        elif t["mode"] == "max":
            c += 400 * max(0, cnt - t["n"])
        elif t["mode"] == "min":
            c += 250 * max(0, t["n"] - cnt)
        f = w["full"]
        if f["mode"] == "eq":
            c += 250 * abs(full - f["n"])
        elif f["mode"] == "max":
            c += 250 * max(0, full - f["n"])
        elif f["mode"] == "min":
            c += 180 * max(0, f["n"] - full)
        if w.get("freeWe"):
            s = set(idx)
            free = sum(1 for a, b in self.weekends if a not in s and b not in s)
            c += 180 * max(0, w["freeWe"] - free)
        yi = self.yes_idx[d]
        s = set(idx)
        c += 60 * len(yi - s)
        c -= 12 * sum(1 for i in idx if self.days[i].weekday() in w["yesWd"])
        for a, b in zip(idx, idx[1:]):
            g = b - a
            if g == 1:
                c += 100000
            elif g == 2:
                c += 30
            elif g == 3:
                c += 6
        return c

    def balance(self, hours, fulls):
        ds = self.any_docs
        if len(ds) < 2:
            return 0.0
        mh = sum(hours[d] for d in ds) / len(ds)
        mf = sum(fulls[d] for d in ds) / len(ds)
        return sum(0.45 * (hours[d] - mh) ** 2 + 30 * (fulls[d] - mf) ** 2 for d in ds)

    def total(self, a):
        by = collections.defaultdict(list)
        for i, d in enumerate(a):
            if d:
                by[d].append(i)
        cost = sum(self.doc_cost(d, by[d]) for d in self.docs)
        hours = {d: sum(self.mins[i] for i in by[d]) / 60 for d in self.docs}
        fulls = {d: sum(self.off[i] for i in by[d]) for d in self.docs}
        empty = sum(1 for d in a if not d)
        return cost + self.balance(hours, fulls) + 5000 * empty

    def can(self, a, i, d):
        if not self.avail[d][i]:
            return False
        return not ((i > 0 and a[i - 1] == d) or (i + 1 < len(a) and a[i + 1] == d))

    def solve(self, seed=1, iters=60000):
        rnd = random.Random(seed)
        n = len(self.days)
        a = [None] * n
        for i, d in self.fixed.items():
            a[i] = d
        free = [i for i in range(n) if i not in self.fixed]
        free.sort(key=lambda i: (sum(self.avail[d][i] for d in self.docs), rnd.random()))
        for i in free:
            best, bc = None, math.inf
            for d in self.docs:
                if self.can(a, i, d):
                    a[i] = d
                    c = self.total(a)
                    if c < bc:
                        best, bc = d, c
                    a[i] = None
            a[i] = best
        cur = self.total(a)
        best_a, best_c = a[:], cur
        T0, T1 = 300.0, 0.5
        for it in range(iters):
            T = T0 * (T1 / T0) ** (it / iters)
            i = rnd.choice(free)
            if rnd.random() < 0.55:
                cands = [d for d in self.docs if d != a[i] and self.can(a, i, d)]
                if not cands:
                    continue
                old = a[i]
                a[i] = rnd.choice(cands)
                new = self.total(a)
                if new <= cur or rnd.random() < math.exp((cur - new) / T):
                    cur = new
                else:
                    a[i] = old
            else:
                j = rnd.choice(free)
                if j == i or a[i] == a[j]:
                    continue
                di, dj = a[i], a[j]
                a[i], a[j] = None, None
                ok = (dj is None or self.can(a, i, dj)) and (di is None or self.can(a, j, di))
                a[i], a[j] = dj, di
                if not ok:
                    a[i], a[j] = di, dj
                    continue
                new = self.total(a)
                if new <= cur or rnd.random() < math.exp((cur - new) / T):
                    cur = new
                else:
                    a[i], a[j] = di, dj
            if cur < best_c:
                best_a, best_c = a[:], cur
        return best_a, best_c

    # ---- результат ----
    def month(self, a):
        duty = {self.keys[i]: [d] for i, d in enumerate(a) if d}
        marks = []
        for d in self.docs:
            ks = sorted(self.W[d]["vac"])
            run = []
            for k in ks + [None]:
                if run and (k is None or dt.date.fromisoformat(k) - dt.date.fromisoformat(run[-1]) != dt.timedelta(1)):
                    marks.append({"who": d, "from": run[0], "to": run[-1], "label": "Отпуск"})
                    run = []
                if k:
                    run.append(k)
        return {"title": f"{MON[self.m - 1]} {self.y}", "order": self.order, "shift": self.shift,
                "off": self.cal["off"], "duty": duty, "marks": marks}

    def report(self, a):
        L = []
        by = collections.defaultdict(list)
        for i, d in enumerate(a):
            if d:
                by[d].append(i)
        norm = WEEK_HOURS / 5 * self.cal["workdays"] - len(self.cal["short"])
        L.append(f"ЧЕРНОВИК: {MON[self.m - 1]} {self.y}. Рабочих дней {self.cal['workdays']}, норма {norm:g} ч"
                 + ("" if self.cal["verified"] else " — ВНИМАНИЕ: переносы выходных этого года не сверены с постановлением"))
        hol = [int(k[8:]) for k in self.cal["hol"]]
        if hol:
            L.append(f"Праздники и переносы в будни: {compress(hol)} {GEN[self.m - 1]}; сутки — {self.shift['off'][0]}–{self.shift['off'][1]}.")
        if self.cal["work"]:
            L.append("Рабочие субботы/воскресенья: " + compress(int(k[8:]) for k in self.cal["work"]) + ".")
        L.append("")
        for d in self.docs:
            idx = by[d]
            h = sum(self.mins[i] for i in idx)
            full = sum(self.off[i] for i in idx)
            L.append(f"{self.names[d]:<14} {len(idx):>2} деж., суток {full}, {h // 60}:{h % 60:02d} ч, доля {h / 60 / norm:.2f} — "
                     + (compress(i + 1 for i in idx) or "—"))
        L.append("")
        issues = []
        for d in self.docs:
            w, idx = self.W[d], by[d]
            cnt, full = len(idx), sum(self.off[i] for i in idx)
            t, f = w["total"], w["full"]
            if t["mode"] == "eq" and cnt != t["n"] or t["mode"] == "max" and cnt > t["n"] or t["mode"] == "min" and cnt < t["n"]:
                issues.append(f"{self.names[d]}: всего {MODE[t['mode']]} {t['n']} — получилось {cnt}")
            if f["mode"] == "eq" and full != f["n"] or f["mode"] == "max" and full > f["n"] or f["mode"] == "min" and full < f["n"]:
                issues.append(f"{self.names[d]}: суток {MODE[f['mode']]} {f['n']} — получилось {full}")
            if w.get("freeWe"):
                s = set(idx)
                free = sum(1 for x, y in self.weekends if x not in s and y not in s)
                if free < w["freeWe"]:
                    issues.append(f"{self.names[d]}: свободных выходных не меньше {w['freeWe']} — получилось {free}")
            miss = sorted(self.yes_idx[d] - set(idx))
            if miss:
                issues.append(f"{self.names[d]}: хотел(а) {compress(i + 1 for i in miss)} — "
                              + "; ".join(f"{i + 1} — {self.names.get(a[i], 'никто') if a[i] else 'никто'}" for i in miss))
            gaps = [idx[k] + 1 for k in range(len(idx) - 1) if idx[k + 1] - idx[k] == 2]
            if gaps:
                issues.append(f"{self.names[d]}: через день после {compress(gaps)}")
        empty = [i + 1 for i, d in enumerate(a) if not d]
        if empty:
            issues.insert(0, f"!!! Дни без дежурного: {compress(empty)} — никто не может по пожеланиям; решите вручную (--fix).")
        L.append("Что не совпало с пожеланиями:" if issues else "Все пожелания выполнены.")
        L += ["  • " + x for x in issues]
        notes = [f"{self.names[d]}: «{self.W[d]['note']}»" for d in self.docs if self.W[d].get("note")]
        if notes:
            L.append("")
            L.append("Комментарии врачей (проверьте, что учтены):")
            L += ["  • " + x for x in notes]
        if self.notes:
            L.append("")
            L += ["  • " + x for x in self.notes]
        return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("month")
    ap.add_argument("wishes")
    ap.add_argument("--data", default=str(ROOT / "data" / "schedule.json"))
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--zero", action="append", default=[], help="врач без дежурств в этом месяце")
    ap.add_argument("--fix", action="append", default=[], help="2026-12-05=klepikov — назначить вручную")
    ap.add_argument("--seed", type=int, default=0, help="0 — лучший из нескольких запусков")
    a = ap.parse_args()
    data = json.loads(pathlib.Path(a.data).read_text())
    raw = json.loads(pathlib.Path(a.wishes).read_text())
    wishes = raw.get("wishes", raw)
    fixes = dict(x.split("=", 1) for x in a.fix)
    P = Problem(a.month, data, wishes, a.exclude, fixes, a.zero)
    runs = [a.seed] if a.seed else range(1, 7)
    best = min((P.solve(s) for s in runs), key=lambda r: r[1])
    month = P.month(best[0])
    PRIV.mkdir(exist_ok=True)
    (PRIV / f"{a.month}-draft.json").write_text(json.dumps(month, ensure_ascii=False, indent=1) + "\n")
    texts = {d: wish_text(P.W[d]) if d in wishes else ("Без дежурств." if P.W[d]["total"] == {"mode": "eq", "n": 0} else "Пожеланий нет.")
             for d in P.docs}
    (PRIV / f"{a.month}-wishes-text.json").write_text(json.dumps(texts, ensure_ascii=False, indent=1) + "\n")
    rep = P.report(best[0])
    (PRIV / f"{a.month}-report.txt").write_text(rep + "\n")
    print(rep)
    print(f"\n→ private/{a.month}-draft.json, -report.txt, -wishes-text.json (стоимость {best[1]:.0f})")


if __name__ == "__main__":
    main()
