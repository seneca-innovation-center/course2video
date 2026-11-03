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


def assemble_video(
    images: list[Path], audios: list[Path], out_path: Path, *, pause_s: float = 0.6, fps: int = 5
) -> list[float]:
    if len(images) != len(audios):
        raise ValueError(f"{len(images)} images but {len(audios)} audio files")
    if not images:
        raise ValueError("nothing to assemble")
    ff = _ffmpeg()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    track = out_path.with_suffix(".wav")
    durations = build_audio_track(audios, track, pause_s)

    listing = out_path.with_suffix(".frames.txt")
    lines = [concat_line(img) + f"duration {d:.6f}\n" for img, d in zip(images, durations, strict=True)]
    lines.append(concat_line(images[-1]))
    listing.write_text("".join(lines), encoding="utf-8")

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
    listing.unlink()
    track.unlink()
    return durations
