"""下半部分共用的图形组件：状态节点、转移箭头、概率柱、堆叠面积图。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from manim import *  # noqa: E402,F403

from style import BG, DIM, INK, PANEL, STATE, M, T  # noqa: E402


def state_node(label: str, color: str, radius: float = 0.48, size: float = 38) -> VGroup:
    """一个马尔科夫状态：彩色圆圈 + 标签（LaTeX，如 S_0）。"""
    ring = Circle(radius=radius, stroke_color=color, stroke_width=5, fill_color=PANEL, fill_opacity=1)
    tex = M(label, size=size, color=color).move_to(ring)
    return VGroup(ring, tex)


def edge(a: VGroup, b: VGroup, color: str = DIM, angle: float = 0.0, width: float = 3.0, buff: float = 0.06) -> Arrow:
    """状态 a 指向状态 b 的箭头。angle≠0 时为弧线（从上方或下方绕过中间的状态）。"""
    if angle == 0:
        return Arrow(a.get_center(), b.get_center(), buff=a[0].radius + buff, color=color,
                     stroke_width=width, tip_length=0.18, max_tip_length_to_length_ratio=0.2)
    arc = CurvedArrow(a[0].point_at_angle(PI / 2 if angle > 0 else -PI / 2),
                      b[0].point_at_angle(PI / 2 if angle > 0 else -PI / 2),
                      angle=-angle, color=color, stroke_width=width, tip_length=0.18)
    return arc


def self_loop(node: VGroup, color: str = DIM, up: bool = True, width: float = 3.0) -> VMobject:
    """状态自环：留在原状态。"""
    r = node[0].radius
    direction = UP if up else DOWN
    start = node.get_center() + r * (direction * 0.82 + LEFT * 0.57)
    end = node.get_center() + r * (direction * 0.82 + RIGHT * 0.57)
    return CurvedArrow(start, end, angle=-TAU * 0.62 if up else TAU * 0.62, color=color, stroke_width=width,
                       tip_length=0.16)


def edge_label(arrow: VMobject, tex: str, color: str = INK, size: float = 28, side=UP, buff: float = 0.1) -> MathTex:
    lab = M(tex, size=size, color=color)
    if isinstance(arrow, Arrow):
        lab.next_to(arrow.get_center(), side, buff=buff)
    else:
        lab.next_to(arrow.point_from_proportion(0.5), side, buff=buff)
    return lab


def chain(n: int, spacing: float = 2.6, labels: list[str] | None = None, radius: float = 0.48) -> VGroup:
    """一排 n 个状态 S_0 … S_{n-1}，颜色按 STATE。"""
    labels = labels or [f"S_{i}" for i in range(n)]
    nodes = VGroup(*[state_node(labels[i], STATE[i % len(STATE)], radius=radius) for i in range(n)])
    nodes.arrange(RIGHT, buff=spacing - 2 * radius)
    return nodes


def prob_columns(values, colors, width: float = 0.9, max_h: float = 2.6, gap: float = 1.6) -> VGroup:
    """一组概率柱，每根对应一个状态；返回 VGroup(柱, 百分比标签)。"""
    bars, labels = VGroup(), VGroup()
    for i, (v, c) in enumerate(zip(values, colors)):
        bar = Rectangle(width=width, height=max(v * max_h, 1e-3), stroke_width=0, fill_color=c, fill_opacity=0.9)
        bar.move_to([i * gap, 0, 0], aligned_edge=DOWN)
        bars.add(bar)
        labels.add(T(f"{v * 100:.1f}%", 22, c).next_to(bar, UP, buff=0.08))
    return VGroup(bars, labels)


def stacked_area(axes: Axes, dist: list[list[float]], colors, opacity: float = 0.85) -> VGroup:
    """堆叠面积图：dist[N] 为第 N 次十连后各状态概率。从下往上依次堆叠，最下层为最后一个状态（终点）。"""
    n_states = len(dist[0])
    order = list(range(n_states))[::-1]        # 终点状态放在最下面
    layers = VGroup()
    cum = [0.0] * len(dist)
    for s in order:
        lower = cum[:]
        upper = [lower[n] + dist[n][s] for n in range(len(dist))]
        pts = [axes.c2p(n, upper[n]) for n in range(len(dist))] + \
              [axes.c2p(n, lower[n]) for n in range(len(dist) - 1, -1, -1)]
        poly = Polygon(*pts, stroke_width=0, fill_color=colors[s], fill_opacity=opacity)
        layers.add(poly)
        cum = upper
    return layers


def prob_axes(x_max: int = 30, width: float = 10.0, height: float = 4.2, x_step: int = 5) -> tuple[Axes, VGroup]:
    """横轴十连数 N、纵轴概率 0~1 的坐标系。"""
    axes = Axes(x_range=[0, x_max, x_step], y_range=[0, 1, 0.25], x_length=width, y_length=height,
                axis_config={"color": DIM, "stroke_width": 2, "include_tip": False})
    labels = VGroup()
    for x in range(0, x_max + 1, x_step):
        labels.add(T(str(x), 18, DIM).next_to(axes.c2p(x, 0), DOWN, buff=0.12))
    for y in (0.25, 0.5, 0.75, 1.0):
        labels.add(T(f"{int(y * 100)}%", 18, DIM).next_to(axes.c2p(0, y), LEFT, buff=0.12))
    labels.add(T("十连数 N", 20, DIM).next_to(axes.c2p(x_max, 0), DOWN, buff=0.42).align_to(axes.c2p(x_max, 0), RIGHT))
    return axes, labels


def legend(names, colors, size: float = 20) -> VGroup:
    items = VGroup(*[VGroup(Square(0.22, fill_color=c, fill_opacity=0.9, stroke_width=0), M(n, size=size + 6, color=c))
                     .arrange(RIGHT, buff=0.12) for n, c in zip(names, colors)])
    return items.arrange(RIGHT, buff=0.35)


def matrix_tex(rows: list[list[str]], size: float = 30, h_buff: float = 0.9, v_buff: float = 0.6) -> Matrix:
    return Matrix(rows, element_to_mobject=lambda s: MathTex(s, font_size=size, color=INK),
                  h_buff=h_buff, v_buff=v_buff, bracket_config={"color": DIM}, element_alignment_corner=ORIGIN)


__all__ = ["state_node", "edge", "self_loop", "edge_label", "chain", "prob_columns", "stacked_area",
           "prob_axes", "legend", "matrix_tex", "BG"]
