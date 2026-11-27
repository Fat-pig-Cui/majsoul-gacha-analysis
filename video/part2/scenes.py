"""下半部分（进阶篇）的分镜。

在 video/ 目录下渲染：
    ../.venv/bin/manim -ql part2/scenes.py S2_0_Recap ...   # 预览
    ../.venv/bin/manim -qp part2/scenes.py                  # 2K 终渲全部分镜
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from manim import *  # noqa: E402,F403

import data as D  # noqa: E402
from common import (  # noqa: E402
    chain, edge, edge_label, legend, matrix_tex, prob_axes, prob_columns, self_loop, stacked_area, state_node,
)
from style import (  # noqa: E402
    BLUE, DIM, GAIN, GOLD, INK, LOSS, PANEL, PURPLE, STATE, M, Narrated, T, chip, e_axes,
)

CTEX = TexTemplateLibrary.ctex


def curve(axes, values, color, radius=0.05, width=3.5):
    path = VMobject(stroke_color=color, stroke_width=width).set_points_as_corners(
        [axes.c2p(n, v) for n, v in enumerate(values)])
    dots = VGroup(*[Dot(axes.c2p(n, v), radius=radius, color=color) for n, v in enumerate(values)])
    return path, dots


def crit_lines(axes, crit, y0, y1, color=GOLD):
    return VGroup(*[DashedLine(axes.c2p(n, y0), axes.c2p(n, y1), color=color, stroke_width=2.5) for n in crit])


# ---------------------------------------------------------------------------
# 2-0 从单目标到状态图
# ---------------------------------------------------------------------------
class S2_0_Recap(Narrated):
    SCENE_ID = "S2_0_Recap"

    def construct(self):
        # 0 上个视频的公式
        self.line(0)
        f = M("E", "=", r"\sum_{n=0}^{N}", "10n", r"\,u_n", "+", "(10N-C)", r"\,v_N", size=50)
        f[3].set_color(GAIN)
        f[6].set_color(LOSS)
        box = SurroundingRectangle(f, color=GOLD, buff=0.22, corner_radius=0.1)
        tag = T("上个视频的结论：单目标", 24, DIM).next_to(box, UP, buff=0.2)
        self.play(FadeIn(tag), Write(f), Create(box), run_time=1.8)

        # 1 分成两支
        self.line(1)
        self.play(VGroup(f, box, tag).animate.scale(0.6).to_edge(UP, buff=0.3), run_time=0.8)
        root = Dot([-5.6, -0.2, 0], radius=0.1, color=INK)
        levels, edges = VGroup(), VGroup()

        def branch(src, x, dy):
            hit = chip(T("抽到", 20, GAIN), stroke=GAIN, pad=0.1).move_to([x, src.get_center()[1] + dy, 0])
            miss = Dot([x, src.get_center()[1] - dy * 0.35, 0], radius=0.09, color=LOSS)
            e1 = Line(src.get_center(), hit.get_left(), color=GAIN, stroke_width=2.5)
            e2 = Line(src.get_center(), miss.get_center(), color=LOSS, stroke_width=2.5)
            return hit, miss, e1, e2

        self.play(FadeIn(root), run_time=0.3)
        h1, m1, a1, b1 = branch(root, -3.6, 1.6)
        self.play(Create(a1), Create(b1), FadeIn(h1), FadeIn(m1), run_time=1.0)

        # 2 继续分下去：树越来越大
        self.line(2)
        src = m1
        hits, misses, es = VGroup(h1), VGroup(m1), VGroup(a1, b1)
        for x in (-1.6, 0.4, 2.4):
            h, m, a, b = branch(src, x, 1.6)
            self.play(Create(a), Create(b), FadeIn(h), FadeIn(m), run_time=0.7)
            hits.add(h); misses.add(m); es.add(a, b)
            src = m
        dots = M(r"\cdots", size=40, color=DIM).next_to(src, RIGHT, buff=0.3)
        self.play(FadeIn(dots), run_time=0.4)

        # 3 所有“没抽到”是同一个状态
        self.line(3)
        self.play(LaggedStart(*[Indicate(m, color=LOSS, scale_factor=1.8) for m in [root, *misses]], lag_ratio=0.15),
                  run_time=1.8)
        miss_t = T("都是：还没拿到目标", 24, LOSS).move_to([-3.2, -1.9, 0])
        self.play(FadeIn(miss_t), run_time=0.6)

        # 4 所有“抽到”也是同一个状态
        self.line(4)
        self.play(LaggedStart(*[Indicate(h, color=GAIN, scale_factor=1.15) for h in hits], lag_ratio=0.15),
                  run_time=1.5)
        hit_t = T("都是：目标到手", 24, GAIN).move_to([4.6, 1.3, 0])
        self.play(FadeIn(hit_t), run_time=0.5)

        # 5 合并：收拢成两个圆圈
        self.line(5)
        s0 = state_node("S_0", STATE[0], radius=0.6, size=44).move_to([-2.2, -0.2, 0])
        s1 = state_node("S_1", STATE[2], radius=0.6, size=44).move_to([2.2, -0.2, 0])
        self.play(ReplacementTransform(VGroup(root, misses), s0), ReplacementTransform(hits, s1),
                  FadeOut(VGroup(es, dots, miss_t, hit_t)), run_time=1.6)
        n0 = T("没获得目标", 22, STATE[0]).next_to(s0, DOWN, buff=0.25)
        n1 = T("获得目标", 22, STATE[2]).next_to(s1, DOWN, buff=0.25)
        e01 = edge(s0, s1, color=INK)
        loop = self_loop(s0, color=INK)
        self.play(GrowArrow(e01), Create(loop), FadeIn(n0), FadeIn(n1), run_time=1.0)

        # 6 马尔科夫性质
        self.line(6)
        prop = chip(T("下一步去哪，只看现在在哪", 28, GOLD), stroke=GOLD, pad=0.2).move_to([0, -2.4, 0])
        self.play(FadeIn(prop, shift=UP * 0.2), run_time=0.8)
        self.play(Indicate(s0, color=GOLD, scale_factor=1.1), run_time=1.0)

        # 7 r_ij
        self.line(7)
        r01 = edge_label(e01, "r_{01}", size=34, buff=0.15)
        r00 = M("r_{00}", size=34).next_to(loop, UP, buff=0.1)
        self.play(FadeIn(r01, shift=DOWN * 0.1), FadeIn(r00, shift=DOWN * 0.1), run_time=1.0)
        meaning = M(r"r_{ij}", size=34, color=GOLD)
        meaning_t = T("：一次十连，从状态 i 到状态 j 的概率", 24)
        mean = VGroup(meaning, meaning_t).arrange(RIGHT, buff=0.1).move_to(prop)
        self.play(ReplacementTransform(prop, mean), run_time=0.8)

        # 8 单目标的 r01、r00
        self.line(8)
        f1 = M(r"r_{01}", "=", "1-(1-p)^9", size=36, color=INK)
        f2 = M(r"r_{00}", "=", "(1-p)^9", size=36, color=INK)
        f3 = M(r"r_{00}+r_{01}=1", size=34, color=DIM)
        fs = VGroup(f1, f2, f3).arrange(RIGHT, buff=0.7).move_to([0, 1.85, 0])
        self.play(LaggedStart(*[Write(x) for x in fs], lag_ratio=0.4), run_time=2.2)

        # 9 状态更多：双 UP 预告
        self.line(9)
        s2 = state_node("S_2", STATE[2], radius=0.6, size=44)
        self.play(FadeOut(VGroup(fs, mean, r01, r00, n0, n1)), run_time=0.5)
        new_s1 = state_node("S_1", STATE[1], radius=0.6, size=44).move_to([0, -0.2, 0])
        s2.move_to([3.4, -0.2, 0])
        self.play(s0.animate.move_to([-3.4, -0.2, 0]), ReplacementTransform(s1, new_s1),
                  FadeOut(e01), FadeOut(loop), run_time=0.9)
        self.play(GrowFromCenter(s2), run_time=0.6)
        nxt = T("常规双 UP · 两个都要", 30, GOLD, weight="BOLD").move_to([0, 1.8, 0])
        self.play(FadeIn(nxt, shift=DOWN * 0.2), run_time=0.7)
        self.finish()


# ---------------------------------------------------------------------------
# 2-1 双 UP 全都要：建模
# ---------------------------------------------------------------------------
class S2_1_Model(Narrated):
    SCENE_ID = "S2_1_Model"

    def construct(self):
        # 0 参数
        self.line(0)
        params = VGroup(T("常规双 UP · 两个都要", 30, GOLD, weight="BOLD"),
                        VGroup(T("每个角色", 22, DIM), M(r"p=1.475\%", size=34, color=BLUE),
                               T("信仰价格", 22, DIM), M("150", size=34, color=LOSS)).arrange(RIGHT, buff=0.2)
                        ).arrange(DOWN, buff=0.2).to_edge(UP, buff=0.35)
        self.play(FadeIn(params, shift=DOWN * 0.2), run_time=1.0)

        # 1 三个状态
        self.line(1)
        nodes = chain(3, spacing=4.4, radius=0.58).move_to([0, 0.15, 0])
        names = VGroup(T("一个都没有", 22, STATE[0]), T("有其中一个", 22, STATE[1]), T("两个都有", 22, STATE[2]))
        for n, nm in zip(nodes, names):
            nm.next_to(n, DOWN, buff=0.25)
        for i in range(3):
            self.play(GrowFromCenter(nodes[i]), FadeIn(names[i]), run_time=0.6)
            self.wait(0.6)

        # 2 只能向右
        self.line(2)
        e01 = edge(nodes[0], nodes[1], color=INK)
        e12 = edge(nodes[1], nodes[2], color=INK)
        e02 = edge(nodes[0], nodes[2], color=INK, angle=-0.9)
        l0 = self_loop(nodes[0], color=DIM)
        l1 = self_loop(nodes[1], color=DIM)
        self.play(FadeOut(names), GrowArrow(e01), GrowArrow(e12), Create(e02), run_time=1.2)
        self.play(Create(l0), Create(l1), run_time=0.8)

        # 3 定义 q_k
        self.line(3)
        q_def = chip(VGroup(M("q_k", size=40, color=GOLD), T("：一次十连里，k 个指定目标一个都不出", 24))
                     .arrange(RIGHT, buff=0.12), stroke=GOLD, pad=0.18).move_to([0, -2.1, 0])
        self.play(FadeIn(q_def, shift=UP * 0.2), run_time=0.9)

        # 4 q_k 的式子
        self.line(4)
        q_f = M("q_k", "=", "(1-k p)^9", size=40)
        q_f[0].set_color(GOLD)
        q_f.next_to(q_def, UP, buff=0.25)
        self.play(Write(q_f), run_time=1.4)
        q_nums = M(rf"q_1\approx{D.DQ1:.3f},\quad q_2\approx{D.DQ2:.3f}", size=30, color=DIM).next_to(q_f, RIGHT, buff=0.5)
        self.play(FadeIn(q_nums), run_time=0.7)
        # q_k 的小卡片收到左下角，腾出画面
        q_card = VGroup(q_f, q_nums)
        self.play(FadeOut(q_def), q_card.animate.scale(0.85).move_to([0, -2.25, 0]), run_time=0.8)

        # 5 S0 留在原地：q2
        self.line(5)
        r00 = M("q_2", size=32, color=STATE[0]).next_to(l0, UP, buff=0.08)
        self.play(Indicate(l0, color=STATE[0]), FadeIn(r00), run_time=1.2)

        # 6 只出 A：韦恩图
        self.line(6)
        venn_c = [2.6, 2.2, 0]
        ca = Circle(radius=0.75, stroke_color=BLUE, stroke_width=3).move_to(venn_c + LEFT * 0.45)
        cb = Circle(radius=0.75, stroke_color=PURPLE, stroke_width=3).move_to(venn_c + RIGHT * 0.45)
        la = T("A 没出", 18, BLUE).next_to(ca, LEFT, buff=0.1)
        lb = T("B 没出", 18, PURPLE).next_to(cb, RIGHT, buff=0.1)
        self.play(FadeOut(params), Create(ca), Create(cb), FadeIn(la), FadeIn(lb), run_time=1.0)
        only_b = Difference(cb, ca, fill_color=PURPLE, fill_opacity=0.55, stroke_width=0)
        inter = Intersection(ca, cb, fill_color=DIM, fill_opacity=0.5, stroke_width=0)
        self.play(FadeIn(only_b), FadeIn(inter), run_time=0.8)
        vf = M("q_1", "-", "q_2", size=34).next_to(VGroup(ca, cb), DOWN, buff=0.15)
        vt = T("B 没出、A 出了", 18, DIM).next_to(vf, DOWN, buff=0.06)
        self.play(Write(vf), FadeIn(vt), run_time=1.0)

        # 7 r01 = 2(q1 − q2)
        self.line(7)
        r01 = M("2(q_1-q_2)", size=32, color=STATE[1]).next_to(e01, DOWN, buff=0.12)
        self.play(TransformFromCopy(vf, r01), run_time=1.2)

        # 8 r02
        self.line(8)
        r02 = M("1-2q_1+q_2", size=32, color=STATE[2]).next_to(e02, DOWN, buff=0.08)
        self.play(FadeOut(VGroup(ca, cb, la, lb, only_b, inter, vf, vt)), Write(r02), run_time=1.4)

        # 9 S1 出发：q1 / 1 − q1
        self.line(9)
        r11 = M("q_1", size=32, color=STATE[1]).next_to(l1, UP, buff=0.08)
        r12 = M("1-q_1", size=32, color=STATE[2]).next_to(e12, UP, buff=0.12)
        self.play(FadeIn(r11), run_time=0.8)
        self.play(FadeIn(r12), run_time=0.8)

        # 10 S2 吸收态
        self.line(10)
        absorb = T("终点：进去就不出来", 22, STATE[2]).next_to(nodes[2], UP, buff=0.3)
        self.play(FadeIn(absorb), Indicate(nodes[2], color=STATE[2]), run_time=1.0)

        # 11 方程组
        self.line(11)
        graph = VGroup(nodes, e01, e12, e02, l0, l1, r00, r01, r02, r11, r12, absorb)
        self.play(FadeOut(q_card), graph.animate.scale(0.7).to_edge(UP, buff=0.2), run_time=1.0)
        sys_tex = M(r"\begin{cases}"
                    r"S_0(N) = r_{00}\,S_0(N-1) \\"
                    r"S_1(N) = r_{01}\,S_0(N-1) + r_{11}\,S_1(N-1) \\"
                    r"S_2(N) = r_{02}\,S_0(N-1) + r_{12}\,S_1(N-1) + S_2(N-1)"
                    r"\end{cases}", size=34).move_to([0, -0.85, 0])
        self.play(Write(sys_tex), run_time=2.6)

        # 12 转移矩阵 R
        self.line(12)
        R = matrix_tex([["q_2", "0", "0"], ["2(q_1-q_2)", "q_1", "0"], ["1-2q_1+q_2", "1-q_1", "1"]],
                       size=32, h_buff=2.0, v_buff=0.7)
        Rl = M("R", "=", size=44)
        Rg = VGroup(Rl, R).arrange(RIGHT, buff=0.2).move_to([0, -0.85, 0])
        self.play(FadeOut(sys_tex, shift=LEFT * 0.3), FadeIn(Rg, shift=LEFT * 0.3), run_time=1.4)
        cols = VGroup(*[SurroundingRectangle(VGroup(*[R.get_rows()[r][c] for r in range(3)]), color=STATE[c],
                                             buff=0.12, corner_radius=0.08) for c in range(3)])
        self.play(LaggedStart(*[Create(c) for c in cols], lag_ratio=0.3), run_time=1.2)
        col_t = T("每一列：从这个状态出发，去各处的概率，加起来是 1", 20, DIM).next_to(Rg, DOWN, buff=0.25)
        self.play(FadeIn(col_t), run_time=0.6)

        # 13 R^N
        self.line(13)
        self.play(FadeOut(cols), FadeOut(col_t), Rg.animate.scale(0.75).shift(LEFT * 3.4), run_time=0.9)
        powf = M(r"\begin{bmatrix}S_0(N)\\S_1(N)\\S_2(N)\end{bmatrix}", "=", "R^N",
                 r"\begin{bmatrix}1\\0\\0\end{bmatrix}", size=38).next_to(Rg, RIGHT, buff=0.8)
        powf[2].set_color(GOLD)
        self.play(Write(powf), run_time=1.8)
        init = T("初始：全部在 S₀", 20, DIM).next_to(powf[3], DOWN, buff=0.15)
        self.play(FadeIn(init), run_time=0.5)
        self.finish()


# ---------------------------------------------------------------------------
# 2-2 概率在流动
# ---------------------------------------------------------------------------
class S2_2_Flow(Narrated):
    SCENE_ID = "S2_2_Flow"

    def construct(self):
        S = D.DUAL_S
        cols = STATE[:3]
        nodes = chain(3, spacing=3.6, radius=0.45).move_to([0, 2.55, 0])
        arrows = VGroup(edge(nodes[0], nodes[1], color=DIM), edge(nodes[1], nodes[2], color=DIM),
                        edge(nodes[0], nodes[2], color=DIM, angle=0.6))
        base_y = -1.9
        xs = [n.get_center()[0] for n in nodes]

        def columns(n):
            g = prob_columns(S[n], cols, width=1.1, max_h=3.0, gap=0)
            for i in range(3):
                g[0][i].move_to([xs[i], base_y, 0], aligned_edge=DOWN)
                g[1][i].next_to(g[0][i], UP, buff=0.08)
            return g

        nlabel = lambda n: T(f"第 {n} 次十连后", 26, GOLD).move_to([-5.6, 0.3, 0])  # noqa: E731
        floor = Line([xs[0] - 1.0, base_y, 0], [xs[2] + 1.0, base_y, 0], color=DIM, stroke_width=2)

        # 0 让概率动起来
        self.line(0)
        self.play(LaggedStart(*[GrowFromCenter(n) for n in nodes], lag_ratio=0.2), Create(arrows), Create(floor),
                  run_time=1.6)

        # 1 初始全在 S0
        self.line(1)
        g = columns(0)
        lab = nlabel(0)
        self.play(GrowFromEdge(g[0][0], DOWN), FadeIn(g[1][0]), FadeIn(lab), run_time=1.0)
        self.add(g)

        # 2 第 1 次十连
        self.line(2)
        g1 = columns(1)
        self.play(Transform(g, g1), Transform(lab, nlabel(1)),
                  *[ShowPassingFlash(a.copy().set_color(GOLD).set_stroke(width=6), time_width=0.6) for a in arrows],
                  run_time=1.4)

        # 3 继续抽：逐次推进到 N = 5
        self.line(3)
        for n in range(2, 5):
            self.play(Transform(g, columns(n)), Transform(lab, nlabel(n)), run_time=0.7)

        # 4 S1 先涨后跌，N=5 左右最高
        self.line(4)
        self.play(Transform(g, columns(5)), Transform(lab, nlabel(5)), run_time=0.7)
        peak = SurroundingRectangle(VGroup(g[0][1], g[1][1]), color=STATE[1], buff=0.12, corner_radius=0.08)
        peak_t = T("峰值 ≈ 一半", 22, STATE[1]).next_to(peak, RIGHT, buff=0.15)
        self.play(Create(peak), FadeIn(peak_t), run_time=0.8)

        # 5 一边接收、一边送出
        self.line(5)
        inflow = Arrow(nodes[0].get_bottom() + DOWN * 0.1, g[1][1].get_top() + UP * 0.3 + LEFT * 0.3,
                       color=STATE[0], stroke_width=4, buff=0.1)
        outflow = Arrow(g[1][1].get_top() + UP * 0.3 + RIGHT * 0.3, nodes[2].get_bottom() + DOWN * 0.1,
                        color=STATE[2], stroke_width=4, buff=0.1)
        self.play(GrowArrow(inflow), run_time=0.7)
        self.play(GrowArrow(outflow), run_time=0.7)

        # 6 到第 30 次
        self.line(6)
        self.play(FadeOut(VGroup(peak, peak_t, inflow, outflow)), run_time=0.4)
        for n in (8, 12, 18, 24, 30):
            self.play(Transform(g, columns(n)), Transform(lab, nlabel(n)), run_time=0.45)
        self.play(Indicate(g[1][2], color=STATE[2]), run_time=0.8)

        # 7 面积图
        self.line(7)
        self.play(FadeOut(VGroup(g, lab, nodes, arrows, floor)), run_time=0.6)
        axes, deco = prob_axes(30, width=10.6, height=4.6)
        VGroup(axes, deco).move_to([0.2, 0.15, 0])
        area = stacked_area(axes, S, cols)
        leg = legend(["S_0", "S_1", "S_2"], cols).to_edge(UP, buff=0.35)
        self.play(Create(axes), FadeIn(deco), FadeIn(leg), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(a, shift=UP * 0.1) for a in area], lag_ratio=0.3), run_time=1.6)
        one = T("三层加起来始终是 100%", 24, INK).move_to(axes.c2p(20, 0.4))
        self.play(FadeIn(one), run_time=0.6)
        self.finish()


# ---------------------------------------------------------------------------
# 2-3 首达概率与 Abel 变换
# ---------------------------------------------------------------------------
class S2_3_Expect(Narrated):
    SCENE_ID = "S2_3_Expect"

    def construct(self):
        # 0 不同状态的信仰花费
        self.line(0)
        nodes = chain(3, spacing=3.4, radius=0.5).move_to([0, 2.3, 0])
        self.play(FadeIn(nodes, lag_ratio=0.2), run_time=1.0)

        # 1 300 / 150 / 0
        self.line(1)
        costs = VGroup(M("-300", size=36, color=LOSS), M("-150", size=36, color=LOSS), M("0", size=36, color=GAIN))
        for c, n in zip(costs, nodes):
            c.next_to(n, DOWN, buff=0.25)
        notes = VGroup(T("兑换两个", 20, DIM), T("兑换一个", 20, DIM), T("不用兑换", 20, DIM))
        for t, c in zip(notes, costs):
            t.next_to(c, DOWN, buff=0.08)
        for i in range(3):
            self.play(FadeIn(costs[i], shift=UP * 0.15), FadeIn(notes[i]), run_time=0.6)
            self.wait(0.5)

        # 2 初版公式
        self.line(2)
        f0 = M(r"E(N)", "=", r"10\sum_{n=1}^{N} n\,", r"S_2(n)", "+", r"(10N-150)\,S_1(N)", "+",
               r"(10N-300)\,S_0(N)", size=36).move_to([0, -0.9, 0])
        f0[3].set_color(STATE[2])
        self.play(Write(f0), run_time=2.4)

        # 3 真的对吗？
        self.line(3)
        q = T("？", 64, GOLD, weight="BOLD").next_to(f0[3], UP, buff=0.15)
        self.play(FadeIn(q, scale=1.6), Indicate(f0[3], color=LOSS), run_time=1.0)

        # 4 坑：N 次以内 vs 恰好第 n 次
        self.line(4)
        wrong = T("N 次以内到达 S₂：抽到后还在继续算", 24, LOSS).next_to(f0, DOWN, buff=0.4)
        self.play(FadeIn(wrong), run_time=0.8)

        # 5 首达概率
        self.line(5)
        right = T("恰好在第 n 次到达 S₂：首达概率", 24, GAIN).move_to(wrong)
        self.play(ReplacementTransform(wrong, right), FadeOut(q), run_time=0.9)

        # 6 吸收态：当次减上次。画 S2(n) 的阶梯
        self.line(6)
        self.play(FadeOut(VGroup(costs, notes, nodes, f0, right)), run_time=0.6)
        Nshow = 6
        S2v = [D.DUAL_S[n][2] for n in range(Nshow + 1)]
        ax = Axes(x_range=[0, Nshow + 1, 1], y_range=[0, 0.35, 0.1], x_length=6.4, y_length=4.0,
                  axis_config={"color": DIM, "stroke_width": 2, "include_tip": False}).move_to([-2.6, -0.1, 0])
        xl = VGroup(*[T(str(i), 18, DIM).next_to(ax.c2p(i, 0), DOWN, buff=0.1) for i in range(Nshow + 1)])
        yname = M("S_2(n)", size=30, color=STATE[2]).next_to(ax.c2p(0, 0.35), UP, buff=0.1)
        stairs = VGroup()
        for n in range(1, Nshow + 1):
            stairs.add(Line(ax.c2p(n - 1, S2v[n - 1]), ax.c2p(n, S2v[n - 1]), color=STATE[2], stroke_width=3))
            stairs.add(Line(ax.c2p(n, S2v[n - 1]), ax.c2p(n, S2v[n]), color=STATE[2], stroke_width=3))
        self.play(Create(ax), FadeIn(xl), FadeIn(yname), run_time=0.8)
        self.play(Create(stairs), run_time=1.4)
        risers = VGroup(*[Line(ax.c2p(n, S2v[n - 1]), ax.c2p(n, S2v[n]), color=GOLD, stroke_width=6)
                          for n in range(1, Nshow + 1)])
        first = M(r"S_2(n)-S_2(n-1)", size=32, color=GOLD).move_to([3.4, 1.6, 0])
        ft = T("台阶高度 = 恰好第 n 次到达", 22, GOLD).next_to(first, DOWN, buff=0.15)
        self.play(LaggedStart(*[Create(r) for r in risers], lag_ratio=0.2), Write(first), FadeIn(ft), run_time=1.6)

        # 7 第一项：n × 台阶高度
        self.line(7)
        term = M(r"10\sum_{n=1}^{N} n\,[S_2(n)-S_2(n-1)]", size=34).move_to([3.4, 0.0, 0])
        self.play(Write(term), run_time=1.6)

        # 8 每级台阶横拉出长度 n 的细条
        self.line(8)
        strips = VGroup()
        for n in range(1, Nshow + 1):
            y0, y1 = S2v[n - 1], S2v[n]
            strips.add(Polygon(ax.c2p(0, y0), ax.c2p(n, y0), ax.c2p(n, y1), ax.c2p(0, y1),
                               stroke_width=1, stroke_color=GOLD, fill_color=GOLD, fill_opacity=0.35))
        self.play(LaggedStart(*[GrowFromEdge(s, RIGHT) for s in strips], lag_ratio=0.25), run_time=2.2)
        widths = VGroup(*[T(f"×{n}", 16, GOLD).next_to(strips[n - 1], RIGHT, buff=0.05) for n in (4, 5, 6)])
        self.play(FadeIn(widths), run_time=0.5)

        # 9 大矩形 − 台阶下方面积
        self.line(9)
        big = Polygon(ax.c2p(0, 0), ax.c2p(Nshow, 0), ax.c2p(Nshow, S2v[Nshow]), ax.c2p(0, S2v[Nshow]),
                      stroke_color=INK, stroke_width=2.5, fill_opacity=0)
        under = VGroup()
        for n in range(1, Nshow + 1):
            under.add(Polygon(ax.c2p(n - 1, 0), ax.c2p(n, 0), ax.c2p(n, S2v[n - 1]), ax.c2p(n - 1, S2v[n - 1]),
                              stroke_width=0, fill_color=STATE[2], fill_opacity=0.3))
        self.play(FadeOut(widths), Create(big), run_time=0.8)
        self.play(FadeIn(under, lag_ratio=0.15), run_time=1.2)
        tb = VGroup(T("大矩形", 20, INK), M(r"N\cdot S_2(N)", size=28)).arrange(RIGHT, buff=0.12)
        tu = VGroup(T("台阶下方", 20, STATE[2]), M(r"\sum_{n=0}^{N-1} S_2(n)", size=28, color=STATE[2])).arrange(RIGHT, buff=0.12)
        VGroup(tb, tu).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.4, -1.6, 0])
        self.play(FadeIn(tb), FadeIn(tu), run_time=0.9)

        # 10 Abel 变换
        self.line(10)
        abel = M(r"\sum_{n=1}^{N} n\,[S_2(n)-S_2(n-1)]", "=", r"N\cdot S_2(N)", "-", r"\sum_{n=0}^{N-1} S_2(n)",
                 size=34)
        abel.scale_to_fit_width(6.0).move_to([3.75, -1.75, 0])
        self.play(FadeOut(VGroup(tb, tu)), Write(abel), run_time=1.8)
        abel_t = T("分部求和（Abel 变换）", 22, GOLD).next_to(abel, UP, buff=0.18)
        self.play(FadeIn(abel_t), run_time=0.5)

        # 11 最终公式
        self.line(11)
        self.play(FadeOut(VGroup(ax, xl, yname, stairs, risers, strips, big, under, first, ft, term, abel_t)),
                  abel.animate.scale(0.8).to_edge(UP, buff=0.4), run_time=0.9)
        final = M(r"E(N)=10\Big[", r"N\,S_2(N)-\sum_{n=0}^{N-1}S_2(n)", "+", r"(N-15)\,S_1(N)", "+",
                  r"(N-30)\,S_0(N)", r"\Big]", size=40)
        final[1].set_color(STATE[2])
        final[3].set_color(STATE[1])
        final[5].set_color(STATE[0])
        final.move_to([0, 0.6, 0])
        self.play(Write(final), run_time=2.0)
        fbox = SurroundingRectangle(final, color=GOLD, buff=0.2, corner_radius=0.1)
        self.play(Create(fbox), run_time=0.6)

        # 12 数值：−0.41 / +14.03
        self.line(12)
        self.play(FadeOut(abel), VGroup(final, fbox).animate.scale(0.62).to_edge(UP, buff=0.25), run_time=0.8)
        axes, deco = e_axes(30, -300, 120, 60, width=10.4, height=3.6, x_step=5)
        VGroup(axes, deco).move_to([0.2, -0.5, 0])
        path, dots = curve(axes, D.DUAL_E, BLUE)
        self.play(Create(axes), FadeIn(deco), run_time=0.7)
        self.play(Create(path), FadeIn(dots, lag_ratio=0.03), run_time=1.6)
        l10 = M(f"{D.DUAL_E[10]:.2f}", size=30, color=LOSS).next_to(dots[10], UL, buff=0.4)
        l11 = M(f"+{D.DUAL_E[11]:.2f}", size=30, color=GAIN).next_to(dots[11], DR, buff=0.4)
        self.play(dots[10].animate.scale(1.8).set_color(LOSS), FadeIn(l10), run_time=0.6)
        self.play(dots[11].animate.scale(1.8).set_color(GAIN), FadeIn(l11), run_time=0.6)

        # 13 临界 10 / 11
        self.line(13)
        lines = crit_lines(axes, (10, 11), -300, 120)
        crit = chip(T("临界十连数：10 和 11", 28, GOLD, weight="BOLD"), stroke=GOLD, pad=0.18).move_to(axes.c2p(21, -150))
        self.play(Create(lines), FadeIn(crit, scale=0.9), run_time=1.0)
        self.finish()


# ---------------------------------------------------------------------------
# 2-4 ΔE 的疑问
# ---------------------------------------------------------------------------
class S2_4_Delta(Narrated):
    SCENE_ID = "S2_4_Delta"
    COL_X = 4.75          # 右侧信息栏的中心 x

    def bars(self, axes, values, color, width=0.36):
        g = VGroup()
        for n, v in enumerate(values):
            top, base = axes.c2p(n + 0.5, v), axes.c2p(n + 0.5, 0)
            g.add(Rectangle(width=width, height=max(top[1] - base[1], 1e-3), stroke_width=0, fill_color=color,
                            fill_opacity=0.85).move_to(base, aligned_edge=DOWN))
        return g

    def col(self, mob, y):
        """把 mob 左对齐放进右侧信息栏，顶边在 y。"""
        mob.move_to([self.COL_X, 0, 0]).align_to([self.COL_X - 2.1, 0, 0], LEFT).align_to([0, y, 0], UP)
        return mob

    def construct(self):
        # 0 E 曲线回顾
        self.line(0)
        axes, deco = e_axes(30, -300, 120, 60, width=10.4, height=4.6, x_step=5)
        VGroup(axes, deco).move_to([0.2, 0.2, 0])
        path, dots = curve(axes, D.DUAL_E, BLUE)
        lines = crit_lines(axes, (10, 11), -300, 120)
        self.play(Create(axes), FadeIn(deco), Create(path), FadeIn(dots), Create(lines), run_time=1.6)

        # 1 ΔE 定义：相邻两点的高度差
        self.line(1)
        n0 = 4
        a, b = axes.c2p(n0, D.DUAL_E[n0]), axes.c2p(n0 + 1, D.DUAL_E[n0 + 1])
        run = DashedLine(a, [b[0], a[1], 0], color=DIM)
        rise = Line([b[0], a[1], 0], b, color=GOLD, stroke_width=6)
        de_t = M(r"\Delta E(N)=E(N+1)-E(N)", size=34, color=GOLD).move_to([0, 3.4, 0])
        self.play(Create(run), Create(rise), Write(de_t), run_time=1.4)

        # 2 ΔE 与 10 比较。换成 ΔE 柱状图（左侧），右侧留作信息栏
        self.line(2)
        dax = Axes(x_range=[0, 16, 1], y_range=[0, 50, 10], x_length=8.2, y_length=4.6,
                   axis_config={"color": DIM, "stroke_width": 2, "include_tip": False}).move_to([-2.2, -0.15, 0])
        dxl = VGroup(*[T(str(i), 16, DIM).next_to(dax.c2p(i + 0.5, 0), DOWN, buff=0.1) for i in range(16)])
        dyl = VGroup(*[T(str(v), 16, DIM).next_to(dax.c2p(0, v), LEFT, buff=0.1) for v in range(10, 51, 10)])
        dname = T("N（从 N 到 N+1 的那次十连）", 18, DIM).next_to(dxl, DOWN, buff=0.1)
        ten = DashedLine(dax.c2p(0, 10), dax.c2p(16, 10), color=LOSS, stroke_width=3)
        ten_t = T("成本 10", 20, LOSS).next_to(dax.c2p(16, 10), UP, buff=0.08).align_to(dax.c2p(16, 10), RIGHT)
        self.play(FadeOut(VGroup(axes, deco, path, dots, lines, run, rise)),
                  de_t.animate.scale(0.85).move_to([-2.2, 3.35, 0]), run_time=0.6)
        self.play(Create(dax), FadeIn(dxl), FadeIn(dyl), FadeIn(dname), run_time=0.7)
        self.play(Create(ten), FadeIn(ten_t), run_time=0.6)
        worth = self.col(VGroup(T("ΔE > 10", 26, GAIN, weight="BOLD"), T("多抽这一次值得", 22, GAIN))
                         .arrange(DOWN, aligned_edge=LEFT, buff=0.1), 2.6)
        self.play(FadeIn(worth), run_time=0.5)

        # 3 单目标的 ΔE
        self.line(3)
        single = self.bars(dax, D.SINGLE_DE[:15], DIM)
        self.play(LaggedStart(*[GrowFromEdge(r, DOWN) for r in single], lag_ratio=0.12), run_time=1.6)
        tag1 = self.col(T("单目标（常规单 UP）", 24, DIM), 1.3)
        self.play(FadeIn(tag1), run_time=0.4)

        # 4 单目标：在临界 5/6 附近跌破 10
        self.line(4)
        cross = SurroundingRectangle(VGroup(single[5], single[6]), color=GOLD, buff=0.06)
        cross_t = T("临界 5 / 6", 20, GOLD).next_to(cross, UP, buff=0.1)
        self.play(Create(cross), FadeIn(cross_t), run_time=0.9)

        # 5 双目标：E 在 10/11 转正，ΔE 到 13/14 才跌破
        self.line(5)
        dual = self.bars(dax, D.DUAL_DE[:16], BLUE)
        tag2 = self.col(T("双目标（常规双 UP 全都要）", 24, BLUE), 1.3)
        self.play(FadeOut(VGroup(single, cross, cross_t, worth)), ReplacementTransform(tag1, tag2), run_time=0.5)
        self.play(LaggedStart(*[GrowFromEdge(r, DOWN) for r in dual], lag_ratio=0.1), run_time=1.6)
        eband = DashedLine(dax.c2p(10.5, 0), dax.c2p(10.5, 50), color=GOLD, stroke_width=2.5)
        et = T("E 转正", 20, GOLD).next_to(dax.c2p(10.5, 50), LEFT, buff=0.1)
        dband = DashedLine(dax.c2p(13, 0), dax.c2p(13, 50), color=LOSS, stroke_width=2.5)
        dt = T("ΔE 跌破 10", 20, LOSS).next_to(dax.c2p(13, 50), RIGHT, buff=0.1)
        self.play(Create(eband), FadeIn(et), run_time=0.6)
        self.play(Create(dband), FadeIn(dt), run_time=0.6)

        # 6 第一个问题
        self.line(6)
        q1 = self.col(chip(T("问题一：为什么会这样？", 24, GOLD), stroke=GOLD, pad=0.14), 0.6)
        self.play(FadeIn(q1, shift=LEFT * 0.2), run_time=0.7)

        # 7 拆成 S0 部分 + S1 部分
        self.line(7)
        b1, b0 = VGroup(), VGroup()
        for n in range(16):
            base = dax.c2p(n + 0.5, 0)
            h1 = dax.c2p(n + 0.5, D.B1[n])[1] - base[1]
            h0 = dax.c2p(n + 0.5, D.B1[n] + D.B0[n])[1] - dax.c2p(n + 0.5, D.B1[n])[1]
            r1 = Rectangle(width=0.36, height=max(h1, 1e-3), stroke_width=0, fill_color=STATE[1], fill_opacity=0.9)
            r1.move_to(base, aligned_edge=DOWN)
            r0 = Rectangle(width=0.36, height=max(h0, 1e-3), stroke_width=0, fill_color=STATE[0], fill_opacity=0.9)
            r0.next_to(r1, UP, buff=0)
            b1.add(r1)
            b0.add(r0)
        dec = M(r"\Delta E=", r"S_0(N)\cdot 47.55", "+", r"S_1(N)\cdot 28.78", size=30)
        dec[1].set_color(STATE[0])
        dec[3].set_color(STATE[1])
        dec.scale_to_fit_width(3.9)
        self.col(dec, 2.75)
        tag2.generate_target()
        self.col(tag2.target, 3.45)
        self.play(FadeOut(q1), ReplacementTransform(dual, VGroup(b0, b1)), MoveToTarget(tag2), run_time=1.4)
        self.play(Write(dec), run_time=1.2)

        # 8 S0 这部分衰减得快
        self.line(8)
        f0 = self.col(VGroup(T("停在 S₀ 的概率", 22, STATE[0]), M(r"\times 0.764", size=30, color=STATE[0]),
                             T("/ 次", 20, DIM)).arrange(RIGHT, buff=0.12), 1.85)
        self.play(FadeIn(f0), LaggedStart(*[Indicate(r, color=STATE[0], scale_factor=1.15) for r in b0[:8]],
                                          lag_ratio=0.1), run_time=1.6)

        # 9 S1 衰减得慢：12.5% 机会补齐
        self.line(9)
        f1 = self.col(VGroup(T("停在 S₁ 的概率", 22, STATE[1]), M(r"\times 0.875", size=30, color=STATE[1]),
                             T("/ 次", 20, DIM)).arrange(RIGHT, buff=0.12), 1.3)
        self.play(FadeIn(f1), LaggedStart(*[Indicate(r, color=STATE[1], scale_factor=1.1) for r in b1[8:14]],
                                          lag_ratio=0.1), run_time=1.6)
        save = self.col(VGroup(T("只差一个：每次 12.5% 补齐", 20, STATE[1]), T("一次省下 150 信仰", 20, STATE[1]))
                        .arrange(DOWN, aligned_edge=LEFT, buff=0.06), 0.8)
        self.play(FadeIn(save), run_time=0.6)

        # 10 S1 是缓冲池：往后延长约 3 次
        self.line(10)
        ext = DoubleArrow(dax.c2p(10.5, 30), dax.c2p(13, 30), color=GOLD, buff=0, stroke_width=4, tip_length=0.16)
        ext_t = T("≈ 3 次十连", 22, GOLD).next_to(ext, UP, buff=0.08)
        self.play(GrowFromCenter(ext), FadeIn(ext_t), run_time=0.9)
        pool = self.col(chip(T("S₁ = 缓冲池", 28, STATE[1], weight="BOLD"), stroke=STATE[1], pad=0.14), 0.05)
        self.play(FadeIn(pool, scale=1.2), run_time=0.6)

        # 11 第二个问题（思考题）：替换信息栏下半部分
        self.line(11)
        q2 = chip(VGroup(T("问题二：实际抽卡时，", 24, GOLD), T("临界值取哪一组？", 24, GOLD),
                         VGroup(chip(T("10 和 11", 24), stroke=GOLD, pad=0.12),
                                chip(T("13 和 14", 24), stroke=LOSS, pad=0.12)).arrange(RIGHT, buff=0.4)
                         ).arrange(DOWN, aligned_edge=LEFT, buff=0.15), stroke=GOLD, pad=0.2)
        self.col(q2, 1.95)
        self.play(FadeOut(VGroup(f0, f1, save, pool)), FadeIn(q2, scale=0.92), run_time=0.9)
        self.countdown(11, where=[self.COL_X, -1.45, 0], radius=0.55)

        # 12 答案 10 和 11
        self.line(12)
        opts = q2[1][2]
        pick = SurroundingRectangle(opts[0], color=GAIN, buff=0.06, corner_radius=0.08, stroke_width=5)
        self.play(Create(pick), opts[1].animate.set_opacity(0.3), run_time=0.8)
        goal = self.col(VGroup(T("目标：长期信仰不涨不跌", 22, GAIN), T("→ 看 E ≈ 0", 22, GAIN))
                        .arrange(DOWN, aligned_edge=LEFT, buff=0.08), -0.35)
        self.play(FadeIn(goal), run_time=0.7)

        # 13 两个标准在单目标里重合，多目标里要看 E
        self.line(13)
        rule = self.col(chip(VGroup(T("以 E 由负转正为准", 24, GOLD, weight="BOLD"),
                                    T("而不是 ΔE 跌破 10", 22, DIM)).arrange(DOWN, aligned_edge=LEFT, buff=0.08),
                             stroke=GOLD, pad=0.16), -1.4)
        self.play(FadeIn(rule, shift=UP * 0.15), Indicate(eband, color=GOLD), run_time=1.0)
        self.finish()


# ---------------------------------------------------------------------------
# 共用：画一条 E(N) 曲线并标出临界十连数
# ---------------------------------------------------------------------------
def e_panel(values, y_min, y_max, y_step, color=BLUE, width=10.4, height=4.0, center=(0.2, -0.4)):
    axes, deco = e_axes(30, y_min, y_max, y_step, width=width, height=height, x_step=5)
    VGroup(axes, deco).move_to([center[0], center[1], 0])
    path, dots = curve(axes, values, color)
    return axes, deco, path, dots


def crit_chip(text, axes, x, y):
    return chip(T(text, 28, GOLD, weight="BOLD"), stroke=GOLD, pad=0.18).move_to(axes.c2p(x, y))


# ---------------------------------------------------------------------------
# 2-5 联动 4UP：只要特定两个
# ---------------------------------------------------------------------------
class S2_5_Link2(Narrated):
    SCENE_ID = "S2_5_Link2"

    def construct(self):
        # 0 套用模板
        self.line(0)
        nodes = chain(3, spacing=3.6, radius=0.45).move_to([0, 2.5, 0])
        arrows = VGroup(edge(nodes[0], nodes[1]), edge(nodes[1], nodes[2]), edge(nodes[0], nodes[2], angle=0.6))
        self.play(FadeIn(nodes, lag_ratio=0.2), Create(arrows), run_time=1.2)

        # 1 联动特定两个
        self.line(1)
        title = T("联动 4UP · 只要特定两个", 30, GOLD, weight="BOLD").to_edge(UP, buff=0.25)
        self.play(VGroup(nodes, arrows).animate.shift(DOWN * 0.55), FadeIn(title, shift=DOWN * 0.2), run_time=0.9)

        # 2 概率减半
        self.line(2)
        pcmp = VGroup(M(r"p=1.475\%", size=34, color=DIM), M(r"\rightarrow", size=34, color=DIM),
                      M(r"0.7375\%", size=40, color=BLUE)).arrange(RIGHT, buff=0.25).move_to([0, 0.75, 0])
        self.play(FadeIn(pcmp[0]), run_time=0.5)
        self.play(GrowFromCenter(pcmp[1]), FadeIn(pcmp[2], shift=LEFT * 0.2), run_time=0.8)
        half = T("减半", 24, BLUE).next_to(pcmp[1], DOWN, buff=0.1)
        self.play(FadeIn(half), run_time=0.4)

        # 3 概率流得更慢：面积图对比
        self.line(3)
        self.play(FadeOut(VGroup(nodes, arrows, pcmp, half)), run_time=0.5)
        axes, deco = prob_axes(30, width=10.4, height=4.0)
        VGroup(axes, deco).move_to([0.2, -0.25, 0])
        area = stacked_area(axes, D.LINK2_S, STATE[:3])
        leg = legend(["S_0", "S_1", "S_2"], STATE[:3]).next_to(title, DOWN, buff=0.2)
        self.play(Create(axes), FadeIn(deco), FadeIn(leg), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(a, shift=UP * 0.1) for a in area], lag_ratio=0.3), run_time=1.4)
        gap = 1 - D.LINK2_S[30][2]
        br = BraceBetweenPoints(axes.c2p(30, 1), axes.c2p(30, D.LINK2_S[30][2]), direction=RIGHT, color=INK)
        br_t = T(f"{gap * 100:.0f}% 还没拿齐", 20, INK).next_to(br, RIGHT, buff=0.08)
        if br_t.get_right()[0] > 7.0:
            br_t.next_to(br, LEFT, buff=0.08)
        self.play(GrowFromCenter(br), FadeIn(br_t), run_time=0.8)

        # 4 临界 13 / 14
        self.line(4)
        self.play(FadeOut(VGroup(axes, deco, area, leg, br, br_t)), run_time=0.5)
        ax, dc, path, dots = e_panel(D.LINK2_E, -300, 150, 50)
        ghost, _ = curve(ax, D.DUAL_E, DIM, width=2)
        ghost.set_stroke(opacity=0.5)
        ghost_t = T("常规双 UP", 18, DIM).next_to(ax.c2p(30, D.DUAL_E[30]), UP, buff=0.08).shift(LEFT * 0.4)
        self.play(Create(ax), FadeIn(dc), Create(ghost), FadeIn(ghost_t), run_time=0.8)
        self.play(Create(path), FadeIn(dots), run_time=1.0)
        self.play(Create(crit_lines(ax, (13, 14), -300, 150)), FadeIn(crit_chip("临界十连数：13 和 14", ax, 22, -180)),
                  run_time=0.8)
        self.finish()


# ---------------------------------------------------------------------------
# 2-6 联动 4UP：全都要 + 抽井彩蛋
# ---------------------------------------------------------------------------
class S2_6_Link4(Narrated):
    SCENE_ID = "S2_6_Link4"

    def construct(self):
        # 0 五个状态
        self.line(0)
        title = T("联动 4UP · 全都要", 30, GOLD, weight="BOLD").to_edge(UP, buff=0.25)
        nodes = chain(5, spacing=2.7, radius=0.42).move_to([0, 0.9, 0])
        self.play(FadeIn(title), LaggedStart(*[GrowFromCenter(n) for n in nodes[:3]], lag_ratio=0.2), run_time=1.0)
        self.play(LaggedStart(*[GrowFromCenter(n) for n in nodes[3:]], lag_ratio=0.3), run_time=0.9)

        # 1 箭头很多：任意 i → j (i < j)
        self.line(1)
        arrows = VGroup()
        for i in range(5):
            for j in range(i + 1, 5):
                if j == i + 1:
                    arrows.add(edge(nodes[i], nodes[j], color=DIM, width=2.5))
                else:
                    bend = 0.35 + 0.18 * (j - i)
                    arrows.add(edge(nodes[i], nodes[j], color=DIM, width=2, angle=bend if (i + j) % 2 else -bend))
        loops = VGroup(*[self_loop(nodes[i], color=DIM, up=(i % 2 == 0), width=2) for i in range(4)])
        self.play(LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.12), Create(loops), run_time=2.2)

        # 2 容斥原理
        self.line(2)
        qdef = M(r"q_k=(1-k p)^9", size=34, color=GOLD).move_to([0, -1.5, 0])
        incl = T("容斥原理", 26, GOLD).next_to(qdef, DOWN, buff=0.15)
        self.play(FadeIn(qdef), FadeIn(incl), run_time=0.8)

        # 3 S0 → 恰好两个：6 种选法
        self.line(3)
        target = [a for a in arrows if True][1]   # S0 → S2
        self.play(target.animate.set_color(GOLD).set_stroke(width=5), run_time=0.6)
        pick = VGroup(M(r"\binom{4}{2}=6", size=36, color=GOLD), T("种选法", 22, DIM)).arrange(RIGHT, buff=0.15)
        pick.move_to([-3.2, -2.35, 0])
        self.play(FadeOut(incl), Write(pick), run_time=1.0)

        # 4 q2 − 2q3 + q4
        self.line(4)
        inner = M(r"\times\,(q_2-2q_3+q_4)", size=36).next_to(pick, RIGHT, buff=0.25)
        self.play(Write(inner), run_time=1.4)
        r02 = M(r"=\;r_{02}", size=36, color=GOLD).next_to(inner, RIGHT, buff=0.25)
        self.play(Write(r02), run_time=0.8)

        # 5 杨辉三角
        self.line(5)
        self.play(FadeOut(VGroup(nodes, arrows, loops, pick, inner, r02, qdef)), run_time=0.6)
        rows = [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]
        tri = VGroup()
        for r, row in enumerate(rows):
            tri.add(VGroup(*[T(str(v), 30, GOLD if r == 4 else DIM) for v in row]).arrange(RIGHT, buff=0.55))
        tri.arrange(DOWN, buff=0.22).move_to([-3.6, 0.2, 0])
        self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.15) for r in tri], lag_ratio=0.25), run_time=1.6)
        r0 = VGroup(M(r"r_{00}=q_4", size=40), M(r"r_{01}=4(q_3-q_4)", size=40),
                    M(r"r_{02}=6(q_2-2q_3+q_4)", size=40), M(r"r_{03}=4(q_1-3q_2+3q_3-q_4)", size=40),
                    M(r"r_{04}=1-4q_1+6q_2-4q_3+q_4", size=40)).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        r0.move_to([2.4, 0.2, 0])
        self.play(LaggedStart(*[TransformFromCopy(tri[4][i], r0[i]) for i in range(5)], lag_ratio=0.2), run_time=2.0)

        # 6 5 × 5 矩阵
        self.line(6)
        Rg = M(r"R=\begin{bmatrix}"
               r"q_4 & 0 & 0 & 0 & 0\\[4pt]"
               r"4(q_3-q_4) & q_3 & 0 & 0 & 0\\[4pt]"
               r"6(q_2-2q_3+q_4) & 3(q_2-q_3) & q_2 & 0 & 0\\[4pt]"
               r"4(q_1-3q_2+3q_3-q_4) & 3(q_1-2q_2+q_3) & 2(q_1-q_2) & q_1 & 0\\[4pt]"
               r"1-4q_1+6q_2-4q_3+q_4 & 1-3q_1+3q_2-q_3 & 1-2q_1+q_2 & 1-q_1 & 1"
               r"\end{bmatrix}", size=40)
        if Rg.width > 13.6:
            Rg.scale_to_fit_width(13.6)
        Rg.move_to([0, -0.1, 0])
        self.play(FadeOut(tri), FadeOut(r0, shift=DOWN * 0.2), FadeIn(Rg, shift=DOWN * 0.2), run_time=1.6)

        # 7 面积图：五色铺开
        self.line(7)
        self.play(FadeOut(Rg), run_time=0.5)
        axes, deco = prob_axes(30, width=10.4, height=4.2)
        VGroup(axes, deco).move_to([0.2, -0.3, 0])
        area = stacked_area(axes, D.LINK4_S, STATE[:5])
        leg = legend([f"S_{i}" for i in range(5)], STATE[:5]).next_to(title, DOWN, buff=0.2)
        self.play(Create(axes), FadeIn(deco), FadeIn(leg), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(a, shift=UP * 0.1) for a in area], lag_ratio=0.25), run_time=2.0)

        # 8 第 30 次也只有 56%
        self.line(8)
        s4 = D.LINK4_S[30][4]
        mark = Line(axes.c2p(30, 0), axes.c2p(30, s4), color=GOLD, stroke_width=6)
        mark_t = VGroup(T(f"{s4 * 100:.0f}%", 28, GOLD, weight="BOLD"), T("全拿到", 18, GOLD)).arrange(DOWN, buff=0.04)
        mark_t.next_to(mark, RIGHT, buff=0.12)
        self.play(Create(mark), FadeIn(mark_t), run_time=0.9)

        # 9 E 曲线：−600，临界 18 / 19
        self.line(9)
        self.play(FadeOut(VGroup(axes, deco, area, leg, mark, mark_t)), run_time=0.5)
        ax, dc, path, dots = e_panel(D.LINK4_E, -600, 200, 100, height=4.2, center=(0.2, -0.3))
        self.play(Create(ax), FadeIn(dc), Create(path), FadeIn(dots), run_time=1.4)
        c_lines = crit_lines(ax, (18, 19), -600, 200)
        c_chip = crit_chip("临界十连数：18 和 19", ax, 11.5, -480)
        self.play(Flash(dots[0], color=LOSS, line_length=0.25), dots[0].animate.scale(1.8).set_color(LOSS), run_time=0.7)
        self.play(Create(c_lines), FadeIn(c_chip), run_time=0.9)
        e_group = VGroup(ax, dc, path, dots, c_lines, c_chip)

        # 10 彩蛋
        self.line(10)
        self.play(FadeOut(e_group), FadeOut(title), run_time=0.6)
        egg = chip(T("彩蛋 · 来自另一篇专栏", 30, PURPLE, weight="BOLD"), stroke=PURPLE, pad=0.22).move_to([0, 2.9, 0])
        self.play(FadeIn(egg, scale=1.2), run_time=0.8)

        # 11 策略说明
        self.line(11)
        rule = VGroup(chip(T("0 信仰开局", 24), stroke=DIM, pad=0.14),
                      M(r"\rightarrow", size=34, color=DIM),
                      chip(T("信仰够换剩下的 → 停", 24, GAIN), stroke=GAIN, pad=0.14),
                      chip(T("不够 → 继续十连", 24, LOSS), stroke=LOSS, pad=0.14)).arrange(RIGHT, buff=0.25)
        if rule.width > 13:
            rule.scale_to_fit_width(13)
        rule.move_to([0, 1.85, 0])
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in rule], lag_ratio=0.3), run_time=1.8)

        # 12-14 结局分布柱状图
        names = ["抽 0 井 4", "抽 1 井 3", "抽 2 井 2", "抽 3 井 1", "抽 4 井 0"]
        colors = [STATE[0], STATE[0], STATE[1], GOLD, STATE[2]]
        base_y, h, step = -2.2, 3.0, 2.3
        xs = [(i - 2) * step for i in range(5)]
        bars, vals, labs = VGroup(), VGroup(), VGroup()
        for i, v in enumerate(D.STRAT):
            b = Rectangle(width=1.3, height=max(v * h / 0.75, 0.02), stroke_width=0, fill_color=colors[i], fill_opacity=0.9)
            b.move_to([xs[i], base_y, 0], aligned_edge=DOWN)
            bars.add(b)
            pct = f"{v * 100:.1f}%" if v >= 0.001 else ("< 0.1%" if v > 1e-6 else "≈ 0")
            vals.add(T(pct, 24, colors[i]).next_to(b, UP, buff=0.08))
            labs.add(T(names[i], 22, DIM).move_to([xs[i], base_y - 0.3, 0]))
        floor = Line([xs[0] - 1, base_y, 0], [xs[-1] + 1, base_y, 0], color=DIM, stroke_width=2)

        self.line(12)
        self.play(Create(floor), FadeIn(labs), run_time=0.6)
        self.play(GrowFromEdge(bars[4], DOWN), FadeIn(vals[4]), run_time=0.9)

        self.line(13)
        self.play(GrowFromEdge(bars[3], DOWN), FadeIn(vals[3]), run_time=1.2)
        self.play(Flash(bars[3].get_top(), color=GOLD, line_length=0.3), run_time=0.6)

        self.line(14)
        self.play(GrowFromEdge(bars[2], DOWN), FadeIn(vals[2]), run_time=0.8)
        self.play(*[GrowFromEdge(bars[i], DOWN) for i in (0, 1)], FadeIn(vals[0]), FadeIn(vals[1]), run_time=0.8)

        # 15 抽三井一
        self.line(15)
        hl = SurroundingRectangle(VGroup(bars[3], vals[3], labs[3]), color=GOLD, buff=0.15, corner_radius=0.1)
        self.play(Create(hl), *[m.animate.set_opacity(0.35) for i in (0, 1, 2, 4) for m in (bars[i], vals[i])],
                  run_time=1.0)
        self.finish()


# ---------------------------------------------------------------------------
# 2-7 联动 4UP：只要特定三个
# ---------------------------------------------------------------------------
class S2_7_Link3(Narrated):
    SCENE_ID = "S2_7_Link3"

    def construct(self):
        # 0 去掉 S4
        self.line(0)
        title = T("联动 4UP · 只要特定三个", 30, GOLD, weight="BOLD").to_edge(UP, buff=0.25)
        nodes = chain(5, spacing=2.7, radius=0.42).move_to([0, 1.6, 0])
        self.play(FadeIn(title), FadeIn(nodes), run_time=0.7)
        cross = Cross(nodes[4], stroke_color=LOSS, stroke_width=6)
        self.play(Create(cross), run_time=0.5)
        nodes3 = chain(4, spacing=3.0, radius=0.42).move_to([0, 1.6, 0])
        self.play(FadeOut(VGroup(nodes[4], cross)), ReplacementTransform(nodes[:4], nodes3), run_time=0.8)

        # 1 系数 1 3 3 1，4 × 4 矩阵
        self.line(1)
        coef = VGroup(*[T(str(v), 34, GOLD) for v in (1, 3, 3, 1)]).arrange(RIGHT, buff=0.6).move_to([-4.2, -0.6, 0])
        Rg = M(r"R=\begin{bmatrix}"
               r"q_3 & 0 & 0 & 0\\[4pt]"
               r"3(q_2-q_3) & q_2 & 0 & 0\\[4pt]"
               r"3(q_1-2q_2+q_3) & 2(q_1-q_2) & q_1 & 0\\[4pt]"
               r"1-3q_1+3q_2-q_3 & 1-2q_1+q_2 & 1-q_1 & 1"
               r"\end{bmatrix}", size=34)
        if Rg.width > 8.4:
            Rg.scale_to_fit_width(8.4)
        Rg.move_to([2.4, -0.6, 0])
        self.play(LaggedStart(*[FadeIn(c, scale=1.3) for c in coef], lag_ratio=0.2), run_time=1.0)
        self.play(FadeIn(Rg, shift=LEFT * 0.2), run_time=1.0)

        # 2 临界 16 / 17
        self.line(2)
        self.play(FadeOut(VGroup(coef, Rg, nodes3)), run_time=0.4)
        ax, dc, path, dots = e_panel(D.LINK3_E, -450, 200, 100, height=4.4, center=(0.2, -0.1))
        self.play(Create(ax), FadeIn(dc), Create(path), FadeIn(dots), run_time=1.2)
        self.play(Create(crit_lines(ax, (16, 17), -450, 200)), FadeIn(crit_chip("临界十连数：16 和 17", ax, 24, -250)),
                  run_time=0.8)
        self.finish()


# ---------------------------------------------------------------------------
# 2-8 目标不等价：角色 + 头像框
# ---------------------------------------------------------------------------
class S2_8_Mixed(Narrated):
    SCENE_ID = "S2_8_Mixed"

    def construct(self):
        # 0 之前目标都等价
        self.line(0)
        same = VGroup(*[chip(T("角色", 22, BLUE), stroke=BLUE, pad=0.14) for _ in range(4)]).arrange(RIGHT, buff=0.25)
        eq = VGroup(same, T("概率相同 · 价格相同 → 只看拿到几个", 24, DIM)).arrange(DOWN, buff=0.3).move_to([0, 1.2, 0])
        self.play(FadeIn(eq, lag_ratio=0.1), run_time=1.2)

        # 1 不等价：角色 + 头像框
        self.line(1)
        role = chip(VGroup(T("特定角色", 24, BLUE), M(r"0.7375\%", size=30, color=BLUE), T("150 信仰", 20, DIM))
                    .arrange(DOWN, buff=0.08), stroke=BLUE, pad=0.2)
        frame = chip(VGroup(T("头像框", 24, GOLD), M(r"0.9\%", size=30, color=GOLD), T("100 信仰", 20, DIM))
                     .arrange(DOWN, buff=0.08), stroke=GOLD, pad=0.2)
        pair = VGroup(role, T("+", 40, INK), frame).arrange(RIGHT, buff=0.5).move_to([0, 0.6, 0])
        self.play(FadeOut(eq), FadeIn(pair[0], shift=RIGHT * 0.2), FadeIn(pair[1]), FadeIn(pair[2], shift=LEFT * 0.2),
                  run_time=1.2)

        # 2 参数（已在卡片上）：强调不同
        self.line(2)
        self.play(Indicate(role, color=BLUE, scale_factor=1.06), run_time=0.8)
        self.play(Indicate(frame, color=GOLD, scale_factor=1.06), run_time=0.8)

        # 3 菱形状态图：S0 → Sa / Sc → S2
        self.line(3)
        self.play(pair.animate.scale(0.8).to_corner(UL, buff=0.3), run_time=0.7)
        s0 = state_node("S_0", STATE[0], radius=0.5).move_to([-4.0, -0.3, 0])
        sa = state_node("S_a", GOLD, radius=0.5).move_to([0, 1.25, 0])
        sc = state_node("S_c", BLUE, radius=0.5).move_to([0, -1.85, 0])
        s2 = state_node("S_2", STATE[3], radius=0.5).move_to([4.0, -0.3, 0])
        ta = T("只有头像框", 20, GOLD).next_to(sa, UP, buff=0.12)
        tc = T("只有角色", 20, BLUE).next_to(sc, DOWN, buff=0.12)
        self.play(GrowFromCenter(s0), run_time=0.4)
        self.play(GrowFromCenter(sa), FadeIn(ta), run_time=0.6)
        self.play(GrowFromCenter(sc), FadeIn(tc), run_time=0.6)

        # 4 不能合并：兑换的东西不同
        self.line(4)
        ca = T("还差角色：150", 20, LOSS).next_to(sa, RIGHT, buff=0.25)
        cc = T("还差头像框：100", 20, LOSS).next_to(sc, RIGHT, buff=0.25)
        self.play(FadeIn(ca), FadeIn(cc), run_time=0.8)

        # 5 菱形
        self.line(5)
        self.play(FadeOut(VGroup(ca, cc)), GrowFromCenter(s2), run_time=0.6)
        es = VGroup(edge(s0, sa, color=GOLD), edge(s0, sc, color=BLUE), edge(sa, s2, color=BLUE),
                    edge(sc, s2, color=GOLD), edge(s0, s2, color=DIM))
        self.play(LaggedStart(*[GrowArrow(e) for e in es], lag_ratio=0.2), run_time=1.4)

        # 6 q_c、q_a、q_ca
        self.line(6)
        qs = VGroup(M(r"q_c=(1-p_1)^9", size=34, color=BLUE), M(r"q_a=(1-p_2)^9", size=34, color=GOLD),
                    M(r"q_{ca}=(1-p_1-p_2)^9", size=34, color=INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        qs.to_corner(UR, buff=0.35)
        self.play(LaggedStart(*[FadeIn(q, shift=RIGHT * 0.15) for q in qs], lag_ratio=0.3), run_time=1.6)

        # 7 S0 → Sa
        self.line(7)
        self.play(es[0].animate.set_stroke(width=6), run_time=0.4)
        r0a = M(r"q_c-q_{ca}", size=36, color=GOLD).next_to(es[0].get_center(), UL, buff=0.08)
        self.play(Write(r0a), run_time=1.2)
        rest = VGroup(M(r"q_a-q_{ca}", size=32, color=BLUE).next_to(es[1].get_center(), DL, buff=0.08),
                      M(r"1-q_c", size=32, color=BLUE).next_to(es[2].get_center(), UR, buff=0.08),
                      M(r"1-q_a", size=32, color=GOLD).next_to(es[3].get_center(), DR, buff=0.08))
        self.play(FadeIn(rest, lag_ratio=0.3), run_time=1.0)

        # 8 临界 12 / 13
        self.line(8)
        self.play(FadeOut(VGroup(s0, sa, sc, s2, ta, tc, es, qs, r0a, rest, pair)), run_time=0.5)
        ax, dc, path, dots = e_panel(D.MIXED_E, -250, 200, 50, height=4.6, center=(0.2, 0.0))
        self.play(Create(ax), FadeIn(dc), Create(path), FadeIn(dots), run_time=1.2)
        self.play(Create(crit_lines(ax, (12, 13), -250, 200)), FadeIn(crit_chip("临界十连数：12 和 13", ax, 22, -120)),
                  run_time=0.8)
        self.finish()


# ---------------------------------------------------------------------------
# 2-9 毕业：9 个目标，50 个状态
# ---------------------------------------------------------------------------
class S2_9_Grad(Narrated):
    SCENE_ID = "S2_9_Grad"

    def construct(self):
        # 0 毕业
        self.line(0)
        title = T("联动 4UP · 毕业", 34, GOLD, weight="BOLD").to_edge(UP, buff=0.3)
        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.8)

        # 1 9 个目标
        self.line(1)
        roles = VGroup(*[chip(T("角色", 20, BLUE), stroke=BLUE, pad=0.12) for _ in range(4)]).arrange(RIGHT, buff=0.15)
        frame = chip(T("头像框", 20, GOLD), stroke=GOLD, pad=0.12)
        dress = VGroup(*[chip(T("装扮", 20, PURPLE), stroke=PURPLE, pad=0.12) for _ in range(4)]).arrange(RIGHT, buff=0.15)
        items = VGroup(roles, frame, dress).arrange(RIGHT, buff=0.45).move_to([0, 1.9, 0])
        self.play(LaggedStart(*[FadeIn(x, scale=0.8) for x in [*roles, frame, *dress]], lag_ratio=0.1), run_time=1.6)

        # 2 2^9 = 512
        self.line(2)
        grid = VGroup(*[Square(0.17, stroke_width=0, fill_color=DIM, fill_opacity=0.55) for _ in range(512)])
        grid.arrange_in_grid(rows=16, cols=32, buff=0.04).move_to([0, -0.45, 0])
        g_t = M(r"2^9=512", size=40, color=INK).next_to(grid, RIGHT, buff=0.3)
        if g_t.get_right()[0] > 7.0:
            g_t.next_to(grid, DOWN, buff=0.15)
        self.play(LaggedStart(*[FadeIn(sq) for sq in grid], lag_ratio=0.002), run_time=2.0)
        self.play(Write(g_t), run_time=0.8)

        # 3 等价合并：5 × 2 × 5
        self.line(3)
        merge = VGroup(
            VGroup(T("角色拿到几个", 20, BLUE), M("0..4", size=30, color=BLUE), T("5 种", 22, BLUE)).arrange(DOWN, buff=0.08),
            VGroup(T("头像框", 20, GOLD), M("0/1", size=30, color=GOLD), T("2 种", 22, GOLD)).arrange(DOWN, buff=0.08),
            VGroup(T("装扮拿到几个", 20, PURPLE), M("0..4", size=30, color=PURPLE), T("5 种", 22, PURPLE)).arrange(DOWN, buff=0.08),
        ).arrange(RIGHT, buff=1.0)
        merge.next_to(items, DOWN, buff=0.35)
        self.play(FadeOut(g_t), grid.animate.scale(0.45).set_opacity(0.35).move_to([-4.6, -1.6, 0]),
                  FadeIn(merge, shift=DOWN * 0.15), run_time=1.2)
        for m, src in zip(merge, (roles, frame, dress)):
            self.play(Indicate(src, color=INK, scale_factor=1.08), run_time=0.6)

        # 4 50 个状态
        self.line(4)
        cube = VGroup(*[Square(0.34, stroke_width=0, fill_color=GOLD, fill_opacity=0.8) for _ in range(50)])
        cube.arrange_in_grid(rows=5, cols=10, buff=0.08).move_to([0.4, -1.55, 0])
        c_t = M(r"5\times 2\times 5=50", size=40, color=GOLD).next_to(cube, RIGHT, buff=0.35)
        self.play(ReplacementTransform(grid, cube), run_time=1.6)
        self.play(Write(c_t), run_time=0.8)

        # 5 直接看结果：−900，临界 19 / 20
        self.line(5)
        self.play(FadeOut(VGroup(items, merge, cube, c_t)), run_time=0.5)
        ax, dc, path, dots = e_panel(D.GRAD_E, -900, 300, 300, height=4.4, center=(0.2, -0.3))
        ghost, _ = curve(ax, D.LINK4_E, DIM, width=2)
        ghost.set_stroke(opacity=0.5)
        self.play(Create(ax), FadeIn(dc), Create(path), FadeIn(dots), run_time=1.4)
        self.play(Flash(dots[0], color=LOSS, line_length=0.25), dots[0].animate.scale(1.8).set_color(LOSS), run_time=0.7)
        self.play(Create(crit_lines(ax, (19, 20), -900, 300)),
                  FadeIn(crit_chip("临界十连数：19 和 20", ax, 11.5, -720)), run_time=0.9)

        # 6 只比 4 个角色多 1
        self.line(6)
        ghost_t = T("联动 4 个角色全都要（18 / 19）", 20, DIM).next_to(ax.c2p(24, D.LINK4_E[24]), UP, buff=0.35)
        ghost_t.align_to(ax.c2p(20.6, 0), LEFT)
        self.play(Create(ghost), FadeIn(ghost_t), run_time=1.2)
        self.finish()


# ---------------------------------------------------------------------------
# 2-10 总结 + 练习题
# ---------------------------------------------------------------------------
class S2_10_Summary(Narrated):
    SCENE_ID = "S2_10_Summary"

    def construct(self):
        rows = D.SUMMARY
        n = len(rows)
        left_x, bar_x0, unit = -6.4, -2.2, 0.36
        ys = [2.7 - i * 0.44 for i in range(n)]

        # 0 汇总条形图
        self.line(0)
        title = T("临界十连数汇总", 30, GOLD, weight="BOLD").to_corner(UR, buff=0.35)
        self.play(FadeIn(title), run_time=0.6)
        names, bars, nums = VGroup(), VGroup(), VGroup()
        for (name, (lo, hi), multi), y in zip(rows, ys):
            color = PURPLE if multi else BLUE
            names.add(T(name, 22, INK).move_to([left_x, y, 0], aligned_edge=LEFT))
            bars.add(Rectangle(width=hi * unit, height=0.3, stroke_width=0, fill_color=color, fill_opacity=0.85)
                     .move_to([bar_x0, y, 0], aligned_edge=LEFT))
            nums.add(T(f"{lo} / {hi}", 22, color).next_to(bars[-1], RIGHT, buff=0.12))
        self.play(FadeIn(names, lag_ratio=0.05), run_time=0.8)

        # 1 单目标
        self.line(1)
        single = [i for i, r in enumerate(rows) if not r[2]]
        self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(bars[i], LEFT), FadeIn(nums[i])) for i in single],
                              lag_ratio=0.15), run_time=1.6)

        # 2 多目标
        self.line(2)
        multi = [i for i, r in enumerate(rows) if r[2]]
        self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(bars[i], LEFT), FadeIn(nums[i])) for i in multi],
                              lag_ratio=0.15), run_time=1.6)
        leg = VGroup(VGroup(Square(0.2, fill_color=BLUE, fill_opacity=0.85, stroke_width=0), T("单目标", 20, BLUE)).arrange(RIGHT, buff=0.1),
                     VGroup(Square(0.2, fill_color=PURPLE, fill_opacity=0.85, stroke_width=0), T("多目标", 20, PURPLE)).arrange(RIGHT, buff=0.1)
                     ).arrange(RIGHT, buff=0.4).next_to(title, DOWN, buff=0.2).align_to(title, RIGHT)
        self.play(FadeIn(leg), run_time=0.5)

        # 3 联动全都要 18/19，毕业 19/20
        self.line(3)
        hl = VGroup(*[SurroundingRectangle(VGroup(names[i], nums[i]), color=GOLD, buff=0.06, corner_radius=0.06)
                      for i in (n - 2, n - 1)])
        self.play(Create(hl), run_time=0.9)

        # 4 原因：信仰自由兑换
        self.line(4)
        self.play(FadeOut(VGroup(names, bars, nums, hl, leg, title)), run_time=0.6)
        why = chip(T("信仰可以自由兑换", 36, GOLD, weight="BOLD"), stroke=GOLD, pad=0.25).move_to([0, 2.2, 0])
        self.play(FadeIn(why, scale=1.15), run_time=0.9)

        # 5 前期：多个目标概率相加，很快先拿到一两个
        self.line(5)
        phase1 = chip(VGroup(T("前期", 26, GAIN, weight="BOLD"), T("多个目标的概率加在一起", 22),
                             T("很容易先抽到一两个", 22)).arrange(DOWN, buff=0.1), stroke=GAIN, pad=0.22)
        phase1.move_to([-3.3, -0.2, 0])
        self.play(FadeIn(phase1, shift=RIGHT * 0.2), run_time=0.9)

        # 6 后期：剩下的几个；花掉的抽数变成信仰
        self.line(6)
        phase2 = chip(VGroup(T("后期", 26, LOSS, weight="BOLD"), T("瓶颈在剩下的那几个", 22),
                             T("但前面花掉的抽数已经变成信仰", 22), T("相当于给它们降了价", 22, GOLD)).arrange(DOWN, buff=0.1),
                      stroke=LOSS, pad=0.22).move_to([3.3, -0.2, 0])
        arrow = Arrow(phase1.get_right(), phase2.get_left(), color=DIM, buff=0.15)
        self.play(GrowArrow(arrow), FadeIn(phase2, shift=LEFT * 0.2), run_time=1.2)

        # 7 练习题
        self.line(7)
        self.play(FadeOut(VGroup(why, phase1, phase2, arrow)), run_time=0.6)
        ex_head = T("练习题", 32, GOLD, weight="BOLD").move_to([0, 2.9, 0])
        targets = VGroup(chip(T("特定角色 A", 22, BLUE), stroke=BLUE, pad=0.14),
                         chip(T("特定角色 B", 22, BLUE), stroke=BLUE, pad=0.14),
                         chip(T("特定装扮（非头像框）", 22, PURPLE), stroke=PURPLE, pad=0.14)).arrange(RIGHT, buff=0.35)
        targets.move_to([0, 1.8, 0])
        self.play(FadeIn(ex_head), LaggedStart(*[FadeIn(t, shift=UP * 0.15) for t in targets], lag_ratio=0.3),
                  run_time=1.4)

        # 8 参数
        self.line(8)
        params = VGroup(
            VGroup(T("角色", 22, BLUE), M(r"p=0.7375\%", size=30, color=BLUE), T("价格 150", 22, DIM)).arrange(RIGHT, buff=0.2),
            VGroup(T("装扮（5UP 有头像框）", 22, PURPLE), M(r"p=1.6125\%", size=30, color=PURPLE), T("价格 50", 22, DIM)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, 0.6, 0])
        self.play(FadeIn(params, lag_ratio=0.3), run_time=1.2)

        # 9 思考题：临界十连数是多少？
        self.line(9)
        ask = T("临界十连数 = ?", 34, GOLD, weight="BOLD").move_to([-1.6, -1.0, 0])
        self.play(Write(ask), run_time=0.9)
        self.countdown(9, where=[2.6, -1.0, 0], radius=0.6)

        # 10 答案 13 / 14
        self.line(10)
        ans = T("临界十连数 = 13 和 14", 34, GAIN, weight="BOLD").move_to(ask)
        self.play(ReplacementTransform(ask, ans), run_time=0.8)
        note = T("过程比答案重要", 24, DIM).next_to(ans, DOWN, buff=0.2)
        self.play(FadeIn(note), run_time=0.5)

        # 11 状态图 + 转移矩阵
        self.line(11)
        self.play(FadeOut(VGroup(ex_head, targets, params, ans, note)), run_time=0.6)
        tools = VGroup(chip(T("状态图", 30, INK), stroke=BLUE, pad=0.25), M("+", size=44),
                       chip(T("转移矩阵", 30, INK), stroke=PURPLE, pad=0.25), M(r"\Rightarrow", size=44),
                       chip(T("任意组合都能算", 30, GOLD), stroke=GOLD, pad=0.25)).arrange(RIGHT, buff=0.35)
        if tools.width > 13:
            tools.scale_to_fit_width(13)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.15) for t in tools], lag_ratio=0.25), run_time=1.6)

        # 12 结尾
        self.line(12)
        bye = T("感谢观看", 48, GOLD, weight="BOLD").move_to([0, -1.2, 0])
        self.play(tools.animate.shift(UP * 0.8), FadeIn(bye, shift=UP * 0.2), run_time=1.0)
        self.finish()
