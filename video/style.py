"""全片共用的配色、字体、字幕与计时工具。"""

from __future__ import annotations

import json
from pathlib import Path

from manim import (
    DOWN, LEFT, PI, RIGHT, TAU, UP, ORIGIN, Arc, Circle, FadeIn, FadeOut, VGroup, Text, MarkupText,
    MathTex, Rectangle, RoundedRectangle, Scene, ValueTracker, always_redraw, config, linear,
)

ROOT = Path(__file__).resolve().parent
TIMINGS = ROOT / "build" / "timings"
ASSETS = ROOT / "assets"
GAP_AFTER_LINE = 0.15   # 句子念完后再起倒计时的缓冲（秒）

# ---------- 画布 ----------
BG = "#16171d"
config.background_color = BG
# 必须关闭缓存：复用缓存片段时 Manim 的内部时钟按名义时长前进，而片段的实际帧数经过取整，
# 两者每段差不到一帧，累积后音画会错开（2026-11-27 在 1-5 实测偏差 0.96 秒）。
config.disable_caching = True

# ---------- 配色 ----------
INK = "#e8e6e3"        # 主文字
DIM = "#8b8d98"        # 次要文字/坐标轴
PANEL = "#23252e"      # 卡片底
GAIN = "#5fd38d"       # 信仰正收益
LOSS = "#ff6b6b"       # 信仰负收益
GOLD = "#f5c451"       # 临界值/强调
BLUE = "#6aa9ff"       # 概率/主对象
PURPLE = "#b48cff"     # 十连
# 马尔科夫状态色，沿用原文配图：S0 红 S1 黄 S2 蓝 S3 绿 S4 白
STATE = ["#ff5a4e", "#f7c142", "#4b8fe8", "#4cbf6b", "#f0f0f0"]

CN_FONT = "PingFang SC"


def T(text: str, size: float = 30, color: str = INK, weight: str = "NORMAL", **kw) -> Text:
    """中文/普通文字。"""
    return Text(text, font=CN_FONT, font_size=size, color=color, weight=weight, **kw)


def M(*tex: str, size: float = 40, color: str = INK, **kw) -> MathTex:
    """数学公式。"""
    return MathTex(*tex, font_size=size, color=color, **kw)


def panel(width: float, height: float, color: str = PANEL, stroke: str | None = None) -> RoundedRectangle:
    return RoundedRectangle(
        width=width, height=height, corner_radius=0.18,
        fill_color=color, fill_opacity=1, stroke_color=stroke or color, stroke_width=2 if stroke else 0,
    )


def chip(content, stroke: str | None = None, pad: float = 0.22, fill: str = PANEL) -> VGroup:
    """带圆角底板的标签。"""
    bg = panel(content.width + 2 * pad, content.height + 1.6 * pad, color=fill, stroke=stroke)
    content.move_to(bg)
    return VGroup(bg, content)


def ten_cards(width: float = 0.85, height: float = 1.2, buff: float = 0.14) -> VGroup:
    """一次辉玉十连：前 9 张为有效抽，最后 1 张为必得的紫礼物。"""
    cards = VGroup()
    for i in range(10):
        gift = i == 9
        cards.add(RoundedRectangle(
            width=width, height=height, corner_radius=0.1,
            fill_color="#3b2c55" if gift else PANEL, fill_opacity=1,
            stroke_color=PURPLE if gift else BLUE, stroke_width=2.5,
        ))
    return cards.arrange(RIGHT, buff=buff)


def e_axes(x_max: int, y_min: float, y_max: float, y_step: float, width: float = 10.0,
           height: float = 5.2, x_step: int = 1):
    """信仰变动期望 E(N) 的坐标系：横轴为给定十连数 N，纵轴为 E。

    返回 (axes, labels)。刻度数字用 Text 手画，避免依赖 LaTeX 的数字渲染。
    """
    from manim import Axes, Line
    axes = Axes(
        x_range=[0, x_max, x_step], y_range=[y_min, y_max, y_step],
        x_length=width, y_length=height,
        axis_config={"color": DIM, "stroke_width": 2, "include_tip": False},
    )
    labels = VGroup()
    for x in range(0, x_max + 1, x_step):
        labels.add(T(str(x), 18, DIM).next_to(axes.c2p(x, y_min), DOWN, buff=0.12))
    y = y_min
    while y <= y_max + 1e-9:
        if abs(y) > 1e-9:
            labels.add(T(f"{y:g}", 18, DIM).next_to(axes.c2p(0, y), LEFT, buff=0.12))
        y += y_step
    zero = Line(axes.c2p(0, 0), axes.c2p(x_max, 0), color=INK, stroke_width=2.5)
    labels.add(T("0", 18, DIM).next_to(axes.c2p(0, 0), LEFT, buff=0.12))
    x_name = T("十连数 N", 20, DIM).next_to(axes.c2p(x_max, y_min), DOWN, buff=0.42)
    x_name.align_to(axes.c2p(x_max, y_min), RIGHT)
    y_name = T("E(N)", 20, DIM).next_to(axes.y_axis.get_top(), UP, buff=0.32)
    return axes, VGroup(labels, zero, x_name, y_name)


