from __future__ import annotations

import logging
from pathlib import Path

from .lecture import Frame
from .subtitles import write_srt
from .video_assembly import assemble_video

log = logging.getLogger(__name__)


def split_parts(frames: list[Frame]) -> list[list[int]]:
    starts = [f.index for f in frames if f.kind == "section"]
    if len(starts) < 2:
        return []
    bounds = [0] + starts[1:] + [len(frames)]
    return [list(range(a, b)) for a, b in zip(bounds, bounds[1:], strict=False)]


def write_part_videos(frames: list[Frame], images: list[Path], audios: list[Path], out_dir: Path,
                      *, pause_s: float, fps: int,
                      states: dict[int, list[tuple[Path, float]]] | None = None) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in list(out_dir.glob("part_*.mp4")) + list(out_dir.glob("part_*.srt")):
        old.unlink()
    parts = []
    groups = split_parts(frames)
    if not groups:
        log.warning("per_part_videos is on, but the lecture has fewer than 2 parts; "
                    "only the full video was written")
    for n, idx in enumerate(groups, start=1):
        video = out_dir / f"part_{n:02d}.mp4"
        local = {k: (states or {})[i] for k, i in enumerate(idx) if i in (states or {})}
        durations = assemble_video([images[i] for i in idx], [audios[i] for i in idx], video,
                                   pause_s=pause_s, fps=fps, states=local)
        speech = [d - pause_s for d in durations]
        write_srt([frames[i].narration for i in idx], durations, speech, video.with_suffix(".srt"))
        heading = next((frames[i].heading for i in idx if frames[i].kind == "section"), "")
        parts.append({"part": n, "title": heading, "video": str(video),
                      "duration_s": round(sum(durations), 2)})
    return parts
