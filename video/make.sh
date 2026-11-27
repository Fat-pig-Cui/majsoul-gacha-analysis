#!/usr/bin/env bash
# 从仓库内容一键复现两个视频。
#
#   ./make.sh            # 2K（2560×1440 60fps）终版：out/P1.mp4、out/P2.mp4 及 .srt
#   ./make.sh preview    # 480p15 预览：out/P1_480p.mp4、out/P2_480p.mp4
#
# 需要先按 ../README.md 装好环境。配音片段已在 narration/tts/ 里，无需联网。
set -euo pipefail
cd "$(dirname "$0")"

PY=../.venv/bin/python
MANIM=../.venv/bin/manim
if [[ "${1:-}" == "preview" ]]; then
    FLAG=-ql; QUALITY=480p15; SUFFIX=_480p
else
    FLAG=-qp; QUALITY=1440p60; SUFFIX=
fi

# 1. 数值校验（plot.py 与专栏文中的基准值一致）
$PY ../plot.py --verify

# 2. 配音：把单句片段拼成每个分镜的音频，并生成时间轴 build/timings/*.json
$PY tts.py narration/part1.yaml
$PY tts.py narration/part2.yaml

# 3. 渲染分镜
$MANIM $FLAG part1/scenes.py S1_0_Hook S1_1_Probability S1_2_Faith S1_3_Define S1_4_Refine \
    S1_5_Example S1_6_Critical S1_7_Pools S1_8_Answer S1_9_Summary
$MANIM $FLAG part2/scenes.py S2_0_Recap S2_1_Model S2_2_Flow S2_3_Expect S2_4_Delta S2_5_Link2 \
    S2_6_Link4 S2_7_Link3 S2_8_Mixed S2_9_Grad S2_10_Summary

# 4. 拼接出片（含音画长度校验、响度标准化）
$PY build.py "P1$SUFFIX" --part part1 --q "$QUALITY"
$PY build.py "P2$SUFFIX" --part part2 --q "$QUALITY"