# ---------- 字幕 + 计时 ----------
class Narrated(Scene):
    """按配音时间轴编排的场景基类。

    子类设置 ``SCENE_ID``，在 construct 里用 ``self.line(i)`` 切到第 i 句：
    它会先等到第 i 句开始的时刻，再切换字幕。之后的 play 都以这一刻为起点。
    ``self.until(t)`` 等到分镜内的绝对时刻 t。
    """

    SCENE_ID = ""
    SUB_SIZE = 26

    def setup(self):
        data = json.loads((TIMINGS / f"{self.SCENE_ID}.json").read_text(encoding="utf-8"))
        self.timing = data["lines"]
        self.total = data["total"]
        self._sub = None
        self._counted: set[int] = set()
        self.add_sound(str(ROOT / "build" / "audio" / f"{self.SCENE_ID}.wav"))

    # 当前时刻（秒），由 Manim 的渲染器累计
    @property
    def now(self) -> float:
        return self.renderer.time

    def until(self, t: float) -> None:
        dt = t - self.now
        if dt > 1 / config.frame_rate:
            self.wait(dt)

    def start(self, i: int) -> float:
        return self.timing[i]["start"]

    def end(self, i: int) -> float:
        return self.timing[i]["end"]

    def line(self, i: int) -> None:
        if i > 0 and self.timing[i - 1].get("quiz") and (i - 1) not in self._counted:
            self.countdown(i - 1)
        late = self.now - self.start(i)
        if late > 0.1:
            print(f"[时间轴警告] {self.SCENE_ID} 第 {i} 句晚了 {late:.2f}s，前一句动画超出预算")
        self.until(self.start(i))
        self._set_sub(self.timing[i]["sub"])

    def _set_sub(self, text: str) -> None:
        if self._sub is not None:
            self.remove(self._sub)   # remove() 同时清掉 mobjects 与 foreground_mobjects
        if "<" in text:   # 旁白稿里的 <sub>/<sup> 换成大小和偏移可控的 span，Pango 默认的太小太偏
            text = (text.replace("<sub>", '<span size="75%" rise="-3pt">')
                        .replace("<sup>", '<span size="75%" rise="6pt">')
                        .replace("</sub>", "</span>").replace("</sup>", "</span>"))
            label = MarkupText(text, font=CN_FONT, font_size=self.SUB_SIZE, color=INK)
        else:
            label = T(text, size=self.SUB_SIZE, color=INK)
        if label.width > config.frame_width - 1.2:
            label.scale_to_fit_width(config.frame_width - 1.2)
        box = Rectangle(
            width=label.width + 0.5, height=label.height + 0.28,
            fill_color="#000000", fill_opacity=0.55, stroke_width=0,
        )
        sub = VGroup(box, label).to_edge(DOWN, buff=0.22)
        label.move_to(box)
        self._sub = sub
        self.add_foreground_mobject(sub)

    def pause_of(self, i: int) -> float:
        return float(self.timing[i].get("pause", 0))

    def countdown(self, i: int, where=None, radius: float = 0.75) -> None:
        """在第 i 句之后的停顿里显示倒计时（停顿时长来自旁白稿的 pause 字段）。

        先等第 i 句念完，再每秒跳一次数字，同时圆环收缩；结束时淡出。
        ``where`` 为倒计时的中心位置，默认右上角。
        """
        secs = self.pause_of(i)
        if secs <= 0:
            raise ValueError(f"{self.SCENE_ID} 第 {i} 句没有设置 pause，不能放倒计时")
        self._counted.add(i)
        self.until(self.end(i) + GAP_AFTER_LINE)
        center = where if where is not None else [config.frame_width / 2 - 1.2, config.frame_height / 2 - 1.15, 0]
        n = int(secs)          # 每秒一跳；pause 比 n 多出的零头留给淡入淡出
        track = Circle(radius=radius, stroke_color=DIM, stroke_width=6, stroke_opacity=0.35).move_to(center)
        prog = ValueTracker(1.0)
        ring = always_redraw(lambda: Arc(
            radius=radius, start_angle=PI / 2, angle=TAU * max(prog.get_value(), 1e-4),
            stroke_color=GOLD, stroke_width=8,
        ).move_arc_center_to(center))
        hint = T("想一想", 22, DIM).next_to(track, DOWN, buff=0.18)
        num = T(str(n), 64, GOLD, weight="BOLD").move_to(center)
        self.add(track, ring)
        # 每秒一跳：滴答声与数字出现/切换在同一帧开始；圆环全程线性收缩
        t0 = self.now
        self.add_sound(str(ASSETS / "tick.wav"))
        self.play(FadeIn(track), FadeIn(num, scale=1.4), FadeIn(hint), run_time=0.12)
        for k in range(n, 0, -1):
            beat = t0 + (n - k + 1)          # 第 k 个数字持续到这一刻，每个数字恰好 1 秒
            self.play(prog.animate.set_value((k - 1) / n), run_time=max(beat - self.now, 0.2), rate_func=linear)
            if k > 1:
                nxt = T(str(k - 1), 64, GOLD, weight="BOLD").move_to(center)
                self.add_sound(str(ASSETS / "tick.wav"))
                self.play(FadeOut(num, scale=0.7), FadeIn(nxt, scale=1.3), run_time=0.12)
                num = nxt
        print(f"[倒计时] {self.SCENE_ID} 第 {i} 句后：{t0:.2f}s 开始，{self.now:.2f}s 结束")
        self.add_sound(str(ASSETS / "ding.wav"))
        self.play(FadeOut(VGroup(track, num, hint), scale=1.15), run_time=0.25)
        self.remove(ring)

    def finish(self) -> None:
        last = len(self.timing) - 1
        if self.timing[last].get("quiz") and last not in self._counted:
            self.countdown(last)
        self.until(self.total)
        if self._sub is not None:
            self.remove(self._sub)
