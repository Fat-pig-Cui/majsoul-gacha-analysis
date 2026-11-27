# 雀魂卡池抽卡概率与规划详解

两篇专栏和据此制作的两集科普视频（B 站 P1、P2）。

| 内容 | 文件 |
| --- | --- |
| 专栏：基础篇（单目标） | [【雀魂】卡池抽卡概率与规划详解.md](【雀魂】卡池抽卡概率与规划详解.md)，配图在 `pic/` |
| 专栏：进阶篇（多目标、马尔科夫链） | [【雀魂】卡池抽卡概率与规划详解（进阶版）.md](【雀魂】卡池抽卡概率与规划详解（进阶版）.md)，配图在 `pic2/` |
| 计算脚本 | [plot.py](plot.py)：全部模型的唯一实现，专栏数字和视频画面都由它算出 |
| 视频工程 | [video/](video/)：旁白稿、配音、Manim 动画、出片脚本，见 [video/README.md](video/README.md) |

## 计算脚本

```bash
python3 plot.py             # 打印各卡池的信仰变动期望与临界十连数
python3 plot.py --verify    # 校验结果与专栏中的基准值一致
python3 plot.py --plots     # 重绘 pic/ 中的曲线图（需要 matplotlib）
```

## 复现视频

以下在 macOS（Apple Silicon）上验证过，其他系统需要自行替换系统依赖的安装方式。

1. 系统依赖：
   ```bash
   brew install python@3.12 ffmpeg cairo pango pkgconf dvisvgm
   ```
   还需要一份 TeX Live（basic 版即可），再补装 Manim 需要的宏包。用户模式安装不需要 sudo：
   ```bash
   tlmgr --usermode install standalone preview doublestroke relsize setspace rsfs ragged2e microtype physics everysel
   ```
   中文字体用的是 macOS 自带的苹方（PingFang SC）。

2. Python 环境：
   ```bash
   /opt/homebrew/bin/python3.12 -m venv .venv
   ```
   ```bash
   .venv/bin/pip install -r requirements.txt
   ```

3. 一键出片（在仓库根目录执行）：
   ```bash
   video/make.sh preview
   ```
   这是 480p 预览版，几分钟就能完成。2K 终版去掉 `preview`，M4 上约需 30 分钟：
   ```bash
   video/make.sh
   ```
   成片在 `video/out/`。

配音片段已经随仓库保存在 `video/narration/tts/`，复现不需要联网。只有修改旁白后，新句子才会调用 edge-tts 在线合成。

## 目录

```
.
├── plot.py                 计算模型（单目标、多目标马尔科夫链、抽井分布）
├── requirements.txt
├── pic/  pic2/             专栏配图
├── *.md                    两篇专栏
└── video/
    ├── make.sh             一键复现
    ├── narration/          旁白稿、读音词典、单句配音片段
    ├── tts.py              旁白 → 分镜音频 + 时间轴
    ├── data.py             视频画面用到的全部数字（从 plot.py 计算并断言校验）
    ├── style.py            配色、字体、字幕与计时基类、倒计时
    ├── part1/ part2/       两集的分镜（每个分镜一个 Scene 类）
    ├── assets/             倒计时音效
    ├── tools/pron_check.py 多音字读音检查
    └── build.py            拼接出片、导出 .srt
```

渲染和出片的中间产物（`video/media/`、`video/build/`、`video/out/`）都可以重新生成，已在 `.gitignore` 中排除。

## 许可证

- **代码**（`plot.py`、`requirements.txt`、`video/` 下的 `.py` 和 `.sh`）：[MIT](LICENSE)。
- **内容**（两篇专栏、`pic/` 和 `pic2/` 的配图、`video/narration/` 的旁白稿与配音片段、`video/assets/` 的音效）：[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/deed.zh-hans)，可以转载和改编，但需要署名，不得用于商业用途。
- `pic2/imgxx1.png`、`pic2/imgxx2.png` 是 B 站 UP 主“冷暖自知_QvQ”视频的截图，版权归原作者，不在上述许可范围内。

详见 [LICENSE](LICENSE)。
