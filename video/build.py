"""拼接已渲染的分镜，导出成片与 .srt 字幕。

用法（在 video/ 目录下）：
    ../.venv/bin/python build.py P1 --part part1                 # 按 PARTS 里的分镜顺序，默认 2K（1440p60）
    ../.venv/bin/python build.py P1 --part part1 --q 480p15      # 用 480p 预览渲染
    ../.venv/bin/python build.py sample S1_4_Refine S1_5_Example # 手动指定分镜

Manim 已经在每个分镜里混入了配音（Narrated.setup 里的 add_sound）。
终渲档位（1440p60/1080p60/2160p60）会把视频重编码为高码率 H.264，给 B 站二压留余量；
预览档位直接拷贝视频流。音频统一响度到 -16 LUFS。字幕已渲染进画面，.srt 供 B 站外挂/CC 字幕使用。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"

# 各分 P 的分镜顺序
PARTS = {
    "part1": ["S1_0_Hook", "S1_1_Probability", "S1_2_Faith", "S1_3_Define", "S1_4_Refine",
              "S1_5_Example", "S1_6_Critical", "S1_7_Pools", "S1_8_Answer", "S1_9_Summary"],
    "part2": ["S2_0_Recap", "S2_1_Model", "S2_2_Flow", "S2_3_Expect", "S2_4_Delta", "S2_5_Link2",
              "S2_6_Link4", "S2_7_Link3", "S2_8_Mixed", "S2_9_Grad", "S2_10_Summary"],
}
# 终渲档位的视频码率；不在表里的档位（预览）直接拷贝视频流
BITRATE = {"2160p60": "45M", "1440p60": "18M", "1080p60": "10M"}


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def probe(path: Path) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True).stdout)


def stream_duration(path: Path, kind: str) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", f"{kind}:0", "-show_entries", "stream=duration",
         "-of", "csv=p=0", str(path)], check=True, capture_output=True, text=True).stdout)


def check_sync(clips: list[Path], tol: float = 0.1) -> None:
    """每个分镜的视频流与音频流必须等长，否则拼接后后面的分镜会音画错位。"""
    bad = []
    for c in clips:
        v, a = stream_duration(c, "v"), stream_duration(c, "a")
        if abs(v - a) > tol:
            bad.append(f"  {c.stem}: 视频 {v:.3f}s, 音频 {a:.3f}s, 差 {v - a:+.3f}s")
    if bad:
        raise SystemExit("音画长度不一致，请重新渲染这些分镜：\n" + "\n".join(bad))


def conform(clip: Path) -> Path:
    """把分镜的音频补齐或裁到与视频流完全等长（误差在帧取整的量级），避免拼接后误差累加。"""
    v = stream_duration(clip, "v")
    out = ROOT / "build" / "conformed" / clip.parent.name / clip.name
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip),
                    "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy",
                    "-af", f"apad,atrim=0:{v:.6f}", "-c:a", "pcm_s16le", "-ar", "48000",
                    "-f", "mov", str(out.with_suffix(".mov"))], check=True)
    return out.with_suffix(".mov")


def video_args(quality: str) -> list[str]:
    rate = BITRATE.get(quality)
    if rate is None:
        return ["-c:v", "copy"]
    return ["-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-b:v", rate, "-maxrate", rate, "-bufsize", str(int(rate[:-1]) * 2) + "M", "-g", "120"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--part", choices=sorted(PARTS), help="按分 P 的分镜清单出片")
    ap.add_argument("--q", default="1440p60")
    ap.add_argument("--src", default="scenes", help="media/videos/ 下的脚本名目录")
    args = ap.parse_args()
    if args.part:
        args.scenes = PARTS[args.part]
    if not args.scenes:
        raise SystemExit("需要 --part 或分镜名")

    OUT.mkdir(exist_ok=True)
    video_dir = ROOT / "media" / "videos" / args.src / args.q
    clips = [video_dir / f"{s}.mp4" for s in args.scenes]
    for c in clips:
        if not c.exists():
            raise SystemExit(f"缺少渲染结果：{c}")

    check_sync(clips)
    clips_for_concat = [conform(c) for c in clips]
    concat = OUT / f"{args.name}.concat.txt"
    concat.write_text("".join(f"file '{c}'\n" for c in clips_for_concat), encoding="utf-8")
    mp4 = OUT / f"{args.name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
                    *video_args(args.q), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", str(mp4)], check=True)

    entries, offset = [], 0.0
    for scene, clip in zip(args.scenes, clips):
        data = json.loads((ROOT / "build" / "timings" / f"{scene}.json").read_text(encoding="utf-8"))
        for line in data["lines"]:
            text = re.sub(r"<[^>]+>", "", line["sub"])   # 去掉上下标标记
            entries.append((offset + line["start"], offset + line["end"], text))
        offset += stream_duration(clip, "v")
    srt = OUT / f"{args.name}.srt"
    srt.write_text("\n".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n"
                             for i, (a, b, t) in enumerate(entries, 1)), encoding="utf-8")
    print(f"{mp4}  ({probe(mp4):.1f} 秒)\n{srt}  ({len(entries)} 条)")


if __name__ == "__main__":
    main()
