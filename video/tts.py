"""旁白稿 → 每个分镜一条配音 + 时间轴。

用法（在 video/ 目录下）：
    ../.venv/bin/python tts.py narration/part1.yaml               # 生成全部分镜
    ../.venv/bin/python tts.py narration/part1.yaml S1_5_Example  # 只生成指定分镜
    ../.venv/bin/python tts.py --voices                           # 列出中文男声

产物：
    build/audio/<分镜>.wav           该分镜完整配音（句间留 GAP 秒静音）
    build/timings/<分镜>.json        每句 {sub, start, end}，Manim 场景据此编排
    narration/tts/<hash>.mp3         单句配音片段（随仓库保存），改哪句只重新合成哪句
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import edge_tts
import yaml

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
# 单句配音片段随仓库保存：edge-tts 是在线服务，声线可能随时间变化，保留片段才能逐字节复现
CACHE = ROOT / "narration" / "tts"

VOICE = "zh-CN-YunxiNeural"
RATE = "+5%"
GAP = 0.35          # 句间静音（秒）
LEAD = 0.30         # 分镜开头静音（秒）
SAMPLE_RATE = 48000
QUIZ_PAUSE = 5.2    # 思考题倒计时：5 秒 + 淡入淡出余量


PRONOUNCE = ROOT / "narration" / "pronounce.yaml"


def load_rules() -> list[tuple[re.Pattern, str]]:
    """读取全局读音词典；只有 from 没有 to 的条目是提醒，不做替换。"""
    rules = []
    for r in yaml.safe_load(PRONOUNCE.read_text(encoding="utf-8"))["rules"]:
        if "to" not in r:
            continue
        pat = r["from"] if r.get("regex") else re.escape(r["from"])
        rules.append((re.compile(pat), r["to"]))
    return rules


def spoken(line: dict, rules: list[tuple[re.Pattern, str]]) -> str:
    """一句旁白实际送进 TTS 的文本：say（缺省为去掉标记的 sub），再套用读音词典。"""
    text = line.get("say") or re.sub(r"<[^>]+>", "", line["sub"])
    for pat, to in rules:
        text = pat.sub(to, text)
    return text


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return float(out.strip())


async def synth(text: str, voice: str, rate: str) -> Path:
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16]
    path = CACHE / f"{key}.mp3"
    if not path.exists() or path.stat().st_size == 0:
        tmp = path.with_suffix(".part")
        for attempt in range(12):
            try:
                await edge_tts.Communicate(text, voice, rate=rate).save(str(tmp))
                break
            except Exception as exc:  # 网络抖动时重试
                if attempt == 11:
                    raise
                print(f"  重试({attempt + 1}): {exc}", file=sys.stderr)
                await asyncio.sleep(min(3 * (attempt + 1), 20))
        tmp.rename(path)
    return path


def build_scene(name: str, lines: list[dict], voice: str, rate: str) -> None:
    rules = load_rules()
    texts = [spoken(l, rules) for l in lines]
    clips = [asyncio.run(synth(t, voice, rate)) for t in texts]
    timings, t = [], LEAD
    inputs, filters = [], []
    for i, (line, clip) in enumerate(zip(lines, clips)):
        dur = probe_duration(clip)
        # 思考题（quiz: true）默认在句后留 QUIZ_PAUSE 秒静音给倒计时；也可用 pause 显式指定
        pause = float(line.get("pause", QUIZ_PAUSE if line.get("quiz") else 0))
        entry = {"sub": line["sub"], "say": texts[i], "start": round(t, 3), "end": round(t + dur, 3)}
        if pause:
            entry["pause"] = pause
        if line.get("quiz"):
            entry["quiz"] = True
        timings.append(entry)
        inputs += ["-i", str(clip)]
        filters.append(f"[{i}:a]aresample={SAMPLE_RATE},adelay={int(t * 1000)}:all=1[a{i}]")
        t += dur + GAP + pause
    total = t - GAP + 0.6
    mix = "".join(f"[a{i}]" for i in range(len(clips)))
    filters.append(f"{mix}amix=inputs={len(clips)}:normalize=0,apad,atrim=0:{total:.3f}[out]")

    (BUILD / "audio").mkdir(parents=True, exist_ok=True)
    (BUILD / "timings").mkdir(parents=True, exist_ok=True)
    wav = BUILD / "audio" / f"{name}.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs,
         "-filter_complex", ";".join(filters), "-map", "[out]",
         "-ac", "1", "-ar", str(SAMPLE_RATE), str(wav)],
        check=True,
    )
    payload = {"voice": voice, "rate": rate, "total": round(total, 3), "lines": timings}
    (BUILD / "timings" / f"{name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{name}: {len(lines)} 句, {total:.1f} 秒")


async def list_voices() -> None:
    for v in await edge_tts.list_voices():
        if v["Locale"].startswith("zh-CN") and v["Gender"] == "Male":
            print(v["ShortName"], v.get("VoiceTag", {}).get("VoicePersonalities"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("narration", nargs="?")
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--rate", default=RATE)
    ap.add_argument("--voices", action="store_true")
    args = ap.parse_args()
    if args.voices:
        asyncio.run(list_voices())
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(Path(args.narration).read_text(encoding="utf-8"))
    for name, lines in data.items():
        if args.scenes and name not in args.scenes:
            continue
        build_scene(name, lines, args.voice, args.rate)


if __name__ == "__main__":
    main()
