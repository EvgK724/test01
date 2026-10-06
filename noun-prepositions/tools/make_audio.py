"""Озвучивает фразы из phrases.json голосом Microsoft Ryan (en-GB-RyanNeural).

Файлы: audio/<fnv1a-хэш фразы>.mp3 и список audio/index.json, по которому
приложение понимает, какие записи есть. Уже готовые файлы не перезаписываются,
лишние (от удалённых фраз) удаляются.

Запуск:  pip install edge-tts  &&  python tools/make_audio.py
"""
import asyncio
import json
import pathlib

import edge_tts

VOICE = "en-GB-RyanNeural"
RATE = "-4%"
ROOT = pathlib.Path(__file__).resolve().parent.parent
AUDIO = ROOT / "audio"


def fnv(text: str) -> str:
    """FNV-1a (32 бита) по UTF-8 — тот же хэш, что fnv() в index.html."""
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


async def synth(text: str, path: pathlib.Path) -> bool:
    for attempt in range(4):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(path))
            if path.stat().st_size > 0:
                return True
        except Exception as exc:  # сеть или лимит сервиса — пробуем ещё раз
            print(f"  retry {attempt + 1}: {exc}")
        await asyncio.sleep(2 * (attempt + 1))
    path.unlink(missing_ok=True)
    return False


async def main() -> None:
    phrases = json.loads((ROOT / "phrases.json").read_text("utf-8"))["phrases"]
    AUDIO.mkdir(exist_ok=True)
    ready, failed = [], []
    for text in phrases:
        h = fnv(text)
        path = AUDIO / f"{h}.mp3"
        if path.exists() and path.stat().st_size > 0:
            ready.append(h)
            continue
        print(f"{h}  {text}")
        (ready if await synth(text, path) else failed).append(h)

    keep = set(ready)
    for old in AUDIO.glob("*.mp3"):
        if old.stem not in keep:
            old.unlink()

    (AUDIO / "index.json").write_text(
        json.dumps({"voice": VOICE, "files": sorted(keep)}, indent=1) + "\n", "utf-8"
    )
    print(f"{len(keep)} ready, {len(failed)} failed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
