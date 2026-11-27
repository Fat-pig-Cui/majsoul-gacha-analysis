"""画面数字的唯一来源：全部由 ../plot.py 的函数算出，不手抄表格。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plot import (  # noqa: E402
    EFFECTIVE_DRAWS, critical_interval, multi_target_curve, one_target_curve,
    state_distributions, strategy_distribution, verify,
)

verify()

# ---------- 例题：常规单 UP，C=150，p=2.95%，N=5 ----------
P1 = 0.0295
C1 = 150
N_EX = 5
P10 = 1 - (1 - P1) ** EFFECTIVE_DRAWS          # ≈ 0.236
Q10 = 1 - P10                                    # ≈ 0.764
V5 = Q10 ** N_EX                                 # ≈ 0.26
MISS_PART = (10 * N_EX - C1) * V5                # ≈ -25.99
HIT_TERMS = [10 * n * P10 * Q10 ** (n - 1) for n in range(1, N_EX + 1)]
HIT_PART = sum(HIT_TERMS)                        # ≈ 18.33
NAIVE = 10 * N_EX * (1 - V5) + (10 * N_EX - C1) * V5   # 抽满不停：≈ +11.02
CURVE_1UP = one_target_curve(P1, C1, 10)

# 原文按两位小数手算（0.236、0.26），所以手算结果是 -7.67，表格精确值是 -7.66
HAND_MISS = round((10 * N_EX - C1) * round(V5, 2), 2)      # -26.0
HAND_HIT = round(HIT_PART, 2)                               # 18.33
HAND_NET = round(HAND_HIT + HAND_MISS, 2)                   # -7.67

assert abs(HAND_NET - (-7.67)) < 1e-9, HAND_NET
assert round(NAIVE, 2) == 11.02, NAIVE
assert critical_interval(CURVE_1UP) == (5, 6)

# ---------- 1-6 / 1-7：各卡池的单目标曲线 ----------
# (显示名, 单抽概率, 信仰价格, 画到的最大十连数, 颜色键)
POOLS = [
    ("常规单 UP", 0.0295, 150, 15),
    ("常规双 UP", 0.01475, 150, 15),
    ("贵人", 0.01, 300, 30),
    ("联动 4UP", 0.007375, 150, 15),
    ("头像框", 0.009, 100, 10),
]
DRESS = {   # 非头像框装扮：(是否有头像框, 总 UP 数) -> 单抽概率
    ("无框", 3): 0.0245, ("无框", 4): 0.018375, ("无框", 5): 0.0147,
    ("有框", 3): 0.03225, ("有框", 4): 0.0215, ("有框", 5): 0.016125,
}
CURVES = {name: one_target_curve(p, c, m) for name, p, c, m in POOLS}
CRIT = {name: critical_interval(v) for name, v in CURVES.items()}
DRESS_CURVES = {k: one_target_curve(p, 50, 5) for k, p in DRESS.items()}
DRESS_CRIT = {k: critical_interval(v) for k, v in DRESS_CURVES.items()}

assert CRIT == {"常规单 UP": (5, 6), "常规双 UP": (7, 8), "贵人": (14, 15), "联动 4UP": (10, 11), "头像框": (7, 8)}
assert DRESS_CRIT[("无框", 5)] == (3, 4) and DRESS_CRIT[("有框", 3)] == (2, 3)

# ---------- 1-0 / 1-8：12 个十连分给联动和贵人 ----------
TOTAL_TENS = 12
COLLAB = one_target_curve(0.007375, 150, TOTAL_TENS)
NOBLE = one_target_curve(0.01, 300, TOTAL_TENS)
SPLIT = [COLLAB[k] + NOBLE[TOTAL_TENS - k] for k in range(TOTAL_TENS + 1)]   # 联动抽 k 个
BEST_K = max(range(TOTAL_TENS + 1), key=SPLIT.__getitem__)
assert BEST_K == 3 and round(SPLIT[3], 2) == -163.23 and round(SPLIT[12], 2) == -282.03

# =========================== 下半部分（进阶篇） ===========================
from plot import count_transition_table  # noqa: E402

N_MAX = 30
P_DUAL = 0.01475           # 常规双 UP 每个角色
P_LINK = 0.007375          # 联动 4UP 每个角色
P_FRAME = 0.009            # 头像框
P_DRESS5F = 0.016125       # 5UP 有头像框时的其他装扮


def qk(k: int, p: float) -> float:
    """一次十连里 k 个指定目标一个都不出的概率。"""
    return (1 - k * p) ** EFFECTIVE_DRAWS


# ---------- 2-1 ~ 2-4：常规双 UP 全都要 ----------
DUAL_S = state_distributions(2, P_DUAL, N_MAX)               # DUAL_S[N] = [S0, S1, S2]
DUAL_E = multi_target_curve([P_DUAL] * 2, [150] * 2, N_MAX)
DUAL_DE = [DUAL_E[n + 1] - DUAL_E[n] for n in range(N_MAX)]  # ΔE(N) = E(N+1) - E(N)
DQ1, DQ2 = qk(1, P_DUAL), qk(2, P_DUAL)
DR = {"00": DQ2, "01": 2 * (DQ1 - DQ2), "02": 1 - 2 * DQ1 + DQ2, "11": DQ1, "12": 1 - DQ1}
A0 = DR["01"] * 150 + DR["02"] * 300          # ≈ 37.55
A1 = DR["12"] * 150                            # ≈ 18.78
B0 = [s[0] * (10 + A0) for s in DUAL_S[:N_MAX]]   # ΔE 中来自 S0 的部分
B1 = [s[1] * (10 + A1) for s in DUAL_S[:N_MAX]]   # ΔE 中来自 S1 的部分
SINGLE_DE = [CURVE_1UP[n + 1] - CURVE_1UP[n] for n in range(len(CURVE_1UP) - 1)]

assert critical_interval(DUAL_E) == (10, 11)
assert max(abs(a + b - d) for a, b, d in zip(B0, B1, DUAL_DE)) < 1e-9
assert max(n for n in range(N_MAX) if DUAL_DE[n] > 10) == 12      # ΔE 在 12→13 之后跌破 10
assert round(A0, 2) == 37.55 and round(A1, 2) == 18.78
assert max(range(N_MAX + 1), key=lambda n: DUAL_S[n][1]) == 5

# ---------- 2-5 ~ 2-7：联动 4UP ----------
LINK2_S = state_distributions(2, P_LINK, N_MAX)
LINK2_E = multi_target_curve([P_LINK] * 2, [150] * 2, N_MAX)
LINK3_E = multi_target_curve([P_LINK] * 3, [150] * 3, N_MAX)
LINK4_S = state_distributions(4, P_LINK, N_MAX)
LINK4_E = multi_target_curve([P_LINK] * 4, [150] * 4, N_MAX)
STRAT = strategy_distribution()            # 0 信仰开局、全都要：[抽0井4, 抽1井3, 抽2井2, 抽3井1, 抽4井0]
assert critical_interval(LINK2_E) == (13, 14)
assert critical_interval(LINK3_E) == (16, 17)
assert critical_interval(LINK4_E) == (18, 19)
assert round(STRAT[4] * 100, 1) == 16.8 and round(STRAT[3] * 100, 1) == 74.2 and round(STRAT[2] * 100, 1) == 9.0
assert STRAT[0] + STRAT[1] < 0.0005

# ---------- 2-8 ~ 2-10：混合、毕业、练习 ----------
MIXED_E = multi_target_curve([P_LINK, P_FRAME], [150, 100], N_MAX)
GRAD_E = multi_target_curve([P_LINK] * 4 + [P_FRAME] + [P_DRESS5F] * 4, [150] * 4 + [100] + [50] * 4, N_MAX)
EXERCISE_E = multi_target_curve([P_LINK] * 2 + [P_DRESS5F], [150, 150, 50], N_MAX)
assert critical_interval(MIXED_E) == (12, 13)
assert critical_interval(GRAD_E) == (19, 20)
assert critical_interval(EXERCISE_E) == (13, 14)

# 2-10 汇总：(名称, 临界十连数, 是否多目标)
SUMMARY = [
    ("装扮（5UP 无框）", DRESS_CRIT[("无框", 5)], False),
    ("常规单 UP", CRIT["常规单 UP"], False),
    ("头像框", CRIT["头像框"], False),
    ("常规双 UP 单个", CRIT["常规双 UP"], False),
    ("联动单个角色", CRIT["联动 4UP"], False),
    ("贵人", CRIT["贵人"], False),
    ("常规双 UP 全都要", critical_interval(DUAL_E), True),
    ("联动角色 + 头像框", critical_interval(MIXED_E), True),
    ("联动特定两个", critical_interval(LINK2_E), True),
    ("联动特定三个", critical_interval(LINK3_E), True),
    ("联动全都要", critical_interval(LINK4_E), True),
    ("联动毕业（9 个目标）", critical_interval(GRAD_E), True),
]
