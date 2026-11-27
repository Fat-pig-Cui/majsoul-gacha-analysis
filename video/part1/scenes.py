"""上半部分（基础篇）的分镜。

在 video/ 目录下渲染：
    ../.venv/bin/manim -ql part1/scenes.py S1_4_Refine S1_5_Example   # 预览
    ../.venv/bin/manim -qp part1/scenes.py                            # 2K（1440p60）终渲全部分镜
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from manim import *  # noqa: E402,F403

import data as D  # noqa: E402
from style import (  # noqa: E402
    BG, BLUE, DIM, GAIN, GOLD, INK, LOSS, PANEL, PURPLE, STATE as STATE_COLORS, M, Narrated, T, chip, e_axes,
    panel, ten_cards,
)

BG_DARK = BG


# ---------------------------------------------------------------------------
# 共用小组件
# ---------------------------------------------------------------------------
def pool_card(title: str, sub: str, color: str, w: float = 3.6, h: float = 2.3) -> VGroup:
    """卡池卡片：标题 + 一行说明。"""
    bg = panel(w, h, stroke=color)
    t = T(title, 34, color, weight="BOLD")
    s = T(sub, 22, DIM)
    VGroup(t, s).arrange(DOWN, buff=0.22).move_to(bg)
    return VGroup(bg, t, s)


def split_bar(k: int, total: int, width: float, left_color: str, right_color: str, h: float = 0.5) -> VGroup:
    """把 total 个十连分成左 k 个、右 total-k 个的分段条。"""
    cell = width / total
    cells = VGroup(*[
        Rectangle(width=cell - 0.06, height=h, stroke_width=0,
                  fill_color=left_color if i < k else right_color, fill_opacity=0.9)
        for i in range(total)
    ]).arrange(RIGHT, buff=0.06)
    return cells


def prob_bar(parts, width: float = 11.0, h: float = 0.62) -> VGroup:
    """按比例分段的概率条。parts = [(比例, 颜色, 标签或 None)]。返回 VGroup(段, 标签)。"""
    segs, labels = VGroup(), VGroup()
    x = -width / 2
    for frac, color, label in parts:
        w = width * frac
        seg = Rectangle(width=max(w, 0.02), height=h, stroke_width=0, fill_color=color, fill_opacity=0.9)
        seg.move_to([x + w / 2, 0, 0])
        segs.add(seg)
        if label:
            labels.add(T(label, 22, INK).move_to(seg) if w > 1.3 else T(label, 22, INK).next_to(seg, DOWN, buff=0.12))
        x += w
    return VGroup(segs, labels)


# ---------------------------------------------------------------------------
# 1-0 开场钩子：12 个十连怎么分给联动和贵人
# ---------------------------------------------------------------------------
class S1_0_Hook(Narrated):
    SCENE_ID = "S1_0_Hook"

    def construct(self):
        # 0 12 个十连
        self.line(0)
        stacks = VGroup(*[ten_cards(width=0.2, height=0.3, buff=0.025) for _ in range(12)])
        stacks.arrange_in_grid(rows=3, cols=4, buff=(0.45, 0.3)).move_to([0, 1.0, 0])
        cnt = T("× 12 个十连", 30, GOLD).next_to(stacks, DOWN, buff=0.4)
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.3, scale=0.8) for s in stacks], lag_ratio=0.08), run_time=1.6)
        self.play(FadeIn(cnt, shift=UP * 0.2), run_time=0.6)

        # 1 两个池子
        self.line(1)
        collab = pool_card("联动池", "想要 1 个联动角色", BLUE).move_to([-4.3, -1.3, 0])
        noble = pool_card("贵人池", "想要 1 个贵人角色", PURPLE).move_to([4.3, -1.3, 0])
        self.play(VGroup(stacks, cnt).animate.scale(0.8).move_to([0, 2.4, 0]), run_time=0.8)
        self.play(FadeIn(collab, shift=RIGHT * 0.4), FadeIn(noble, shift=LEFT * 0.4), run_time=1.0)

        # 2 怎么分？分段条左右滑动
        self.line(2)
        k = ValueTracker(6)
        bar_w = 7.0
        bar = always_redraw(lambda: split_bar(int(round(k.get_value())), 12, bar_w, BLUE, PURPLE)
                            .move_to([0, -0.2, 0]))
        nums = always_redraw(lambda: VGroup(
            T(f"联动 {int(round(k.get_value()))}", 26, BLUE).move_to([-1.5, -0.95, 0]),
            T(f"贵人 {12 - int(round(k.get_value()))}", 26, PURPLE).move_to([1.5, -0.95, 0]),
        ))
        self.play(FadeOut(cnt), FadeIn(bar), FadeIn(nums), run_time=0.6)
        self.play(k.animate.set_value(2), run_time=1.0)
        self.play(k.animate.set_value(10), run_time=1.3)

        # 3 全砸联动？全砸贵人？对半分？
        self.line(3)
        for target in (12, 0, 6):
            self.play(k.animate.set_value(target), run_time=0.7)
            self.wait(0.35)

        # 4 看完就能算出来：问号
        self.line(4)
        q = T("？", 120, GOLD, weight="BOLD").move_to([0, -2.3, 0])
        best = T("最划算的分法", 26, GOLD).next_to(q, LEFT, buff=0.3)
        self.play(FadeIn(q, scale=1.8), FadeIn(best, shift=RIGHT * 0.2), run_time=0.9)
        self.play(Wiggle(q), run_time=1.0)

        # 5 从头说起
        self.line(5)
        self.play(FadeOut(VGroup(stacks, collab, noble, q, best)), FadeOut(bar), FadeOut(nums), run_time=1.0)
        self.finish()


# ---------------------------------------------------------------------------
# 1-1 抽卡概率：概率条逐层拆分
# ---------------------------------------------------------------------------
class S1_1_Probability(Narrated):
    SCENE_ID = "S1_1_Probability"
    ROSE = "#ff8fb1"

    def construct(self):
        W = 11.0
        title = T("抽卡概率", 34, INK, weight="BOLD").to_edge(UP, buff=0.5)

        # 0 三大类
        self.line(0)
        full = Rectangle(width=W, height=0.62, stroke_width=0, fill_color=DIM, fill_opacity=0.6).move_to([0, 2.2, 0])
        full_t = T("每一抽 100%", 24).move_to(full)
        self.play(FadeIn(title, shift=DOWN * 0.2), GrowFromEdge(full, LEFT), FadeIn(full_t), run_time=1.4)

        # 1 5% / 15% / 80%
        self.line(1)
        top = prob_bar([(0.05, GOLD, "角色 5%"), (0.15, self.ROSE, "装扮 15%"), (0.80, DIM, "礼物 80%")], W)
        top.move_to([0, 2.2, 0])
        # 小段的标签放到下面
        self.play(ReplacementTransform(full, top[0]), FadeOut(full_t), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.1) for l in top[1]], lag_ratio=0.3), run_time=1.2)

        # 2 礼物不管
        self.line(2)
        gift = top[0][2]
        self.play(gift.animate.set_fill(opacity=0.15), top[1][2].animate.set_opacity(0.35), run_time=0.8)

        # 3 角色放大：UP 占 59%
        self.line(3)
        role_src = top[0][0]
        role = prob_bar([(0.59, GOLD, "UP 角色 59%"), (0.41, "#8a7330", "其他角色 41%")], W)
        role.move_to([0, 0.75, 0])
        role_head = T("角色 5% 放大来看", 22, GOLD).next_to(role, UP, buff=0.15).align_to(role, LEFT)
        guide = VGroup(
            DashedLine(role_src.get_corner(DL), role[0].get_corner(UL), color=GOLD, stroke_width=1.5),
            DashedLine(role_src.get_corner(DR), role[0].get_corner(UR), color=GOLD, stroke_width=1.5),
        )
        self.play(Create(guide), TransformFromCopy(role_src, role[0]), run_time=1.2)
        self.play(FadeIn(role[1]), FadeIn(role_head), run_time=0.7)

        # 4 5% × 59% = 2.95%
        self.line(4)
        eq = M(r"5\%", r"\times", r"59\%", "=", r"2.95\%", size=48).move_to([0, -0.45, 0])
        eq[4].set_color(GOLD)
        self.play(Write(eq), run_time=1.6)
        self.play(Circumscribe(eq[4], color=GOLD), run_time=0.9)

        # 5 多位 UP 平分
        self.line(5)
        self.play(eq.animate.scale(0.7).to_edge(LEFT, buff=0.6).shift(DOWN * 0.15), run_time=0.7)
        up_seg = role[0][0]
        rows = VGroup()
        for n, label in ((1, "单 UP"), (2, "双 UP"), (4, "联动 4UP")):
            cells = VGroup(*[Rectangle(width=up_seg.width / n - 0.05, height=0.42, stroke_width=0,
                                       fill_color=GOLD, fill_opacity=0.9 - 0.12 * i) for i in range(n)])
            cells.arrange(RIGHT, buff=0.05)
            name = T(label, 22, DIM)
            rows.add(VGroup(name, cells))
        for r in rows:
            r[1].align_to(up_seg, LEFT)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([1.2, -1.75, 0])
        for r in rows:
            r[0].next_to(r[1], LEFT, buff=0.3)
        self.play(LaggedStart(*[TransformFromCopy(up_seg, r[1]) for r in rows], lag_ratio=0.3),
                  LaggedStart(*[FadeIn(r[0]) for r in rows], lag_ratio=0.3), run_time=1.8)

        # 6 每位 1.475% / 0.7375%
        self.line(6)
        vals = VGroup(
            M(r"2.95\%", size=30, color=GOLD).next_to(rows[0][1], RIGHT, buff=0.25),
            M(r"1.475\%", size=30, color=GOLD).next_to(rows[1][1], RIGHT, buff=0.25),
            M(r"0.7375\%", size=30, color=GOLD).next_to(rows[2][1], RIGHT, buff=0.25),
        )
        self.play(LaggedStart(*[FadeIn(v, shift=LEFT * 0.2) for v in vals], lag_ratio=0.35), run_time=1.6)

        # 7 贵人 20% → 1%
        self.line(7)
        self.play(FadeOut(VGroup(rows, vals, eq)), run_time=0.6)
        noble = prob_bar([(0.20, PURPLE, "贵人 20%"), (0.80, "#4b3c66", "其他角色 80%")], W).move_to([0, 0.75, 0])
        self.play(ReplacementTransform(role, noble), run_time=1.0)
        eq2 = M(r"5\%", r"\times", r"20\%", "=", r"1\%", size=48).move_to([0, -0.6, 0])
        eq2[4].set_color(PURPLE)
        self.play(Write(eq2), run_time=1.6)

        # 8 装扮：UP 49% = 7.35%
        self.line(8)
        dress_src = top[0][1]
        self.play(FadeOut(VGroup(noble, eq2, role_head)), FadeOut(guide), run_time=0.6)
        dress = prob_bar([(0.49, self.ROSE, "UP 装扮 49%"), (0.51, "#80485a", "其他装扮 51%")], W).move_to([0, 0.75, 0])
        d_head = T("装扮 15% 放大来看", 22, self.ROSE).next_to(dress, UP, buff=0.15).align_to(dress, LEFT)
        guide2 = VGroup(
            DashedLine(dress_src.get_corner(DL), dress[0].get_corner(UL), color=self.ROSE, stroke_width=1.5),
            DashedLine(dress_src.get_corner(DR), dress[0].get_corner(UR), color=self.ROSE, stroke_width=1.5),
        )
        self.play(Create(guide2), TransformFromCopy(dress_src, dress[0]), FadeIn(dress[1]), FadeIn(d_head), run_time=1.3)
        eq3 = M(r"15\%", r"\times", r"49\%", "=", r"7.35\%", size=44).move_to([0, -0.45, 0])
        eq3[4].set_color(self.ROSE)
        self.play(Write(eq3), run_time=1.4)

        # 9 头像框拿走 6% → 0.9%
        self.line(9)
        up_d = dress[0][0]
        frame_w = W * 0.06
        frame_seg = Rectangle(width=frame_w, height=0.62, stroke_width=0, fill_color=GOLD, fill_opacity=0.95)
        frame_seg.move_to(up_d.get_left() + RIGHT * frame_w / 2)
        rest_seg = Rectangle(width=up_d.width - frame_w, height=0.62, stroke_width=0,
                             fill_color=self.ROSE, fill_opacity=0.9).next_to(frame_seg, RIGHT, buff=0)
        frame_t = T("头像框 6%", 22, GOLD).next_to(frame_seg, DOWN, buff=0.15)
        self.play(FadeOut(dress[1][0]), ReplacementTransform(up_d, VGroup(frame_seg, rest_seg)), run_time=1.0)
        self.play(FadeIn(frame_t, shift=UP * 0.1), eq3.animate.shift(DOWN * 0.5), run_time=0.7)
        eq4 = M(r"15\%", r"\times", r"6\%", "=", r"0.9\%", size=38, color=GOLD).next_to(eq3, DOWN, buff=0.3)
        self.play(Write(eq4), run_time=1.2)

        # 10 剩余 43% = 6.45% 平分
        self.line(10)
        rest_t = T("其他 UP 装扮 43%", 22).move_to(rest_seg)
        eq5 = M(r"15\%", r"\times", r"43\%", "=", r"6.45\%", size=38, color=self.ROSE).next_to(eq4, DOWN, buff=0.25)
        self.play(FadeIn(rest_t), Write(eq5), run_time=1.4)

        # 11 记住两个数
        self.line(11)
        self.play(FadeOut(VGroup(top, dress[0][1], dress[1][1], frame_seg, rest_seg, frame_t, rest_t,
                                 eq3, eq4, eq5, d_head, guide2)), run_time=0.8)
        k1 = chip(VGroup(T("UP 角色", 26, DIM), M(r"2.95\%", size=56, color=GOLD)).arrange(DOWN, buff=0.15),
                  stroke=GOLD, pad=0.35)
        k2 = chip(VGroup(T("贵人", 26, DIM), M(r"1\%", size=56, color=PURPLE)).arrange(DOWN, buff=0.15),
                  stroke=PURPLE, pad=0.35)
        keys = VGroup(k1, k2).arrange(RIGHT, buff=1.2).move_to([0, 0.3, 0])
        self.play(LaggedStart(FadeIn(k1, scale=0.9), FadeIn(k2, scale=0.9), lag_ratio=0.4), run_time=1.2)
        self.finish()


# ---------------------------------------------------------------------------
# 1-2 信仰与十连
# ---------------------------------------------------------------------------
class S1_2_Faith(Narrated):
    SCENE_ID = "S1_2_Faith"

    def construct(self):
        # 0 信仰 = 井
        self.line(0)
        well = VGroup(
            Circle(radius=1.0, stroke_color=GOLD, stroke_width=6),
            T("信仰", 40, GOLD, weight="BOLD"),
        ).move_to([0, 1.2, 0])
        tag = T("最终保底 · 井", 26, DIM).next_to(well, DOWN, buff=0.3)
        self.play(Create(well[0]), FadeIn(well[1], scale=1.3), run_time=1.2)
        self.play(FadeIn(tag, shift=UP * 0.2), run_time=0.6)

        # 1 一抽一信仰、共享、继承
        self.line(1)
        counter = ValueTracker(0)
        num = always_redraw(lambda: T(f"{int(counter.get_value())}", 44, GOLD).next_to(well, RIGHT, buff=0.6))
        plus = T("抽 1 次 = 信仰 +1", 24, INK).move_to([-4.3, 1.2, 0])
        self.play(FadeIn(plus), FadeIn(num), run_time=0.5)
        self.play(counter.animate.set_value(40), run_time=1.6, rate_func=linear)
        share = VGroup(chip(T("池子 A", 22), stroke=BLUE, pad=0.14), chip(T("池子 B", 22), stroke=PURPLE, pad=0.14),
                       chip(T("下一期", 22), stroke=GAIN, pad=0.14)).arrange(RIGHT, buff=0.5).move_to([0, -1.2, 0])
        arrows = VGroup(*[Arrow(well.get_bottom(), s.get_top(), buff=0.2, color=DIM, stroke_width=3) for s in share])
        self.play(FadeOut(tag), LaggedStart(*[AnimationGroup(GrowArrow(a), FadeIn(s)) for a, s in zip(arrows, share)],
                                            lag_ratio=0.3), run_time=1.6)

        # 2 角色价格
        self.line(2)
        self.play(FadeOut(VGroup(well, plus, share, arrows)), FadeOut(num), run_time=0.6)

        def price(name, value, color):
            return chip(VGroup(T(name, 24, DIM), M(str(value), size=52, color=color)).arrange(DOWN, buff=0.12),
                        stroke=color, pad=0.3)

        prices = VGroup(price("常驻 / 联动角色", 150, GOLD), price("贵人角色", 300, PURPLE),
                        price("装扮", 50, S1_1_Probability.ROSE), price("头像框", 100, S1_1_Probability.ROSE))
        prices.arrange(RIGHT, buff=0.45).move_to([0, 0.9, 0])
        head = T("兑换价格（信仰）", 26, INK).next_to(prices, UP, buff=0.4)
        self.play(FadeIn(head), LaggedStart(FadeIn(prices[0], shift=UP * 0.2), FadeIn(prices[1], shift=UP * 0.2),
                                            lag_ratio=0.5), run_time=1.4)

        # 3 装扮价格
        self.line(3)
        self.play(LaggedStart(FadeIn(prices[2], shift=UP * 0.2), FadeIn(prices[3], shift=UP * 0.2), lag_ratio=0.5),
                  run_time=1.2)

        # 4 十连必出紫礼物
        self.line(4)
        self.play(FadeOut(VGroup(prices, head)), run_time=0.6)
        cards = ten_cards().move_to([0, 1.2, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in cards], lag_ratio=0.08), run_time=1.2)
        gift = T("必得紫礼物", 24, PURPLE).next_to(cards[9], UP, buff=0.2)
        self.play(Indicate(cards[9], color=PURPLE, scale_factor=1.15), FadeIn(gift), run_time=1.0)

        # 5 只有 9 次有效
        self.line(5)
        b9 = Brace(cards[:9], DOWN, color=BLUE, buff=0.15)
        b9_t = T("对角色和装扮：9 次有效抽卡", 26, BLUE).next_to(b9, DOWN, buff=0.12)
        self.play(GrowFromCenter(b9), FadeIn(b9_t), run_time=1.0)

        # 6 1800 = 200 × 9
        self.line(6)
        eq = VGroup(T("十连", 26, DIM), M("1800", size=48), M("=", size=48), M("200", size=48),
                    M(r"\times", size=48), M("9", size=48, color=BLUE), T("辉玉", 26, DIM)).arrange(RIGHT, buff=0.18)
        eq.move_to([0, -1.6, 0])
        self.play(Write(eq), run_time=1.8)

        # 7 十连的好处
        self.line(7)
        self.play(FadeOut(VGroup(eq, b9, b9_t)), run_time=0.5)
        perks = VGroup(chip(T("+1 信仰", 28, GOLD), stroke=GOLD), chip(T("+1 紫礼物", 28, PURPLE), stroke=PURPLE))
        perks.arrange(RIGHT, buff=0.8).move_to([0, -1.0, 0])
        vs = T("十连  vs  单抽 9 次", 26, DIM).next_to(perks, UP, buff=0.35)
        self.play(FadeIn(vs), LaggedStart(*[FadeIn(p, scale=0.9) for p in perks], lag_ratio=0.4), run_time=1.4)

        # 8 后面都按辉玉十连算
        self.line(8)
        rule = chip(T("后面的分析：一律按辉玉十连计算", 30, GOLD), stroke=GOLD, pad=0.3).move_to([0, -2.4, 0])
        self.play(FadeOut(vs), FadeIn(rule, shift=UP * 0.2), run_time=0.9)
        self.finish()


# ---------------------------------------------------------------------------
# 1-3 定义信仰变动期望
# ---------------------------------------------------------------------------
class S1_3_Define(Narrated):
    SCENE_ID = "S1_3_Define"

    def construct(self):
        # 0 新概念
        self.line(0)
        name = T("信仰变动期望", 56, GOLD, weight="BOLD").move_to([0, 0.5, 0])
        self.play(Write(name), run_time=1.6)

        # 1 前提
        self.line(1)
        self.play(name.animate.scale(0.55).to_edge(UP, buff=0.45), run_time=0.8)
        conds = VGroup(chip(T("信仰足够多", 24), stroke=DIM, pad=0.15),
                       chip(T("给定抽数", 24), stroke=DIM, pad=0.15),
                       chip(T("一定要拿到目标", 24), stroke=DIM, pad=0.15)).arrange(RIGHT, buff=0.35)
        conds.next_to(name, DOWN, buff=0.35)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.15) for c in conds], lag_ratio=0.35), run_time=1.5)

        # 2 两种结果
        self.line(2)
        root = Dot([-4.8, 0.05, 0], radius=0.12, color=INK)
        hit = chip(T("抽到了", 28, GAIN), stroke=GAIN).move_to([-1.2, 1.25, 0])
        miss = chip(T("没抽到", 28, LOSS), stroke=LOSS).move_to([-1.2, -1.15, 0])
        e1 = Line(root.get_center(), hit.get_left(), color=GAIN, stroke_width=3)
        e2 = Line(root.get_center(), miss.get_left(), color=LOSS, stroke_width=3)
        self.play(FadeIn(root), Create(e1), Create(e2), FadeIn(hit), FadeIn(miss), run_time=1.2)

        # 3 抽到：目标 + 信仰
        self.line(3)
        hit_d = VGroup(T("目标到手", 24), T("+ 白拿这些抽数的信仰", 24, GAIN)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        hit_d.next_to(hit, RIGHT, buff=0.4)
        self.play(FadeIn(hit_d, shift=LEFT * 0.2), run_time=1.0)

        # 4 没抽到：花信仰兑换
        self.line(4)
        miss_d = VGroup(T("花信仰兑换", 24), T("信仰通常净减少", 24, LOSS)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        miss_d.next_to(miss, RIGHT, buff=0.4)
        self.play(FadeIn(miss_d, shift=LEFT * 0.2), run_time=1.0)

        # 5 对立事件
        self.line(5)
        p_hit = M("P", size=36, color=BLUE).next_to(e1.get_center(), UL, buff=0.08)
        p_miss = M("1-P", size=36, color=BLUE).next_to(e2.get_center(), DL, buff=0.08)
        self.play(FadeIn(p_hit), FadeIn(p_miss), run_time=0.9)
        one = M("P + (1-P) = 1", size=34, color=DIM).move_to([3.8, 0.05, 0])
        self.play(Write(one), run_time=1.0)

        # 6 记号 G P C
        self.line(6)
        self.play(FadeOut(VGroup(conds, one)), run_time=0.5)
        legend = VGroup(
            VGroup(M("G", size=36, color=GOLD), T("给定抽数", 22, DIM)).arrange(RIGHT, buff=0.15),
            VGroup(M("P", size=36, color=BLUE), T("抽到的概率", 22, DIM)).arrange(RIGHT, buff=0.15),
            VGroup(M("C", size=36, color=LOSS), T("信仰价格", 22, DIM)).arrange(RIGHT, buff=0.15),
        ).arrange(RIGHT, buff=0.6).next_to(name, DOWN, buff=0.4)
        self.play(LaggedStart(*[FadeIn(l, shift=DOWN * 0.15) for l in legend], lag_ratio=0.35), run_time=1.6)

        # 7 变动 G 和 G − C
        self.line(7)
        g_hit = M("+G", size=44, color=GAIN).next_to(hit_d, RIGHT, buff=0.5)
        g_miss = M("G-C", size=44, color=LOSS).next_to(miss_d, RIGHT, buff=0.5)
        self.play(FadeIn(g_hit, shift=LEFT * 0.2), run_time=0.8)
        self.wait(0.6)
        self.play(FadeIn(g_miss, shift=LEFT * 0.2), run_time=0.8)

        # 8 加权平均 → 公式
        self.line(8)
        f = M("E", "=", "G", r"\cdot P", "+", "(G-C)", r"(1-P)", size=54).move_to([0, -2.55, 0])
        f[2].set_color(GAIN)
        f[5].set_color(LOSS)
        self.play(TransformFromCopy(g_hit, f[2]), TransformFromCopy(p_hit, f[3]),
                  TransformFromCopy(g_miss, f[5]), TransformFromCopy(p_miss, f[6]),
                  FadeIn(VGroup(f[0], f[1], f[4])), run_time=1.8)
        box = SurroundingRectangle(f, color=GOLD, buff=0.2, corner_radius=0.1)
        self.play(Create(box), run_time=0.7)

        # 9 衡量信仰涨跌
        self.line(9)
        tree = VGroup(root, e1, e2, hit, miss, hit_d, miss_d, p_hit, p_miss, g_hit, g_miss, legend)
        self.play(FadeOut(tree), VGroup(f, box).animate.move_to([0, 1.8, 0]), run_time=0.9)
        up = VGroup(Arrow(DOWN * 0.5, UP * 0.5, color=GAIN, stroke_width=6), T("E > 0：信仰长期在涨", 26, GAIN)).arrange(RIGHT)
        dn = VGroup(Arrow(UP * 0.5, DOWN * 0.5, color=LOSS, stroke_width=6), T("E < 0：信仰长期在跌", 26, LOSS)).arrange(RIGHT)
        VGroup(up, dn).arrange(RIGHT, buff=1.2).move_to([0, 0.2, 0])
        self.play(FadeIn(up, shift=UP * 0.2), FadeIn(dn, shift=DOWN * 0.2), run_time=1.0)

        # 10 例：G = 0 → E = −150
        self.line(10)
        self.play(FadeOut(VGroup(up, dn)), run_time=0.4)
        ex_head = T("常规单 UP 池：C = 150", 26, DIM).move_to([0, 0.5, 0])
        ex0 = M(r"G=0:\quad E", "=", r"0\cdot 0", "+", r"(0-150)\cdot 1", "=", "-150", size=44).move_to([0, -0.4, 0])
        ex0[6].set_color(LOSS)
        self.play(FadeIn(ex_head), run_time=0.5)
        self.play(Write(ex0), run_time=2.2)

        # 11 例：G = 150 → E = 150·P150。G=0 的式子逐项变形成 G=150 的式子
        self.line(11)
        ex1 = M(r"G=150:\quad E", "=", r"150P_{150}", "+", r"(150-150)(1-P_{150})", size=40)
        res = M(r"=150P_{150}", size=40, color=GAIN)
        row = VGroup(ex1, res).arrange(RIGHT, buff=0.2)
        if row.width > config.frame_width - 1.0:
            row.scale_to_fit_width(config.frame_width - 1.0)
        row.move_to([0, -0.4, 0])
        # 先把 −150 的结果收掉，再让左边各项对应变形；0 → 150 的变化在 G 和概率两处同时发生
        self.play(FadeOut(ex0[5:], shift=RIGHT * 0.3), run_time=0.5)
        # 内容不同的项（G=…、第一项、第二项）交叉淡化移位，避免字形互相扭曲；“=”“+”直接移动
        self.play(*[FadeTransform(ex0[i], ex1[i]) for i in (0, 2, 4)],
                  *[ReplacementTransform(ex0[i], ex1[i]) for i in (1, 3)], run_time=1.4)
        zero = M("=0", size=34, color=DIM).next_to(ex1[4], DOWN, buff=0.12)
        self.play(ex1[4].animate.set_opacity(0.35), FadeIn(zero, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(res, shift=LEFT * 0.2), run_time=0.8)
        self.finish()


# ---------------------------------------------------------------------------
# 1-4 公式的优化：抽到就停手 → 首达分解 → 换成十连
# ---------------------------------------------------------------------------
class S1_4_Refine(Narrated):
    SCENE_ID = "S1_4_Refine"

    def construct(self):
        # 0 刚才的公式有漏洞
        self.line(0)
        old = M("E", "=", "G", r"\cdot P", "+", "(G-C)", r"(1-P)", size=54).to_edge(UP, buff=0.7)
        old_tag = T("刚才的公式", 24, DIM).next_to(old, UP, buff=0.15)
        self.play(FadeIn(old_tag, shift=DOWN * 0.2), Write(old), run_time=1.8)
        flaw = Underline(VGroup(old[2], old[3]), color=LOSS, stroke_width=5)
        self.play(Create(flaw), Indicate(VGroup(old[2], old[3]), color=LOSS), run_time=1.2)

        # 1 默认抽满：进度条一路走到 150
        self.line(1)
        bar_w, bar_y, left = 11.0, 0.3, -5.5
        state = {"t": ValueTracker(0), "color": BLUE}
        frame = Rectangle(width=bar_w, height=0.55, stroke_color=DIM, stroke_width=2).move_to([0, bar_y, 0])
        fill = always_redraw(lambda: Rectangle(
            width=max(bar_w * state["t"].get_value() / 150, 1e-3), height=0.55,
            fill_color=state["color"], fill_opacity=0.85, stroke_width=0,
        ).move_to([left, bar_y, 0], aligned_edge=LEFT))
        ticks = VGroup(*[
            VGroup(Line([left + bar_w * k / 150, bar_y - 0.32, 0], [left + bar_w * k / 150, bar_y - 0.45, 0],
                        color=DIM, stroke_width=2),
                   T(str(k), 20, DIM).move_to([left + bar_w * k / 150, bar_y - 0.68, 0]))
            for k in (0, 50, 100, 150)
        ])
        cap = T("朴素公式的假设：不管抽没抽到，都把 150 抽抽满", 26).next_to(frame, UP, buff=0.45)
        self.play(FadeIn(frame), FadeIn(ticks), FadeIn(cap, shift=UP * 0.2), run_time=1.0)
        self.add(fill)
        self.play(state["t"].animate.set_value(150), run_time=2.8, rate_func=linear)

        # 2 现实里谁会这么抽？
        self.line(2)
        q = T("？", 80, GOLD).next_to(frame, RIGHT, buff=0.15).shift(UP * 0.9)
        self.play(FadeIn(q, scale=1.6), Wiggle(fill), run_time=1.4)

        # 3 第 40 抽出货就收手
        self.line(3)
        self.play(FadeOut(q), FadeOut(cap), state["t"].animate.set_value(0), run_time=0.6)
        state["color"] = GAIN
        x40 = left + bar_w * 40 / 150
        self.play(state["t"].animate.set_value(40), run_time=1.6, rate_func=linear)
        star = Star(5, outer_radius=0.34, fill_color=GOLD, fill_opacity=1, stroke_width=0).move_to([x40, bar_y, 0])
        hit = T("第 40 抽出货 → 收手", 26, GOLD).next_to(star, UP, buff=0.35)
        tick40 = T("40", 20, GOLD).move_to([x40, bar_y - 0.68, 0])
        self.play(GrowFromCenter(star), FadeIn(hit, shift=UP * 0.2), FadeIn(tick40), ticks[1][1].animate.set_opacity(0), run_time=0.9)
        self.play(Flash(star, color=GOLD, line_length=0.3), run_time=0.7)

        # 4 剩下 110 抽不会花
        self.line(4)
        waste = Rectangle(width=bar_w * 110 / 150, height=0.55, stroke_color=LOSS, stroke_width=2,
                          fill_color=LOSS, fill_opacity=0.18).move_to([x40, bar_y, 0], aligned_edge=LEFT)
        hatch = VGroup(*[
            Line([x40 + 0.15 + 0.35 * k, bar_y - 0.27, 0], [x40 + 0.4 + 0.35 * k, bar_y + 0.27, 0],
                 color=LOSS, stroke_width=1.5, stroke_opacity=0.6)
            for k in range(int(bar_w * 110 / 150 / 0.35) - 1)
        ])
        brace = Brace(waste, DOWN, color=LOSS, buff=0.55)
        brace_t = T("110 抽：根本不会花出去", 26, LOSS).next_to(brace, DOWN, buff=0.15)
        self.play(FadeIn(waste), Create(hatch), run_time=0.9)
        self.play(GrowFromCenter(brace), FadeIn(brace_t), run_time=0.9)
        self.play(Indicate(VGroup(old[2], old[3]), color=LOSS, scale_factor=1.15), run_time=1.0)

        # 5 概率树：抽到 / 没抽到
        self.line(5)
        bar_group = VGroup(frame, ticks, waste, hatch, brace, brace_t, star, hit, tick40)
        self.play(FadeOut(bar_group), FadeOut(fill), FadeOut(flaw),
                  FadeOut(old), FadeOut(old_tag), run_time=0.8)
        self.remove(fill)

        root = Dot([-5.9, 0.7, 0], radius=0.11, color=INK)
        root_t = T("开抽", 24, DIM).next_to(root, LEFT, buff=0.15)
        hit_node = chip(T("抽到", 26, GAIN), stroke=GAIN).move_to([-3.6, 1.95, 0])
        miss_node = chip(T("没抽到", 26, LOSS), stroke=LOSS).move_to([-3.6, -0.9, 0])
        e_hit = Line(root.get_center(), hit_node.get_left(), color=GAIN, stroke_width=3)
        e_miss = Line(root.get_center(), miss_node.get_left(), color=LOSS, stroke_width=3)
        self.play(FadeIn(root), FadeIn(root_t), run_time=0.4)
        self.play(Create(e_hit), Create(e_miss), FadeIn(hit_node), FadeIn(miss_node), run_time=1.0)
        self.play(Indicate(hit_node, color=GAIN), run_time=0.9)

        # 6 “抽到”拆成第 1、2、…、M 抽
        self.line(6)
        ys = [2.95, 2.3, 1.7, 1.0]
        names = ["第 1 抽抽到", "第 2 抽抽到", None, "第 M 抽抽到"]
        leaves, edges = VGroup(), VGroup()
        for y, name in zip(ys, names):
            if name is None:
                leaves.add(M(r"\vdots", size=34, color=DIM).move_to([-0.6, y, 0]))
                continue
            leaf = chip(T(name, 22), stroke=GAIN, pad=0.14).move_to([-0.6, y, 0])
            leaves.add(leaf)
            edges.add(Line(hit_node.get_right(), leaf.get_left(), color=GAIN, stroke_width=2))
        self.play(LaggedStart(*[AnimationGroup(Create(e), FadeIn(l, shift=RIGHT * 0.2))
                                for e, l in zip(edges, [leaves[0], leaves[1], leaves[3]])],
                              lag_ratio=0.5), FadeIn(leaves[2]), run_time=2.4)

        # 7 概率 u_n
        self.line(7)
        u_labels = VGroup(
            M("u_1", size=36, color=BLUE).move_to([1.35, ys[0], 0]),
            M("u_2", size=36, color=BLUE).move_to([1.35, ys[1], 0]),
            M(r"\vdots", size=30, color=DIM).move_to([1.35, ys[2], 0]),
            M("u_M", size=36, color=BLUE).move_to([1.35, ys[3], 0]),
        )
        u_head = T("概率", 22, DIM).move_to([1.35, 3.55, 0])
        self.play(FadeIn(u_head), LaggedStart(*[FadeIn(u, shift=LEFT * 0.2) for u in u_labels], lag_ratio=0.3),
                  run_time=1.6)
        self.until(self.end(7) - 1.6)   # 念到“第 M 抽就是 u_M”时
        self.play(Indicate(u_labels[3], color=GOLD, scale_factor=1.3), run_time=1.0)

        # 8 概率 v_M
        self.line(8)
        miss_leaf = chip(T("抽满 M 抽仍没中", 22), stroke=LOSS, pad=0.14).move_to([-0.6, -0.9, 0])
        e_ml = Line(miss_node.get_right(), miss_leaf.get_left(), color=LOSS, stroke_width=2)
        v_label = M("v_M", size=36, color=BLUE).move_to([1.35, -0.9, 0])
        self.play(Create(e_ml), FadeIn(miss_leaf, shift=RIGHT * 0.2), run_time=0.9)
        self.play(FadeIn(v_label, shift=LEFT * 0.2), run_time=0.7)

        # 9 每种情况的信仰变动
        self.line(9)
        g_head = T("信仰变动", 22, DIM).move_to([3.3, 3.55, 0])
        g_labels = VGroup(
            M("+1", size=36, color=GAIN).move_to([3.3, ys[0], 0]),
            M("+2", size=36, color=GAIN).move_to([3.3, ys[1], 0]),
            M(r"\vdots", size=30, color=DIM).move_to([3.3, ys[2], 0]),
            M("+M", size=36, color=GAIN).move_to([3.3, ys[3], 0]),
        )
        g_miss = M("M-C", size=36, color=LOSS).move_to([3.3, -0.9, 0])
        g_note = T("兑换要花 C 信仰", 20, DIM).next_to(g_miss, DOWN, buff=0.15)
        self.play(FadeIn(g_head), LaggedStart(*[FadeIn(g, shift=LEFT * 0.2) for g in g_labels], lag_ratio=0.3),
                  run_time=2.0)
        self.play(FadeIn(g_miss, shift=LEFT * 0.2), FadeIn(g_note), run_time=1.2)

        # 10 合成公式
        self.line(10)
        f1 = M("E", "=", r"\sum_{n=0}^{M}", "n", r"\,u_n", "+", "(M-C)", r"\,v_M", size=50)
        f1[3].set_color(GAIN)
        f1[6].set_color(LOSS)
        f1.move_to([0.4, -2.25, 0])
        self.play(
            FadeIn(VGroup(f1[0], f1[1], f1[2], f1[5])),
            TransformFromCopy(g_labels[3], f1[3]), TransformFromCopy(u_labels[3], f1[4]),
            TransformFromCopy(g_miss, f1[6]), TransformFromCopy(v_label, f1[7]),
            run_time=1.8,
        )

        # 11 还差最后一步
        self.line(11)
        tree = VGroup(root, root_t, hit_node, miss_node, e_hit, e_miss, leaves, edges, u_head, u_labels,
                      miss_leaf, e_ml, v_label, g_head, g_labels, g_miss, g_note)
        self.play(FadeOut(tree), f1.animate.scale(1.1).move_to([0, 2.2, 0]), run_time=1.3)

        # 12 辉玉十连：9 次有效抽，10 点信仰
        self.line(12)
        cards = ten_cards().move_to([0, -0.15, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in cards], lag_ratio=0.12), run_time=1.6)
        b9 = Brace(cards[:9], DOWN, color=BLUE, buff=0.12)
        b9_t = T("9 次有效抽卡", 24, BLUE).next_to(b9, DOWN, buff=0.1)
        gift_t = T("必得紫礼物", 22, PURPLE).next_to(cards[9], UP, buff=0.15)
        faith = chip(T("+10 信仰", 26, GOLD), stroke=GOLD).next_to(cards, RIGHT, buff=0.3)
        if faith.get_right()[0] > 6.9:
            faith.next_to(cards, UP, buff=0.15).align_to(cards, LEFT)
        self.play(GrowFromCenter(b9), FadeIn(b9_t), FadeIn(gift_t, shift=DOWN * 0.15), run_time=1.1)
        self.play(FadeIn(faith, scale=1.3), run_time=0.8)

        # 13 规划的基本单位是辉玉十连
        self.line(13)
        price = VGroup(M(r"1800", size=36, color=INK), T("辉玉", 24, DIM),
                       M(r"=\,200\times 9", size=36, color=INK)).arrange(RIGHT, buff=0.15)
        unit = chip(VGroup(T("规划的基本单位：辉玉十连", 26, GOLD), price).arrange(DOWN, buff=0.18),
                    stroke=GOLD).move_to([0, -2.0, 0])
        self.play(FadeOut(b9_t), FadeOut(b9), FadeIn(unit, shift=UP * 0.2), run_time=1.0)

        # 14 换成十连：n → 10n，M → 10N
        self.line(14)
        f2 = M("E", "=", r"\sum_{n=0}^{N}", "10n", r"\,u_n", "+", "(10N-C)", r"\,v_N", size=58)
        f2[3].set_color(GAIN)
        f2[6].set_color(LOSS)
        f2.move_to([0, 0.6, 0])
        legend = VGroup(
            VGroup(M("N", size=32, color=GOLD), T("给定十连数", 22, DIM)).arrange(RIGHT, buff=0.12),
            VGroup(M("u_n", size=32, color=BLUE), T("第 n 次十连首次命中的概率", 22, DIM)).arrange(RIGHT, buff=0.12),
            VGroup(M("v_N", size=32, color=BLUE), T("N 次十连仍未命中的概率", 22, DIM)).arrange(RIGHT, buff=0.12),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([0, -1.6, 0])
        self.play(FadeOut(cards), FadeOut(gift_t), FadeOut(faith), FadeOut(unit), run_time=0.8)
        self.play(*[ReplacementTransform(f1[i], f2[i]) for i in range(8)], run_time=1.8)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.15) for l in legend], lag_ratio=0.35), run_time=1.6)

        # 15 最终公式加框
        self.line(15)
        box = SurroundingRectangle(f2, color=GOLD, buff=0.28, corner_radius=0.12, stroke_width=4)
        self.play(Create(box), run_time=0.9)
        self.play(Flash(box.get_corner(UR), color=GOLD, line_length=0.35, num_lines=10), run_time=0.8)
        self.finish()


# ---------------------------------------------------------------------------
# 1-5 例题：常规单 UP，5 次十连
# ---------------------------------------------------------------------------
def ten_icon(k: int, size: float = 0.82) -> VGroup:
    box = RoundedRectangle(width=size, height=size, corner_radius=0.12, fill_color=PANEL, fill_opacity=1,
                           stroke_color=PURPLE, stroke_width=2.5)
    return VGroup(box, T(str(k), 24, DIM).move_to(box))


def mark_hit(icon: VGroup) -> Star:
    return Star(5, outer_radius=0.3, fill_color=GOLD, fill_opacity=1, stroke_width=0).move_to(icon)


def mark_miss(icon: VGroup) -> VGroup:
    return Cross(icon[0], stroke_color=LOSS, stroke_width=5, scale_factor=0.55)


class S1_5_Example(Narrated):
    SCENE_ID = "S1_5_Example"
    MAIN_X = 1.9      # 右侧主区中心

    def construct(self):
        mx = self.MAIN_X

        # 0 题目卡标题
        self.line(0)
        tag = chip(T("例题", 26, GOLD), stroke=GOLD).to_corner(UL, buff=0.45)
        self.play(FadeIn(tag, shift=RIGHT * 0.3), run_time=0.8)

        # 1 题目条件
        self.line(1)
        rows = VGroup(
            T("常规单 UP 池 · 想要 UP 角色", 26),
            VGroup(T("信仰价格", 26, DIM), M("C=150", size=40, color=LOSS)).arrange(RIGHT, buff=0.2),
            VGroup(T("单抽概率", 26, DIM), M(r"p=2.95\%", size=40, color=BLUE)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to([0, 0.6, 0])
        for r in rows:
            self.play(FadeIn(r, shift=UP * 0.2), run_time=0.7)
            self.wait(0.9)

        # 2 给 5 次十连，E = ?
        self.line(2)
        ask = VGroup(T("给定十连数", 26, DIM), M("N=5", size=40, color=GOLD)).arrange(RIGHT, buff=0.2)
        ask.next_to(rows, DOWN, aligned_edge=LEFT, buff=0.32)
        e_q = M("E=\\,?", size=64, color=GOLD).next_to(VGroup(rows, ask), DOWN, buff=0.6)
        self.play(FadeIn(ask, shift=UP * 0.2), run_time=0.7)
        self.play(Write(e_q), run_time=1.0)
        self.play(Indicate(e_q, color=GOLD), run_time=0.9)

        # 3 收进左栏，第一步
        self.line(3)
        card_body = VGroup(rows.copy(), ask.copy()).arrange(DOWN, aligned_edge=LEFT, buff=0.22).scale(0.72)
        card = chip(card_body, stroke=DIM, pad=0.25).next_to(tag, DOWN, aligned_edge=LEFT, buff=0.25)
        self.add(card[0])
        self.bring_to_back(card[0])
        card[0].set_opacity(0)
        self.play(ReplacementTransform(rows, card_body[0]), ReplacementTransform(ask, card_body[1]),
                  card[0].animate.set_fill(opacity=1).set_stroke(opacity=1), FadeOut(e_q), run_time=1.2)
        step1 = T("第一步：单抽概率 → 一次十连的概率", 28, INK).move_to([mx, 3.3, 0])
        self.play(FadeIn(step1, shift=DOWN * 0.2), run_time=0.8)

        # 4 9 次全不中
        self.line(4)
        cards = ten_cards(width=0.72, height=1.02, buff=0.12).move_to([mx, 1.6, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.25) for c in cards], lag_ratio=0.08), run_time=1.2)
        miss9 = VGroup(*[Cross(c, stroke_color=LOSS, stroke_width=4, scale_factor=0.5) for c in cards[:9]])
        self.play(LaggedStart(*[Create(x) for x in miss9], lag_ratio=0.12), run_time=1.6)
        f_q = M("(1-p)^9", size=48, color=LOSS).next_to(cards, DOWN, buff=0.45)
        f_q_t = T("9 次全不中", 24, DIM).next_to(f_q, RIGHT, buff=0.3)
        self.play(Write(f_q), FadeIn(f_q_t), run_time=1.2)

        # 5 p10 ≈ 0.236
        self.line(5)
        f_p10 = M("p_{10}", "=", "1-(1-p)^9", r"\approx", f"{D.P10:.3f}", size=52)
        f_p10[0].set_color(BLUE)
        f_p10[4].set_color(GOLD)
        f_p10.next_to(cards, DOWN, buff=0.45)
        self.play(FadeOut(f_q_t), TransformMatchingShapes(f_q, f_p10[2]), run_time=1.0)
        self.play(FadeIn(VGroup(f_p10[0], f_p10[1], f_p10[3], f_p10[4]), shift=LEFT * 0.2), run_time=0.9)
        self.play(Circumscribe(f_p10[4], color=GOLD), run_time=1.0)

        # 6 大约每 4 次十连出 1 次
        self.line(6)
        quad = VGroup(*[ten_icon(k + 1, 0.7) for k in range(4)]).arrange(RIGHT, buff=0.3)
        quad.next_to(f_p10, DOWN, buff=0.55)
        quad_star = mark_hit(quad[2])
        quad_t = T("≈ 每 4 次十连出 1 次", 26, GOLD).next_to(quad, RIGHT, buff=0.35)
        self.play(LaggedStart(*[FadeIn(q, scale=0.8) for q in quad], lag_ratio=0.15), run_time=0.9)
        self.play(GrowFromCenter(quad_star), FadeIn(quad_t), run_time=0.8)

        # 留在左栏的 p10 小记
        p10_note = VGroup(M(r"p_{10}\approx 0.236", size=34, color=BLUE),
                          M(r"1-p_{10}\approx 0.764", size=34, color=LOSS)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        p10_note.next_to(card, DOWN, aligned_edge=LEFT, buff=0.3)

        # 7 情况一：5 次全没中
        self.line(7)
        self.play(FadeOut(VGroup(cards, miss9, quad, quad_star, quad_t, step1)),
                  ReplacementTransform(f_p10, p10_note[0]), FadeIn(p10_note[1]), run_time=1.0)
        head_miss = T("情况一：5 次十连全没中", 28, LOSS).move_to([mx, 3.3, 0])
        row = VGroup(*[ten_icon(k + 1) for k in range(5)]).arrange(RIGHT, buff=0.35).move_to([mx, 2.1, 0])
        self.play(FadeIn(head_miss, shift=DOWN * 0.2),
                  LaggedStart(*[FadeIn(r, shift=UP * 0.2) for r in row], lag_ratio=0.1), run_time=1.0)
        xs = VGroup(*[mark_miss(r) for r in row])
        self.play(LaggedStart(*[Create(x) for x in xs], lag_ratio=0.2), run_time=1.2)

        # 8 v5 ≈ 0.26
        self.line(8)
        f_v5 = M("v_5", "=", "0.764^5", r"\approx", f"{D.V5:.2f}", size=50)
        f_v5[0].set_color(BLUE)
        f_v5[4].set_color(GOLD)
        f_v5.move_to([mx, 0.75, 0])
        self.play(Write(f_v5), run_time=1.6)

        # 9 +50 −150 = −100
        self.line(9)
        f_g = VGroup(
            VGroup(M("+50", size=46, color=GAIN), T("抽卡得到的信仰", 22, DIM)).arrange(DOWN, buff=0.1),
            VGroup(M("-150", size=46, color=LOSS), T("兑换花掉", 22, DIM)).arrange(DOWN, buff=0.1),
            VGroup(M("=-100", size=46, color=LOSS), T("净变动", 22, DIM)).arrange(DOWN, buff=0.1),
        ).arrange(RIGHT, buff=0.55, aligned_edge=UP).move_to([mx, -0.75, 0])
        for g in f_g:
            self.play(FadeIn(g, shift=UP * 0.2), run_time=0.7)
            self.wait(0.6)

        # 10 贡献 ≈ −26，记入左栏账本
        self.line(10)
        f_c = M("-100", r"\times", "0.26", r"\approx", "-26", size=54).move_to([mx, -2.2, 0])
        f_c[0].set_color(LOSS)
        f_c[2].set_color(GOLD)
        f_c[4].set_color(LOSS)
        self.play(Write(f_c), run_time=1.5)
        miss_num = M(f"{D.HAND_MISS:.0f}", size=38, color=LOSS)
        ledger_miss = chip(VGroup(T("没中部分", 22, DIM), miss_num).arrange(RIGHT, buff=0.25), stroke=LOSS, pad=0.16)
        ledger_miss.next_to(p10_note, DOWN, aligned_edge=LEFT, buff=0.4)
        self.play(TransformFromCopy(f_c[4], ledger_miss), run_time=1.0)

        # 11 情况二：第 1 次十连就出
        self.line(11)
        self.play(FadeOut(VGroup(head_miss, xs, f_v5, f_g, f_c)), run_time=0.7)
        head_hit = T("情况二：在第 n 次十连首次出货", 28, GAIN).move_to([mx, 3.3, 0])
        self.play(FadeIn(head_hit, shift=DOWN * 0.2), run_time=0.6)

        base_y, scale = -2.55, 0.6
        slot_x = [mx - 3.2 + 1.6 * k for k in range(5)]
        axis = Line([mx - 4.1, base_y, 0], [mx + 4.1, base_y, 0], color=DIM, stroke_width=2)
        slot_lbl = VGroup(*[T(f"第 {k + 1} 次", 20, DIM).move_to([slot_x[k], base_y - 0.3, 0]) for k in range(5)])
        bars, vals = VGroup(), VGroup()
        for k, term in enumerate(D.HIT_TERMS):
            bars.add(Rectangle(width=0.85, height=term * scale, fill_color=GAIN, fill_opacity=0.85,
                               stroke_width=0).move_to([slot_x[k], base_y, 0], aligned_edge=DOWN))
            vals.add(M(f"{term:.2f}", size=30, color=GAIN).next_to(bars[k], UP, buff=0.1))
        self.play(Create(axis), FadeIn(slot_lbl), run_time=0.6)

        def show_case(n: int, rt: float) -> VGroup:
            """演示第 n 次十连首次出货：前 n−1 次歪，第 n 次出。"""
            marks = VGroup()
            for k in range(n - 1):
                marks.add(mark_miss(row[k]))
            marks.add(mark_hit(row[n - 1]))
            dimmed = VGroup(*row[n:])
            self.play(FadeIn(marks, lag_ratio=0.2), dimmed.animate.set_opacity(0.25), run_time=rt)
            return marks

        def info_line(n: int) -> VGroup:
            prob = r"0.236" if n == 1 else (r"0.764\times 0.236" if n == 2 else rf"0.764^{{{n - 1}}}\times 0.236")
            return VGroup(T("概率", 22, DIM), M(prob, size=36, color=BLUE),
                          T("信仰", 22, DIM), M(f"+{10 * n}", size=36, color=GAIN)).arrange(RIGHT, buff=0.18)

        m1 = show_case(1, 0.8)
        info = info_line(1).move_to([mx, 1.15, 0])
        self.play(FadeIn(info, shift=UP * 0.15), run_time=0.6)
        self.play(GrowFromEdge(bars[0], DOWN), FadeIn(vals[0]), run_time=0.9)

        # 12 第 2 次才出
        self.line(12)
        self.play(FadeOut(m1), row.animate.set_opacity(1), run_time=0.4)
        m2 = show_case(2, 1.0)
        info2 = info_line(2).move_to(info)
        self.play(ReplacementTransform(info, info2), run_time=0.7)
        self.play(GrowFromEdge(bars[1], DOWN), FadeIn(vals[1]), run_time=0.9)

        # 13 以此类推到第 5 次
        self.line(13)
        marks_prev, info_prev = m2, info2
        for n in (3, 4, 5):
            self.play(FadeOut(marks_prev), row.animate.set_opacity(1), run_time=0.15)
            marks_prev = show_case(n, 0.35)
            info_n = info_line(n).move_to(info)
            self.play(ReplacementTransform(info_prev, info_n), GrowFromEdge(bars[n - 1], DOWN),
                      FadeIn(vals[n - 1]), run_time=0.5)
            info_prev = info_n

        # 14 合计 ≈ 18.33
        self.line(14)
        self.play(FadeOut(marks_prev), row.animate.set_opacity(1), run_time=0.3)
        total_t = VGroup(T("5 项合计", 26, DIM), M(rf"\approx {D.HAND_HIT:.2f}", size=48, color=GAIN))
        total_t.arrange(RIGHT, buff=0.2).move_to(info)
        self.play(FadeOut(info_prev), FadeIn(total_t),
                  LaggedStart(*[Indicate(b, color=GOLD, scale_factor=1.05) for b in bars], lag_ratio=0.15),
                  run_time=1.4)
        hit_num = M(f"+{D.HAND_HIT:.2f}", size=38, color=GAIN)
        ledger_hit = chip(VGroup(T("抽到部分", 22, DIM), hit_num).arrange(RIGHT, buff=0.25), stroke=GAIN, pad=0.16)
        ledger_hit.next_to(ledger_miss, DOWN, aligned_edge=LEFT, buff=0.25)
        self.play(TransformFromCopy(total_t[1], ledger_hit), run_time=1.0)

        # 15 18.33 − 26 = −7.67
        self.line(15)
        self.play(FadeOut(VGroup(head_hit, row, axis, slot_lbl, bars, vals, total_t)), run_time=0.7)
        final = M(f"{D.HAND_HIT:.2f}", "-", "26", "=", f"{D.HAND_NET:.2f}", size=80)
        final[0].set_color(GAIN)
        final[2].set_color(LOSS)
        final[4].set_color(LOSS)
        final.move_to([mx, 1.6, 0])
        self.play(TransformFromCopy(hit_num, final[0]), TransformFromCopy(miss_num, final[2]),
                  FadeIn(final[1]), run_time=1.2)
        self.play(FadeIn(final[3]), Write(final[4]), run_time=1.0)
        self.play(Circumscribe(final[4], color=LOSS, buff=0.15), run_time=1.0)

        # 16 策略复述
        self.line(16)
        strat = VGroup(*[chip(T(s, 24), stroke=DIM, pad=0.16)
                         for s in ("给 5 个十连", "抽到就停", "抽不到就换")]).arrange(RIGHT, buff=0.25)
        strat.move_to([mx, 0.0, 0])
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.2) for s in strat], lag_ratio=0.4), run_time=2.0)

        # 17 长期每次亏 7.67，加一个十连可能转正
        self.line(17)
        loss = VGroup(T("长期来看：每次大约", 26, DIM), M(r"-7.67", size=40, color=LOSS),
                      T("信仰", 26, DIM)).arrange(RIGHT, buff=0.15).move_to([mx, -1.15, 0])
        self.play(FadeIn(loss, shift=UP * 0.2), run_time=0.9)
        self.wait(1.6)
        tease = chip(VGroup(T("再加一个十连", 24), M(r"N=6\ \Rightarrow\ ?", size=38, color=GOLD))
                     .arrange(RIGHT, buff=0.25), stroke=GOLD, pad=0.16).move_to([mx, -2.3, 0])
        self.play(FadeIn(tease, shift=UP * 0.2), run_time=0.8)
        self.play(Indicate(tease, color=GOLD), run_time=1.0)

        # 18 思考题
        self.line(18)
        self.play(FadeOut(VGroup(final, strat, loss, tease)), run_time=0.7)
        quiz = chip(VGroup(T("思考题", 26, GOLD),
                           T("如果不考虑“抽到就停手”，", 28),
                           T("结果会偏高还是偏低？", 28)).arrange(DOWN, buff=0.2),
                    stroke=GOLD, pad=0.35).move_to([mx, 1.4, 0])
        self.play(FadeIn(quiz, scale=0.92), run_time=1.0)
        self.countdown(18, where=[mx, -1.0, 0])

        # 19 偏高：+11.02 vs −7.67
        self.line(19)
        naive = chip(VGroup(T("抽满不停", 24, DIM), M(f"+{D.NAIVE:.2f}", size=48, color=GAIN)).arrange(DOWN, buff=0.12),
                     stroke=LOSS, pad=0.25)
        real = chip(VGroup(T("抽到就停", 24, DIM), M(f"{D.HAND_NET:.2f}", size=48, color=LOSS)).arrange(DOWN, buff=0.12),
                    stroke=GAIN, pad=0.25)
        cmp = VGroup(naive, real).arrange(RIGHT, buff=2.2).move_to([mx, -1.1, 0])
        arrow = Arrow(real.get_left(), naive.get_right(), color=GOLD, buff=0.15, stroke_width=5)
        arrow_t = T("偏高", 28, GOLD).next_to(arrow, UP, buff=0.1)
        self.play(FadeIn(real, shift=UP * 0.2), run_time=0.7)
        self.play(FadeIn(naive, shift=UP * 0.2), GrowArrow(arrow), FadeIn(arrow_t), run_time=1.0)
        sign = T("连正负号都反了", 26, LOSS).next_to(cmp, DOWN, buff=0.35)
        self.play(FadeIn(sign), Wiggle(naive), run_time=1.2)

        # 20 原因：出货后不会再抽的十连被算成了收益
        self.line(20)
        self.play(FadeOut(VGroup(quiz, cmp, arrow, arrow_t, sign)), run_time=0.6)
        row2 = VGroup(*[ten_icon(k + 1) for k in range(5)]).arrange(RIGHT, buff=0.35).move_to([mx, 1.6, 0])
        star2 = mark_hit(row2[1])
        self.play(FadeIn(row2, lag_ratio=0.1), GrowFromCenter(star2), run_time=0.9)
        ghost = SurroundingRectangle(row2[2:], color=LOSS, buff=0.12, corner_radius=0.1)
        ghost_t = T("出货后根本不会抽", 24, LOSS).next_to(ghost, UP, buff=0.15)
        self.play(row2[2:].animate.set_opacity(0.3), Create(ghost), FadeIn(ghost_t), run_time=0.9)
        wrong = VGroup(T("朴素公式却把这 30 信仰也算进了收益", 26),
                       ).arrange(RIGHT).next_to(row2, DOWN, buff=0.6)
        self.play(FadeIn(wrong, shift=UP * 0.2), Indicate(ghost, color=LOSS), run_time=1.3)
        self.finish()


# ---------------------------------------------------------------------------
# 1-6 临界十连数：常规单 UP 曲线逐点画出
# ---------------------------------------------------------------------------
def curve_dots(axes, values, color, radius=0.07, upto=None):
    pts = VGroup(*[Dot(axes.c2p(n, v), radius=radius, color=color) for n, v in enumerate(values)])
    path = VMobject(stroke_color=color, stroke_width=3.5).set_points_as_corners(
        [axes.c2p(n, v) for n, v in enumerate(values)])
    return path, pts


class S1_6_Critical(Narrated):
    SCENE_ID = "S1_6_Critical"

    def construct(self):
        values = D.CURVES["常规单 UP"]
        axes, deco = e_axes(15, -160, 60, 40, width=10.4, height=5.0)
        VGroup(axes, deco).move_to([0.3, 0.35, 0])
        title = T("常规单 UP 池 · p = 2.95% · C = 150", 26, DIM).to_edge(UP, buff=0.3)

        # 0 把每个十连数的期望都算出来
        self.line(0)
        self.play(FadeIn(title), Create(axes), FadeIn(deco), run_time=1.6)

        # 1 0 到 15
        self.line(1)
        path, dots = curve_dots(axes, values, BLUE)
        self.play(FadeIn(dots[0], scale=1.5), run_time=0.5)

        # 2 −150 往上爬
        self.line(2)
        v0 = M("-150", size=30, color=LOSS).next_to(dots[0], RIGHT, buff=0.15)
        self.play(FadeIn(v0), run_time=0.4)
        self.play(Create(path, rate_func=linear),
                  LaggedStart(*[FadeIn(d, scale=1.5) for d in dots[1:]], lag_ratio=1.0, rate_func=linear),
                  run_time=2.6)

        # 3 5 → −7.66，6 → +4.15
        self.line(3)
        lab5 = M(f"{values[5]:.2f}", size=30, color=LOSS).next_to(axes.c2p(5, 0), UL, buff=0.12)
        lab6 = M(f"+{values[6]:.2f}", size=30, color=GAIN).next_to(dots[6], DR, buff=0.1)
        self.play(dots[5].animate.scale(1.8).set_color(LOSS), FadeIn(lab5), run_time=0.8)
        self.wait(1.0)
        self.play(dots[6].animate.scale(1.8).set_color(GAIN), FadeIn(lab6), run_time=0.8)

        # 4 −7.67 vs −7.66：舍入
        self.line(4)
        note = chip(VGroup(T("例题手算", 22, DIM), M("-7.67", size=32, color=LOSS), T("精确值", 22, DIM),
                           M(f"{values[5]:.2f}", size=32, color=LOSS)).arrange(RIGHT, buff=0.2),
                    stroke=DIM, pad=0.15).move_to([3.0, 2.2, 0])
        self.play(FadeIn(note, shift=DOWN * 0.15), run_time=0.8)

        # 5 临界十连数
        self.line(5)
        self.play(FadeOut(note), run_time=0.4)
        v5l = DashedLine(axes.c2p(5, -160), axes.c2p(5, 60), color=GOLD, stroke_width=2.5)
        v6l = DashedLine(axes.c2p(6, -160), axes.c2p(6, 60), color=GOLD, stroke_width=2.5)
        crit = chip(T("临界十连数：5 和 6", 30, GOLD, weight="BOLD"), stroke=GOLD, pad=0.2).move_to(axes.c2p(10.5, -50))
        self.play(Create(v5l), Create(v6l), run_time=0.9)
        self.play(FadeIn(crit, scale=0.9), Flash(axes.c2p(5.5, 0), color=GOLD, line_length=0.3), run_time=1.0)

        # 6 5：略亏
        self.line(6)
        side5 = VGroup(T("抽 5 个十连", 24, LOSS), T("每次约亏 7.66", 22, DIM), T("亏得不多", 22, DIM))
        side5.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        card5 = chip(side5, stroke=LOSS, pad=0.18).move_to([2.6, -1.1, 0])
        self.play(FadeIn(card5, shift=LEFT * 0.2), run_time=0.8)

        # 7 6：略赚
        self.line(7)
        side6 = VGroup(T("抽 6 个十连", 24, GAIN), T("每次约赚 4.15", 22, DIM), T("久了信仰会花不完", 22, DIM))
        side6.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        card6 = chip(side6, stroke=GAIN, pad=0.18).next_to(card5, RIGHT, buff=0.3)
        if card6.get_right()[0] > 6.4:
            VGroup(card5, card6).shift(LEFT * (card6.get_right()[0] - 6.4))
        self.play(FadeIn(card6, shift=LEFT * 0.2), run_time=0.8)

        # 8 一正一负互补
        self.line(8)
        self.play(Indicate(card5, color=LOSS, scale_factor=1.05), run_time=0.7)
        self.play(Indicate(card6, color=GAIN, scale_factor=1.05), run_time=0.7)

        # 9 越来越平：边际收益递减
        self.line(9)
        self.play(FadeOut(VGroup(card5, card6, lab5, lab6)), run_time=0.5)
        steps = VGroup()
        for n in (2, 8, 13):
            a, b = axes.c2p(n, values[n]), axes.c2p(n + 1, values[n + 1])
            rise = Line([b[0], a[1], 0], b, color=GOLD, stroke_width=5)
            run = Line(a, [b[0], a[1], 0], color=DIM, stroke_width=3)
            inc = T(f"+{values[n + 1] - values[n]:.1f}", 20, GOLD).next_to(run, DOWN, buff=0.08)
            steps.add(VGroup(run, rise, inc))
        self.play(LaggedStart(*[Create(s) for s in steps], lag_ratio=0.5), run_time=1.6)
        flat = T("多抽一次的收获越来越少", 24, GOLD).move_to(axes.c2p(10.5, -115))
        self.play(FadeIn(flat, shift=UP * 0.15), run_time=0.7)
        self.finish()


# ---------------------------------------------------------------------------
# 1-7 各卡池速览：换参数、曲线变形
# ---------------------------------------------------------------------------
class S1_7_Pools(Narrated):
    SCENE_ID = "S1_7_Pools"

    def show_pool(self, axes, values, color, crit, label, prev=None):
        path, dots = curve_dots(axes, values, color, radius=0.06)
        lines = VGroup(*[DashedLine(axes.c2p(n, axes.y_range[0]), axes.c2p(n, axes.y_range[1]),
                                    color=GOLD, stroke_width=2) for n in crit])
        tag = chip(VGroup(T(label, 24, color), T(f"临界 {crit[0]} / {crit[1]}", 24, GOLD)).arrange(RIGHT, buff=0.3),
                   stroke=color, pad=0.15).to_corner(UR, buff=0.35)
        if prev is None:
            self.play(Create(path), FadeIn(dots, lag_ratio=0.05), run_time=1.4)
        else:
            self.play(ReplacementTransform(prev[0], path), ReplacementTransform(prev[1], dots), run_time=1.4)
        self.play(Create(lines), FadeIn(tag), run_time=0.7)
        return VGroup(path, dots), lines, tag

    def construct(self):
        # 0 换池子曲线跟着变
        self.line(0)
        axes, deco = e_axes(15, -160, 60, 40, width=10.0, height=4.4)
        VGroup(axes, deco).move_to([0.2, 0.2, 0])
        base, base_dots = curve_dots(axes, D.CURVES["常规单 UP"], DIM, radius=0.05)
        base_t = T("常规单 UP", 20, DIM).next_to(base_dots[15], DOWN, buff=0.15).shift(LEFT * 0.2)
        self.play(Create(axes), FadeIn(deco), run_time=1.0)
        self.play(Create(base), FadeIn(base_dots), FadeIn(base_t), run_time=1.2)

        # 1 双 UP
        self.line(1)
        cur, lines, tag = self.show_pool(axes, D.CURVES["常规双 UP"], BLUE, D.CRIT["常规双 UP"], "常规双 UP")
        shift = VGroup(Arrow(axes.c2p(5.6, -100), axes.c2p(8.4, -100), color=BLUE, buff=0, stroke_width=4),
                       T("整体右移", 20, BLUE))
        shift[1].next_to(shift[0], UP, buff=0.08)
        self.play(GrowArrow(shift[0]), FadeIn(shift[1]), run_time=0.6)

        # 2 贵人：横轴要拉到 30
        self.line(2)
        self.play(FadeOut(VGroup(lines, tag, shift, base, base_dots, base_t)), run_time=0.4)
        axes2, deco2 = e_axes(30, -320, 120, 80, width=10.0, height=4.4, x_step=5)
        VGroup(axes2, deco2).move_to(VGroup(axes, deco))
        self.play(ReplacementTransform(axes, axes2), ReplacementTransform(deco, deco2), FadeOut(cur), run_time=1.0)
        cur, lines, tag = self.show_pool(axes2, D.CURVES["贵人"], PURPLE, D.CRIT["贵人"], "贵人  p = 1%  C = 300")

        # 3 联动 4UP
        self.line(3)
        self.play(FadeOut(VGroup(lines, tag)), run_time=0.3)
        axes3, deco3 = e_axes(15, -160, 60, 40, width=10.0, height=4.4)
        VGroup(axes3, deco3).move_to(VGroup(axes2, deco2))
        self.play(ReplacementTransform(axes2, axes3), ReplacementTransform(deco2, deco3), FadeOut(cur), run_time=0.9)
        cur, lines, tag = self.show_pool(axes3, D.CURVES["联动 4UP"], BLUE, D.CRIT["联动 4UP"], "联动 4UP 单个角色")

        # 4 头像框
        self.line(4)
        self.play(FadeOut(VGroup(lines, tag)), run_time=0.3)
        axes4, deco4 = e_axes(10, -100, 40, 20, width=10.0, height=4.4)
        VGroup(axes4, deco4).move_to(VGroup(axes3, deco3))
        self.play(ReplacementTransform(axes3, axes4), ReplacementTransform(deco3, deco4), FadeOut(cur), run_time=0.9)
        cur, lines, tag = self.show_pool(axes4, D.CURVES["头像框"], GOLD, D.CRIT["头像框"], "头像框  p = 0.9%  C = 100")

        # 5 普通装扮 5UP 平分
        self.line(5)
        self.play(FadeOut(VGroup(lines, tag)), run_time=0.3)
        axes5, deco5 = e_axes(5, -50, 30, 10, width=10.0, height=4.4)
        VGroup(axes5, deco5).move_to(VGroup(axes4, deco4))
        self.play(ReplacementTransform(axes4, axes5), ReplacementTransform(deco4, deco5), FadeOut(cur), run_time=0.9)
        cols = {3: GAIN, 4: BLUE, 5: LOSS}
        no_frame = VGroup()
        for n in (3, 4, 5):
            pth, dts = curve_dots(axes5, D.DRESS_CURVES[("无框", n)], cols[n], radius=0.06)
            no_frame.add(VGroup(pth, dts))
        leg = VGroup(*[VGroup(Line(ORIGIN, RIGHT * 0.4, color=cols[n], stroke_width=4), T(f"{n} 个 UP", 20, DIM))
                       .arrange(RIGHT, buff=0.12) for n in (3, 4, 5)]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        leg.move_to(axes5.c2p(1.0, 18))
        lines5 = VGroup(*[DashedLine(axes5.c2p(n, -50), axes5.c2p(n, 30), color=GOLD, stroke_width=2) for n in (3, 4)])
        tag5 = chip(VGroup(T("装扮（无头像框）C = 50", 24, S1_1_Probability.ROSE), T("临界 3 / 4", 24, GOLD))
                    .arrange(RIGHT, buff=0.3), stroke=S1_1_Probability.ROSE, pad=0.15).to_corner(UR, buff=0.35)
        self.play(LaggedStart(*[Create(c) for c in no_frame], lag_ratio=0.3), FadeIn(leg), run_time=1.6)
        self.play(Create(lines5), FadeIn(tag5), run_time=0.7)

        # 6 有头像框 3UP：临界 2 / 3
        self.line(6)
        with_frame = VGroup()
        for n in (3, 4, 5):
            pth, dts = curve_dots(axes5, D.DRESS_CURVES[("有框", n)], cols[n], radius=0.06)
            with_frame.add(VGroup(pth, dts))
        tag6 = chip(VGroup(T("装扮（有头像框）", 24, S1_1_Probability.ROSE), T("3 个 UP：临界 2 / 3", 24, GOLD))
                    .arrange(RIGHT, buff=0.3), stroke=S1_1_Probability.ROSE, pad=0.15).to_corner(UR, buff=0.35)
        line2 = VGroup(*[DashedLine(axes5.c2p(n, -50), axes5.c2p(n, 30), color=GOLD, stroke_width=3) for n in (2, 3)])
        self.play(*[ReplacementTransform(a, b) for a, b in zip(no_frame, with_frame)],
                  ReplacementTransform(tag5, tag6), FadeOut(lines5), run_time=1.4)
        self.play(Create(line2), Indicate(with_frame[0], color=GAIN), run_time=1.0)

        # 7 汇总表
        self.line(7)
        self.play(FadeOut(VGroup(axes5, deco5, with_frame, leg, line2, tag6)), run_time=0.6)
        rows = [("常规单 UP", "2.95%", "150", "5 / 6"), ("常规双 UP", "1.475%", "150", "7 / 8"),
                ("贵人", "1%", "300", "14 / 15"), ("联动 4UP", "0.7375%", "150", "10 / 11"),
                ("头像框", "0.9%", "100", "7 / 8"), ("普通装扮", "1.4%–3.2%", "50", "2 / 3 ~ 3 / 4")]
        table = VGroup()
        header = VGroup(*[T(h, 22, DIM) for h in ("目标", "单抽概率", "信仰价格", "临界十连数")])
        table.add(header)
        for r in rows:
            color = GOLD if r[0] in ("贵人", "联动 4UP") else INK
            table.add(VGroup(T(r[0], 24), T(r[1], 24), T(r[2], 24), T(r[3], 24, color)))
        widths = [2.6, 2.6, 2.0, 3.0]
        for row in table:
            x = -sum(widths) / 2
            for cell, w in zip(row, widths):
                cell.move_to([x + w / 2, 0, 0])
                x += w
        table.arrange(DOWN, buff=0.22).move_to([0, 0.35, 0])
        rule = Line(table[0].get_left() + LEFT * 0.2, table[0].get_right() + RIGHT * 0.2, color=DIM,
                    stroke_width=1.5).next_to(table[0], DOWN, buff=0.1)
        self.play(FadeIn(table[0]), Create(rule), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.15) for r in table[1:]], lag_ratio=0.25), run_time=2.2)
        hl = SurroundingRectangle(VGroup(*[table[i][3] for i in (1, 2, 3, 4)]), color=GOLD, buff=0.12, corner_radius=0.08)
        self.play(Create(hl), run_time=0.8)

        # 8 氪金玩家的专利
        self.line(8)
        end = chip(T("抽卡规划，终究是氪金玩家的专利", 30, GOLD), stroke=GOLD, pad=0.25).move_to([0, -2.5, 0])
        self.play(FadeIn(end, shift=UP * 0.2), run_time=0.9)
        self.finish()


# ---------------------------------------------------------------------------
# 1-8 揭晓开场问题：12 个十连的最优分配
# ---------------------------------------------------------------------------
class S1_8_Answer(Narrated):
    SCENE_ID = "S1_8_Answer"

    def construct(self):
        total = D.TOTAL_TENS
        # 0 回到开头
        self.line(0)
        collab = pool_card("联动池", "1 个联动角色", BLUE, w=3.0, h=1.6).move_to([-4.6, 2.3, 0])
        noble = pool_card("贵人池", "1 个贵人角色", PURPLE, w=3.0, h=1.6).move_to([4.6, 2.3, 0])
        k = ValueTracker(6)
        bar = always_redraw(lambda: split_bar(int(round(k.get_value())), total, 6.0, BLUE, PURPLE, h=0.42)
                            .move_to([0, 2.3, 0]))
        self.play(FadeIn(collab, shift=RIGHT * 0.3), FadeIn(noble, shift=LEFT * 0.3), FadeIn(bar), run_time=1.2)

        # 1 只有一个池子：期望固定
        self.line(1)
        one = T("只有一个池子：12 个十连的期望是定值", 24, DIM).move_to([0, 1.2, 0])
        self.play(FadeIn(one), run_time=0.7)

        # 2 联动 k，贵人 12 − k
        self.line(2)
        f = M(r"E_{\text{总}}(k)", "=", r"E_{\text{联动}}(k)", "+", r"E_{\text{贵人}}(12-k)", size=44,
              tex_template=TexTemplateLibrary.ctex)
        f[2].set_color(BLUE)
        f[4].set_color(PURPLE)
        f.move_to([0, 1.2, 0])
        self.play(FadeOut(one), Write(f), run_time=1.6)
        self.play(k.animate.set_value(3), run_time=0.8)
        self.play(k.animate.set_value(9), run_time=0.8)

        # 3 每种分法查两个池子的期望：手绘柱状图（纵轴 −300 ~ −150，底边在 −300）
        self.line(3)
        lo, hi = -300, -150
        cx, base_y, h, step = -0.35, -2.3, 2.75, 0.8      # 13 根柱子，间距 0.8
        xs = [cx + (i - total / 2) * step for i in range(total + 1)]

        def y_of(v):
            return base_y + (v - lo) / (hi - lo) * h

        grid = VGroup()
        for v in range(lo, hi + 1, 50):
            grid.add(DashedLine([xs[0] - 0.5, y_of(v), 0], [xs[-1] + 0.5, y_of(v), 0], color=DIM,
                                stroke_width=1, stroke_opacity=0.35 if v > lo else 0.9, dash_length=0.08))
            grid.add(T(str(v), 18, DIM).next_to([xs[0] - 0.5, y_of(v), 0], LEFT, buff=0.12))
        xl = VGroup(*[T(str(i), 18, DIM).move_to([xs[i], base_y - 0.22, 0]) for i in range(total + 1)])
        xn = T("联动池十连数 k（贵人池 = 12 − k）", 20, DIM).next_to(xl, DOWN, buff=0.12)
        self.play(f.animate.scale(0.75).move_to([0, 1.25, 0]), FadeIn(grid), FadeIn(xl), FadeIn(xn), run_time=1.4)

        # 4 先猜一猜（思考题）
        self.line(4)
        self.play(k.animate.set_value(6), run_time=0.6)
        self.countdown(4, where=[cx, y_of(-225), 0], radius=0.65)

        # 5 一个个试
        self.line(5)
        bars, vals = VGroup(), VGroup()
        for i in range(total + 1):
            v = D.SPLIT[i]
            b = Rectangle(width=0.5, height=y_of(v) - base_y, stroke_width=0, fill_color=DIM, fill_opacity=0.7)
            b.move_to([xs[i], base_y, 0], aligned_edge=DOWN)
            bars.add(b)
            vals.add(T(f"{v:.0f}", 17, DIM).next_to(b, UP, buff=0.06))
        rt = self.end(5) - self.now - 0.2
        steps = [AnimationGroup(GrowFromEdge(bars[i], DOWN), FadeIn(vals[i])) for i in range(total + 1)]
        self.play(LaggedStart(*steps, lag_ratio=0.6), k.animate.set_value(0), run_time=max(rt, 2.0))

        # 6 答案：k = 3。公式换成答案卡片
        self.line(6)
        best = D.BEST_K
        self.play(k.animate.set_value(best), bars[best].animate.set_fill(GAIN, opacity=0.95),
                  vals[best].animate.set_color(GAIN), run_time=0.9)
        ans = chip(VGroup(T("联动 3 + 贵人 9", 28, GAIN, weight="BOLD"),
                          M(f"{D.SPLIT[best]:.2f}", size=40, color=GAIN)).arrange(RIGHT, buff=0.35),
                   stroke=GAIN, pad=0.2).move_to([0, 1.25, 0])
        link = Arrow(ans.get_bottom(), vals[best].get_top(), buff=0.1, color=GAIN, stroke_width=3, tip_length=0.16)
        self.play(ReplacementTransform(f, ans), run_time=0.8)
        self.play(GrowArrow(link), Flash(bars[best].get_top(), color=GAIN, line_length=0.3), run_time=0.8)

        # 7 全砸联动最差：差距箭头放在最右侧柱子外面
        self.line(7)
        worst = total
        self.play(bars[worst].animate.set_fill(LOSS, opacity=0.95), vals[worst].animate.set_color(LOSS), run_time=0.7)
        gx = xs[worst] + 0.55
        ref = DashedLine([xs[best], y_of(D.SPLIT[best]), 0], [gx, y_of(D.SPLIT[best]), 0], color=GAIN,
                         stroke_width=1.5, dash_length=0.06)
        gap = DoubleArrow([gx, y_of(D.SPLIT[best]), 0], [gx, y_of(D.SPLIT[worst]), 0],
                          color=LOSS, buff=0, stroke_width=3, tip_length=0.15)
        gap_t = VGroup(T("多亏", 20, LOSS), T(f"{D.SPLIT[best] - D.SPLIT[worst]:.0f}", 24, LOSS, weight="BOLD"))
        gap_t.arrange(DOWN, buff=0.05).next_to(gap, RIGHT, buff=0.1)
        self.play(Create(ref), GrowFromCenter(gap), FadeIn(gap_t), run_time=1.0)

        # 8 最优仍是负的：顶部的卡池行换成结论
        self.line(8)
        neg = chip(T("最优解也是负的：两个都要，信仰注定要往外掏", 28, LOSS), stroke=LOSS, pad=0.2)
        neg.move_to([0, 2.45, 0])
        self.play(FadeOut(VGroup(collab, noble)), FadeOut(bar), FadeIn(neg, shift=DOWN * 0.15), run_time=0.9)

        # 9 少掏一点
        self.line(9)
        less = chip(T("我们能做的，是让它少掏一点", 30, GOLD), stroke=GOLD, pad=0.2).move_to(neg)
        self.play(ReplacementTransform(neg, less), Indicate(ans, color=GAIN), run_time=1.2)
        self.finish()


# ---------------------------------------------------------------------------
# 1-9 小结与过渡
# ---------------------------------------------------------------------------
class S1_9_Summary(Narrated):
    SCENE_ID = "S1_9_Summary"

    def construct(self):
        # 0 三句话
        self.line(0)
        head = T("本视频的三句话", 34, GOLD, weight="BOLD").to_edge(UP, buff=0.6)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.8)

        pts = [("1", "信仰变动期望：衡量策略长期是赚还是亏"),
               ("2", "临界十连数：E 由负转正处，最合理的抽卡量"),
               ("3", "概率越低、价格越高，临界十连数越大")]
        items = VGroup()
        for n, text in pts:
            badge = VGroup(Circle(radius=0.3, fill_color=GOLD, fill_opacity=1, stroke_width=0),
                           T(n, 26, BG, weight="BOLD"))
            badge[1].move_to(badge[0])
            items.add(VGroup(badge, T(text, 28)).arrange(RIGHT, buff=0.35))
        items.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, 0.2, 0])

        # 1-3 逐条出现
        for i in range(3):
            self.line(1 + i)
            self.play(FadeIn(items[i], shift=RIGHT * 0.3), run_time=0.8)

        # 4 只讨论了一个目标
        self.line(4)
        self.play(items.animate.set_opacity(0.35).shift(UP * 0.95), head.animate.set_opacity(0.35), run_time=0.8)
        single = chip(T("目前：只要 1 个目标", 28), stroke=DIM, pad=0.2).move_to([0, -1.3, 0])
        self.play(FadeIn(single, shift=UP * 0.2), run_time=0.7)

        # 5 双 UP 都要？4 个全要？
        self.line(5)
        multi = VGroup(chip(T("双 UP 两个都要？", 26, BLUE), stroke=BLUE, pad=0.16),
                       chip(T("联动 4 个全都要？", 26, PURPLE), stroke=PURPLE, pad=0.16)).arrange(RIGHT, buff=0.6)
        multi.move_to([0, -1.3, 0])
        self.play(ReplacementTransform(single, multi), run_time=1.0)

        # 6 马尔科夫链，下个视频见
        self.line(6)
        states = VGroup(*[VGroup(Circle(radius=0.42, stroke_color=c, stroke_width=4, fill_color=PANEL, fill_opacity=1),
                                 M(f"S_{i}", size=34, color=c))
                          for i, c in enumerate(STATE_COLORS[:3])])
        for s in states:
            s[1].move_to(s[0])
        states.arrange(RIGHT, buff=1.3).move_to([0, -1.3, 0])
        arrows = VGroup(*[Arrow(states[i].get_right(), states[i + 1].get_left(), buff=0.08, color=DIM, stroke_width=3)
                          for i in range(2)])
        nxt = T("下个视频：马尔科夫链", 30, GOLD, weight="BOLD").next_to(states, DOWN, buff=0.45)
        self.play(FadeOut(multi), LaggedStart(*[GrowFromCenter(s) for s in states], lag_ratio=0.3),
                  LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.3), run_time=1.6)
        self.play(FadeIn(nxt, shift=UP * 0.2), run_time=0.8)
        self.finish()
