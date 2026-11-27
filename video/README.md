# 视频工程

环境安装和一键复现见 [../README.md](../README.md)。本页说明修改视频时的工作流程，命令都在 `video/` 目录下执行。

## 视频规格

- 2560×1440（2K）、60fps，H.264 + AAC 48kHz，响度 -16 LUFS。
- 字幕渲染进画面，另外导出 `.srt` 供 B 站外挂。
- 配音：edge-tts `zh-CN-YunxiNeural` 男声，语速 +5%。
- 画面上的数字全部由 `../plot.py` 计算，`data.py` 里用断言校验。

## 目录

| 路径 | 内容 |
| --- | --- |
| `narration/part1.yaml`、`part2.yaml` | 两集的旁白稿。`sub` 是字幕文字，`say` 是 TTS 的读法（数字和符号念法），省略时同 `sub`。字幕里的上下标写成 `<sub>n</sub>`、`<sup>9</sup>` |
| `narration/tts/` | 单句配音片段，文件名是“声线 + 语速 + 文本”的哈希。随仓库保存，复现时不需要联网 |
| `tts.py` | 旁白 → `build/audio/<分镜>.wav` 和 `build/timings/<分镜>.json`。已有片段直接复用，只合成改过的句子 |
| `narration/pronounce.yaml` | 全局读音词典，合成前自动替换（如 `UP` → `Up`，`得先` → `嘚先`），只影响配音不影响字幕 |
| `tools/pron_check.py` | 读音客观检查：把目标词的音频与同音字参照做声学比对，判断 TTS 实际读法 |
| `assets/` | 倒计时的滴答声和结束提示音 |
| `data.py` | 画面数字的唯一来源，从 `../plot.py` 导入并在启动时校验 |
| `style.py` | 配色、字体、通用组件；`Narrated` 基类负责字幕和时间轴对齐 |
| `part1/scenes.py` | 上半部分（P1）的分镜，一个分镜一个 `Scene` 类 |
| `part2/scenes.py`、`common.py` | 下半部分（P2）的分镜，以及状态图、面积图等共用组件 |
| `build.py` | 拼接分镜，导出 `out/<名称>.mp4` 和 `.srt`。拼接前检查每个分镜的音画长度 |
| `make.sh` | 一键复现两集 |

## 流程

1. 改旁白稿，然后重新生成配音：
   ```bash
   ../.venv/bin/python tts.py narration/part1.yaml S1_5_Example
   ```
2. 预览渲染（480p15，很快）：
   ```bash
   ../.venv/bin/manim -ql part1/scenes.py S1_5_Example
   ```
   日志里如果出现 `[时间轴警告]`，说明某句的动画超出了这句配音的时长。
3. 终渲（2K，2560×1440 60fps，`-qp`）：
   ```bash
   ../.venv/bin/manim -qp part1/scenes.py
   ```
4. 拼接出片（默认读 1440p60，重编码为 H.264，码率上限 18 Mbps）：
   ```bash
   ../.venv/bin/python build.py P1 --part part1
   ```
   用 480p 预览出片时加 `--q 480p15`。

渲染缓存已在 `style.py` 中关闭。缓存复用的片段会让 Manim 内部时钟和实际帧数逐段错开，累积后音画不同步（曾在一个分镜里错开 0.96 秒）。

## 思考题

旁白稿里给思考题那句加 `quiz: true`，配音会在这句之后自动留 5 秒静音。渲染时会显示“想一想”倒计时圆环，每秒一次滴答声，倒计时结束后才播下一句答案。默认位置在右上角，场景里可以用 `self.countdown(i, where=[x, y, 0])` 指定位置。

## 读音

- `UP`（概率提升）要读成英文单词。edge-tts 遇到全大写的 `UP` 会逐字母读成 U-P，写成 `Up` 才读成单词，所以词典里把所有 `UP` 统一替换成 `Up`。旁白稿和字幕照常写 `UP`。
- 新增多音字规则后，在 `tools/pron_check.py` 的 `CASES` 里加一个用例跑一下：
  ```bash
  ../.venv/bin/python tools/pron_check.py 命中 第五行
  ```
- 2026-11-27 实测（Yunxi 男声）：直觉 jué、命中/全不中/没中 zhòng、第五行 háng、还差 chà、长期 cháng 都读对了；“得先歪”读成了 dé，已改为 děi。

## 配音

默认是 edge-tts 的 `zh-CN-YunxiNeural`（男声，语速 +5%）。其他中文男声有 `zh-CN-YunyangNeural`（新闻播报风格）和 `zh-CN-YunjianNeural`（激昂）。换声音：

```bash
../.venv/bin/python tts.py narration/part1.yaml --voice zh-CN-YunyangNeural
```

换声音后每句时长会变，需要重新渲染。
