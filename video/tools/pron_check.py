"""客观检查 TTS 对某个词的读法：把目标词的音频与“候选读法”的参照音频做声学比对。

原理：
1. 用 edge-tts 合成整句，并取 WordBoundary 得到目标词所在的时间段，截出这段音频。
2. 对每个候选读法，合成一句“同一语境、但目标词换成无歧义同音字”的参照句，同样截出对应片段。
3. 提取 MFCC，用 DTW 距离比较目标片段与各参照片段，距离最小的即为 TTS 实际读法。

用法：
    ../.venv/bin/python tools/pron_check.py            # 运行内置用例
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import edge_tts
import librosa
import numpy as np

VOICE = "zh-CN-YunxiNeural"
RATE = "+5%"
SR = 16000


@dataclass
class Case:
    name: str                 # 用例名
    text: str                 # 实际要送 TTS 的句子
    word: str                 # 目标词在句中的写法
    refs: dict[str, str]      # 候选读法 -> 参照句（目标词替换成无歧义同音字，其余不变）
    ref_words: dict[str, str] # 候选读法 -> 参照句中替换后的词


CACHE = Path(__file__).resolve().parent.parent / "build" / "pron-cache"


async def synth(text: str) -> tuple[np.ndarray, list[dict]]:
    """合成并缓存（音频 + WordBoundary），网络不稳时重复运行不必重新请求。"""
    key = hashlib.sha1(f"{VOICE}|{RATE}|{text}".encode()).hexdigest()[:16]
    audio_path, marks_path = CACHE / f"{key}.mp3", CACHE / f"{key}.json"
    if audio_path.exists() and marks_path.exists():
        y, _ = librosa.load(audio_path, sr=SR, mono=True)
        return y, json.loads(marks_path.read_text(encoding="utf-8"))
    buf, marks = io.BytesIO(), []
    for attempt in range(12):
        try:
            buf, marks = io.BytesIO(), []
            async for ch in edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary").stream():
                if ch["type"] == "audio":
                    buf.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    marks.append(ch)
            break
        except Exception as exc:
            if attempt == 11:
                raise
            print(f"  重试({attempt + 1}): {exc}", file=sys.stderr)
            await asyncio.sleep(min(3 * (attempt + 1), 20))
    CACHE.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(buf.getvalue())
    marks_path.write_text(json.dumps(marks, ensure_ascii=False), encoding="utf-8")
    buf.seek(0)
    y, _ = librosa.load(buf, sr=SR, mono=True)
    return y, marks


def locate(text: str, marks: list[dict], word: str) -> tuple[float, float]:
    """在 WordBoundary 序列里找到覆盖目标词的时间段（秒）。边界可能把词与相邻字合并。"""
    start_char = text.index(word)
    end_char = start_char + len(word)
    pos, t0, t1 = 0, None, None
    for m in marks:
        idx = text.find(m["text"], pos)
        if idx < 0:
            continue
        seg_end = idx + len(m["text"])
        if seg_end > start_char and idx < end_char:
            # 被合并的边界只取目标字所占的比例
            span = len(m["text"])
            a = max(start_char, idx) - idx
            b = min(end_char, seg_end) - idx
            st = m["offset"] / 1e7 + m["duration"] / 1e7 * a / span
            en = m["offset"] / 1e7 + m["duration"] / 1e7 * b / span
            t0 = st if t0 is None else min(t0, st)
            t1 = en if t1 is None else max(t1, en)
        pos = idx + len(m["text"])
    if t0 is None:
        raise ValueError(f"找不到词 {word!r} 的边界: {[m['text'] for m in marks]}")
    return t0, t1


def features(y: np.ndarray, t0: float, t1: float) -> np.ndarray:
    seg = y[int(t0 * SR): int(t1 * SR)]
    mfcc = librosa.feature.mfcc(y=seg, sr=SR, n_mfcc=20, n_fft=512, hop_length=160)[1:]
    pitch = librosa.yin(seg, fmin=70, fmax=400, sr=SR, frame_length=512, hop_length=160)
    pitch = np.log(pitch)[None, : mfcc.shape[1]]
    feats = np.vstack([mfcc, (pitch - pitch.mean()) * 30])  # 加入去均值的音高轮廓以区分声调
    return (feats - feats.mean(axis=1, keepdims=True))


def dtw_distance(a: np.ndarray, b: np.ndarray) -> float:
    d, wp = librosa.sequence.dtw(X=a, Y=b, metric="euclidean")
    return float(d[-1, -1] / len(wp))


async def judge(case: Case) -> tuple[str, dict[str, float]]:
    y, marks = await synth(case.text)
    target = features(y, *locate(case.text, marks, case.word))
    scores = {}
    for label, ref_text in case.refs.items():
        ry, rmarks = await synth(ref_text)
        ref = features(ry, *locate(ref_text, rmarks, case.ref_words[label]))
        scores[label] = dtw_distance(target, ref)
    return min(scores, key=scores.get), scores


MARGIN = 10.0   # 最近与次近候选的距离差低于此值时，判定不可靠（实测“加起来”的单音字“加”曾被误判为 jià，差距 7）


def report(results: list[tuple[Case, str, dict[str, float]]]) -> None:
    for case, best, scores in results:
        ranked = sorted(scores.items(), key=lambda kv: kv[1])
        s = "  ".join(f"{k}={v:.1f}" for k, v in ranked)
        sure = len(ranked) < 2 or ranked[1][1] - ranked[0][1] >= MARGIN
        verdict = best if sure else f"{best}?（无法确定）"
        print(f"{case.name:<24} 判定: {verdict:<14} | {s}")


CASES = [
    # “UP”：英文单词 /ʌp/ 与逐字母 U-P
    Case("UP 原样", "常规单UP池", "UP",
         {"英文 up": "常规单阿普池", "字母 U-P": "常规单优批池"},
         {"英文 up": "阿普", "字母 U-P": "优批"}),
    Case("Up 首字母大写", "常规单Up池", "Up",
         {"英文 up": "常规单阿普池", "字母 U-P": "常规单优批池"},
         {"英文 up": "阿普", "字母 U-P": "优批"}),
    Case("up 小写", "常规单up池", "up",
         {"英文 up": "常规单阿普池", "字母 U-P": "常规单优批池"},
         {"英文 up": "阿普", "字母 U-P": "优批"}),
    # 直觉 jué / jiào
    Case("直觉", "这是一种直觉。", "觉",
         {"jué": "这是一种直决。", "jiào": "这是一种直叫。"},
         {"jué": "决", "jiào": "叫"}),
    # 命中 zhòng / zhōng
    Case("命中", "第一次十连就命中了。", "中",
         {"zhòng 四声": "第一次十连就命重了。", "zhōng 一声": "第一次十连就命钟了。"},
         {"zhòng 四声": "重", "zhōng 一声": "钟"}),
    Case("首次命中", "第n次十连首次命中的概率", "中",
         {"zhòng 四声": "第n次十连首次命重的概率", "zhōng 一声": "第n次十连首次命钟的概率"},
         {"zhòng 四声": "重", "zhōng 一声": "钟"}),
    Case("全不中", "九次全不中的概率", "中",
         {"zhòng 四声": "九次全不重的概率", "zhōng 一声": "九次全不钟的概率"},
         {"zhòng 四声": "重", "zhōng 一声": "钟"}),
    Case("没中", "五次十连全都没中。", "中",
         {"zhòng 四声": "五次十连全都没重。", "zhōng 一声": "五次十连全都没钟。"},
         {"zhòng 四声": "重", "zhōng 一声": "钟"}),
    # 第五行 háng / xíng
    Case("第五行", "看表格的第五行。", "行",
         {"háng": "看表格的第五航。", "xíng": "看表格的第五形。"},
         {"háng": "航", "xíng": "形"}),
]


async def main() -> None:
    cases = CASES
    if len(sys.argv) > 1:
        cases = [c for c in CASES if any(k in c.name for k in sys.argv[1:])]
    results = []
    for c in cases:
        best, scores = await judge(c)
        results.append((c, best, scores))
    report(results)


if __name__ == "__main__":
    asyncio.run(main())
