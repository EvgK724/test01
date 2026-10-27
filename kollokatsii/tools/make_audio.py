"""Озвучивает фразы из phrases.json голосом Microsoft Ryan (en-GB-RyanNeural).

Файлы: audio/<fnv1a-хэш фразы>.mp3 и список audio/index.json, по которому приложение понимает,
какие записи есть. Уже готовые файлы не перезаписываются, лишние (от удалённых фраз) удаляются.

Фраз здесь тысячи, поэтому записи делаются по WORKERS одновременно, а скрипт не падает из-за части неудач:
он сохраняет всё, что успел, и завершается успешно — GitHub Actions закоммитит готовые записи, а недостающие
доделает следующий запуск. Останавливается раньше, если сервис подряд отказал MAX_FAILS раз или прошло TIME_LIMIT секунд.

Запуск:  pip install edge-tts  &&  python tools/make_audio.py
"""
import asyncio
import json
import pathlib
import time

import edge_tts

VOICE = "en-GB-RyanNeural"
RATE = "-4%"
ROOT = pathlib.Path(__file__).resolve().parent.parent
AUDIO = ROOT / "audio"
MAX_FAILS = 12
TIME_LIMIT = 100 * 60
WORKERS = 4


def fnv(text: str) -> str:
    """FNV-1a (32 бита) по UTF-8 — тот же хэш, что fnv() в index.html."""
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


async def synth(text: str, path: pathlib.Path) -> bool:
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(path))
            if path.stat().st_size > 0:
                return True
        except Exception as exc:  # сеть или лимит сервиса — пробуем ещё раз
            print(f"  retry {attempt + 1}: {exc}")
        await asyncio.sleep(2 * (attempt + 1))
    path.unlink(missing_ok=True)
    return False


def save_index(keep):
    (AUDIO / "index.json").write_text(
        json.dumps({"voice": VOICE, "files": sorted(keep)}, indent=1) + "\n", "utf-8"
    )


async def main() -> None:
    phrases = json.loads((ROOT / "phrases.json").read_text("utf-8"))["phrases"]
    AUDIO.mkdir(exist_ok=True)
    wanted = {fnv(t) for t in phrases}
    for old in AUDIO.glob("*.mp3"):
        if old.stem not in wanted:
            old.unlink()
    ready = {p.stem for p in AUDIO.glob("*.mp3") if p.stat().st_size > 0}
    todo = [t for t in phrases if fnv(t) not in ready]
    print(f"{len(ready)} ready, {len(todo)} to record")
    start = time.time()
    st = {"fails": 0, "made": 0, "stop": ""}
    queue = list(todo)

    async def worker():
        while queue and not st["stop"]:
            if st["fails"] >= MAX_FAILS:
                st["stop"] = f"Сервис отказал {MAX_FAILS} раз подряд — остальное в следующий запуск"
                break
            if time.time() - start > TIME_LIMIT:
                st["stop"] = "Время вышло — остальное в следующий запуск"
                break
            text = queue.pop(0)
            h = fnv(text)
            if await synth(text, AUDIO / f"{h}.mp3"):
                ready.add(h)
                st["made"] += 1
                st["fails"] = 0
                if st["made"] % 100 == 0:
                    print(f"  … {st['made']} new")
                    save_index(ready)
            else:
                st["fails"] += 1
                print(f"  failed: {text}")

    await asyncio.gather(*(worker() for _ in range(WORKERS)))
    if st["stop"]:
        print(st["stop"])
    made = st["made"]
    save_index(ready)
    print(f"{len(ready)} of {len(wanted)} ready ({made} new)")


if __name__ == "__main__":
    asyncio.run(main())
