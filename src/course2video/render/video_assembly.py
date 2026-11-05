from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found on PATH")
    return exe


def concat_line(path: Path) -> str:
    return "file '" + str(path.resolve()).replace("'", "'\\''") + "'\n"


def build_audio_track(audios: list[Path], out_wav: Path, pause_s: float) -> list[float]:
    durations = []
    params = None
    with wave.open(str(out_wav), "wb") as out:
        for wav in audios:
            with wave.open(str(wav), "rb") as w:
                p = (w.getnchannels(), w.getsampwidth(), w.getframerate())
                if params is None:
                    params = p
                    out.setnchannels(p[0])
                    out.setsampwidth(p[1])
                    out.setframerate(p[2])
                elif p != params:
                    raise ValueError(f"{wav} has format {p}, expected {params}")
                frames = w.getnframes()
                out.writeframes(w.readframes(frames))
            pad = int(round(pause_s * params[2]))
            out.writeframes(b"\x00" * pad * params[0] * params[1])
            durations.append((frames + pad) / params[2])
    return durations


def _listing(images: list[Path], durations: list[float],
             states: dict[int, list[tuple[Path, float]]]) -> str:
    lines = []
    for i, (img, d) in enumerate(zip(images, durations, strict=True)):
        steps = sorted(states.get(i) or [(img, 0.0)], key=lambda x: x[1])
        for k, (path, start) in enumerate(steps):
            end = steps[k + 1][1] if k + 1 < len(steps) else d
            if end - start > 0:
                lines.append(concat_line(path) + f"duration {end - start:.6f}\n")
    last = (states.get(len(images) - 1) or [(images[-1], 0.0)])[-1][0]
    lines.append(concat_line(last))
    return "".join(lines)


def assemble_video(
    images: list[Path], audios: list[Path], out_path: Path, *, pause_s: float = 0.6, fps: int = 5,
    states: dict[int, list[tuple[Path, float]]] | None = None,
) -> list[float]:
    if len(images) != len(audios):
        raise ValueError(f"{len(images)} images but {len(audios)} audio files")
    if not images:
        raise ValueError("nothing to assemble")
    ff = _ffmpeg()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    track = out_path.with_suffix(".wav")
    listing = out_path.with_suffix(".frames.txt")
    try:
        durations = build_audio_track(audios, track, pause_s)
        listing.write_text(_listing(images, durations, states or {}), encoding="utf-8")
        subprocess.run(
            [ff, "-y", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(listing),
             "-i", str(track),
             "-vf", f"fps={fps},format=yuv420p",
             "-c:v", "libx264", "-tune", "stillimage",
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "1",
             "-t", f"{sum(durations):.3f}",
             "-movflags", "+faststart", str(out_path)],
            check=True,
        )
    finally:
        listing.unlink(missing_ok=True)
        track.unlink(missing_ok=True)
    return durations
