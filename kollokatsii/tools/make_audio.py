"""Generate and validate Microsoft Ryan audio for kollokatsii only.

Install edge-tts==7.3.1 and ffmpeg, then run this file. --check makes no
network requests or file changes. FFMPEG_BINARY can name a local decoder.
Completed MP3s are kept between runs; the public index changes only when every
required recording is valid. An incomplete run exits nonzero, so CI cannot
commit/publish a partial batch. No files from other applications are touched.
"""
import argparse
import array
import asyncio
from collections import deque
import json
import os
import pathlib
import shutil
import ssl
import subprocess
import sys
import tempfile
import time

import aiohttp
import edge_tts

VOICE = "en-GB-RyanNeural"
RATE = "-4%"
ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_FAILS = 12
TIME_LIMIT = 100 * 60
WORKERS = 4
ATTEMPTS = 3
REQUEST_TIMEOUT = 75


class NonRetryableError(RuntimeError):
    """An access or TLS failure must stop the run without a workaround."""


def fnv(text: str) -> str:
    """UTF-8 FNV-1a, matching fnv() in index.html."""
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def load_phrases(root: pathlib.Path) -> dict[str, str]:
    data = json.loads((root / "phrases.json").read_text("utf-8"))
    phrases = data.get("phrases")
    if data.get("voice") != VOICE or not isinstance(phrases, list) or not phrases:
        raise ValueError("phrases.json must contain the Ryan voice and a nonempty phrase list")
    wanted = {}
    for phrase in phrases:
        if not isinstance(phrase, str) or not phrase.strip():
            raise ValueError("Every phrase must be a nonempty string")
        key = fnv(phrase)
        if key in wanted and wanted[key] != phrase:
            raise ValueError(f"FNV collision for {key}; refusing to reuse the wrong recording")
        wanted[key] = phrase
    return wanted


def decoder_path(value: str | None) -> str:
    candidate = value or os.environ.get("FFMPEG_BINARY") or "ffmpeg"
    resolved = shutil.which(candidate)
    if not resolved:
        raise ValueError("ffmpeg is required; install it or set FFMPEG_BINARY")
    return resolved


def valid_mp3(path: pathlib.Path, ffmpeg: str) -> bool:
    """Decode the entire MP3 and require non-silent PCM, not merely nonzero bytes."""
    if not path.is_file() or path.stat().st_size < 128:
        return False
    try:
        result = subprocess.run(
            [ffmpeg, "-nostdin", "-v", "error", "-xerror", "-f", "mp3",
             "-i", str(path), "-map", "0:a:0", "-ac", "1", "-ar", "16000",
             "-f", "s16le", "pipe:1"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False,
        )
        if result.returncode or len(result.stdout) < 3840 or len(result.stdout) % 2:
            return False
        pcm = array.array("h")
        pcm.frombytes(result.stdout)
        if sys.byteorder != "little":
            pcm.byteswap()
        return max(map(abs, pcm), default=0) >= 128
    except (OSError, subprocess.TimeoutExpired):
        return False


async def synth(text: str, path: pathlib.Path, ffmpeg: str) -> bool:
    # A failed download cannot overwrite an older completed recording.
    fd, temporary = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=".mp3", dir=path.parent)
    os.close(fd)
    pending = pathlib.Path(temporary)
    try:
        for attempt in range(ATTEMPTS):
            try:
                await asyncio.wait_for(
                    edge_tts.Communicate(text, VOICE, rate=RATE).save(str(pending)),
                    timeout=REQUEST_TIMEOUT,
                )
                if not await asyncio.to_thread(valid_mp3, pending, ffmpeg):
                    raise ValueError("Downloaded MP3 failed decoding/non-silence validation")
                pending.replace(path)
                return True
            except Exception as exc:
                if getattr(exc, "status", None) in {401, 403} or isinstance(
                    exc, (ssl.SSLError, aiohttp.ClientSSLError)
                ):
                    raise NonRetryableError(
                        f"Access/TLS failure ({type(exc).__name__}); no retry or bypass"
                    ) from exc
                print(f"  {path.stem}: attempt {attempt + 1}/{ATTEMPTS} failed ({type(exc).__name__})", flush=True)
                if attempt + 1 < ATTEMPTS:
                    await asyncio.sleep(2 * (attempt + 1))
        return False
    finally:
        pending.unlink(missing_ok=True)


def save_index(audio: pathlib.Path, wanted: dict[str, str]) -> None:
    content = json.dumps({"voice": VOICE, "files": sorted(wanted)}, indent=1) + "\n"
    target = audio / "index.json"
    if target.exists() and target.read_text("utf-8") == content:
        return
    fd, temporary = tempfile.mkstemp(prefix=".index-", suffix=".json", dir=audio)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(content)
        pathlib.Path(temporary).replace(target)
    finally:
        pathlib.Path(temporary).unlink(missing_ok=True)


async def run(root: pathlib.Path, ffmpeg: str, *, check: bool = False,
              workers: int = WORKERS, time_limit: float = TIME_LIMIT) -> int:
    wanted = load_phrases(root)
    audio = root / "audio"
    ready = {key for key in wanted if valid_mp3(audio / f"{key}.mp3", ffmpeg)}
    print(f"{len(ready)}/{len(wanted)} ready, {len(wanted) - len(ready)} to record", flush=True)
    if check:
        try:
            index = json.loads((audio / "index.json").read_text("utf-8"))
        except (OSError, ValueError):
            index = {}
        complete = ready == set(wanted) and index.get("voice") == VOICE and index.get("files") == sorted(wanted)
        print("Complete Ryan audio verified" if complete else "Ryan audio/index is incomplete", flush=True)
        return 0 if complete else 1

    audio.mkdir(exist_ok=True)
    queue = deque((key, text) for key, text in wanted.items() if key not in ready)
    start = time.monotonic()
    state = {"fails": 0, "made": 0, "stop": ""}

    async def worker():
        while queue and not state["stop"]:
            if state["fails"] >= MAX_FAILS:
                state["stop"] = f"Stopped after {MAX_FAILS} consecutive failed recordings"
                break
            if time.monotonic() - start >= time_limit:
                state["stop"] = "Time limit reached; completed MP3s retained for the next run"
                break
            key, text = queue.popleft()
            try:
                success = await synth(text, audio / f"{key}.mp3", ffmpeg)
            except NonRetryableError as exc:
                state["stop"] = str(exc)
                break
            if success:
                ready.add(key)
                state["made"] += 1
                state["fails"] = 0
                if state["made"] % 50 == 0:
                    print(f"  {len(ready)}/{len(wanted)} ready ({state['made']} new)", flush=True)
            else:
                state["fails"] += 1
                print(f"  failed: {key}", flush=True)

    await asyncio.gather(*(worker() for _ in range(workers)))
    if state["stop"]:
        print(state["stop"], flush=True)
    print(f"{len(ready)}/{len(wanted)} ready ({state['made']} new)", flush=True)
    if ready != set(wanted):
        print("Incomplete: public index unchanged; do not commit/publish this batch", flush=True)
        return 1
    save_index(audio, wanted)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate coverage/index without network or writes")
    parser.add_argument("--ffmpeg", help="Path to the ffmpeg decoder")
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--time-limit", type=float, default=TIME_LIMIT, help="Generation deadline in seconds")
    args = parser.parse_args()
    if not 1 <= args.workers <= 8 or args.time_limit <= 0:
        parser.error("workers must be 1..8 and time-limit must be positive")
    try:
        return asyncio.run(run(ROOT, decoder_path(args.ffmpeg), check=args.check,
                               workers=args.workers, time_limit=args.time_limit))
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
