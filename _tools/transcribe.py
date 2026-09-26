# -*- coding: utf-8 -*-
"""Transcribe a video or audio file with faster-whisper, on CPU, without touching the C: drive.

WHY faster-whisper AND NOT openai-whisper: the official package drags in ~2.5 GB of PyTorch,
and this machine's MX350 has 2 GB of VRAM -- the model would not fit, so the GPU would sit idle
while we paid for it in disk. CTranslate2 runs the same weights in int8 on the CPU, roughly 3-4x
faster than the reference implementation, for a ~50 MB install.

WHY THE MODEL CACHE IS PINNED TO THE D: DRIVE: HuggingFace defaults to %USERPROFILE%/.cache,
i.e. C:, which had 3.8 GB free when this was written. `large-v3` alone is ~3 GB. The cache is
redirected below *before* huggingface_hub is imported, because that library resolves its cache
paths at import time -- setting the variable afterwards would silently do nothing.

WHY THE FILE PATH IS ACCEPTED DIRECTLY (no ffmpeg step for the caller): faster-whisper decodes
through PyAV, which reads video containers natively and pulls just the audio stream out. Handing
it an .mp4 works. ffmpeg is still on PATH for the frame-extraction side of the pipeline, which is
a separate concern -- see the contact-sheet recipe in CLAUDE.md.

USAGE
    python _tools/transcribe.py path/to/video.mp4
    python _tools/transcribe.py talk.mp4 --model medium --lang en
    python _tools/transcribe.py playthrough.mp4 --vad     # skips the quiet stretches

Writes <input-stem>.txt / .srt / .json into --out (default: alongside the input).
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Pinned before the import below -- see the module docstring. HF_HOME is the cache root; the
# model itself lands in <HF_HOME>/hub. D: has ~108 GB free against C:'s 3.8 GB.
CACHE_ROOT = Path(__file__).resolve().parent / "models"
CACHE_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(CACHE_ROOT))
# Silences the "unauthenticated requests" banner on every run; we only ever pull public models.
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

from faster_whisper import WhisperModel  # noqa: E402


# `small` is the knee of the curve for this hardware: ~500 MB, and roughly real-time-ish on a
# CPU-bound laptop. `medium` is noticeably better on technical vocabulary at ~3x the cost.
DEFAULT_MODEL = "small"
DEFAULT_COMPUTE = "int8"


def stamp(seconds):
    """Format a segment offset the way a human scrubs to it, not the way SRT wants it."""
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def srt_time(seconds):
    """SRT insists on HH:MM:SS,mmm with a comma -- a period here makes players reject the file."""
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("media", help="video or audio file (anything PyAV can open)")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help=f"tiny|base|small|medium|large-v3 (default: {DEFAULT_MODEL})")
    ap.add_argument("--lang", default=None,
                    help="force a language code (en/zh/...); omit to auto-detect per file")
    ap.add_argument("--task", default="transcribe", choices=["transcribe", "translate"],
                    help="translate renders any language into English, losing the original")
    ap.add_argument("--vad", action="store_true",
                    help="run Silero VAD first and skip silence -- worth it on gameplay footage")
    ap.add_argument("--words", action="store_true", help="per-word timestamps (slower, noisier)")
    ap.add_argument("--out", default=None, help="output directory (default: beside the input)")
    args = ap.parse_args()

    src = Path(args.media)
    if not src.is_file():
        sys.exit(f"no such file: {src}")
    out_dir = Path(args.out) if args.out else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[load] {args.model} on cpu/{DEFAULT_COMPUTE} (cache: {CACHE_ROOT})", flush=True)
    t0 = time.time()
    model = WhisperModel(args.model, device="cpu", compute_type=DEFAULT_COMPUTE)
    print(f"[load] ready in {time.time() - t0:.1f}s", flush=True)

    t0 = time.time()
    segments, info = model.transcribe(
        str(src),
        language=args.lang,
        task=args.task,
        vad_filter=args.vad,
        word_timestamps=args.words,
    )
    # `segments` is a generator: nothing has been decoded yet at this point, and the duration
    # printed here comes from the container header rather than from the audio we have heard.
    print(f"[run ] {info.language} (p={info.language_probability:.2f}), "
          f"{info.duration:.1f}s of audio -- decoding now\n", flush=True)

    rows, lines = [], []
    for seg in segments:
        text = seg.text.strip()
        rows.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": text,
            "words": ([{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3)}
                       for w in seg.words] if args.words and seg.words else None),
        })
        lines.append(text)
        # Printed as they arrive, so a 40-minute video is watchable rather than a black box.
        print(f"  [{stamp(seg.start)}] {text}", flush=True)

    elapsed = time.time() - t0
    speed = info.duration / elapsed if elapsed else 0
    stem = src.stem
    (out_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / f"{stem}.json").write_text(
        json.dumps({"source": src.name, "model": args.model, "language": info.language,
                    "duration": info.duration, "segments": rows}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    with open(out_dir / f"{stem}.srt", "w", encoding="utf-8") as fh:
        for i, r in enumerate(rows, 1):
            fh.write(f"{i}\n{srt_time(r['start'])} --> {srt_time(r['end'])}\n{r['text']}\n\n")

    print(f"\n[done] {len(rows)} segments in {elapsed:.1f}s ({speed:.1f}x realtime)")
    print(f"[done] wrote {stem}.txt / .srt / .json to {out_dir}")


if __name__ == "__main__":
    main()
