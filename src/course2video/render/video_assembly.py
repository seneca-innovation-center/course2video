from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..tts.base import wav_duration


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found on PATH")
    return exe


def assemble_video(
    images: list[Path], audios: list[Path], out_path: Path, *, pause_s: float = 0.6, fps: int = 2
) -> list[float]:
    if len(images) != len(audios):
        raise ValueError(f"{len(images)} images but {len(audios)} audio files")
    ff = _ffmpeg()
    seg_dir = out_path.parent / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    durations = []
    segments = []
    for i, (img, wav) in enumerate(zip(images, audios, strict=True), start=1):
        dur = wav_duration(wav) + pause_s
        seg = seg_dir / f"seg_{i:03d}.mp4"
        subprocess.run(
            [ff, "-y", "-loglevel", "error",
             "-loop", "1", "-framerate", str(fps), "-i", str(img),
             "-i", str(wav),
             "-af", f"apad=pad_dur={pause_s}", "-t", f"{dur:.3f}",
             "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", str(fps),
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "1",
             str(seg)],
            check=True,
        )
        durations.append(dur)
        segments.append(seg)
    concat = seg_dir / "concat.txt"
    concat.write_text("".join(f"file '{s.resolve()}'\n" for s in segments), encoding="utf-8")
    subprocess.run(
        [ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c", "copy", "-movflags", "+faststart", str(out_path)],
        check=True,
    )
    return durations
