#!/usr/bin/env python3
"""雀魂卡池概率与信仰变动期望的统一计算脚本。

模型约定：辉玉十连包含 9 次有效抽卡，但增加 10 点信仰；抽到全部目标
后立即停止，未完成时在给定十连数结束后用信仰兑换剩余目标。

用法：
    python3 plot.py                 # 打印主要模型结果
    python3 plot.py --plots          # 同时重绘 Markdown 使用的图片
    python3 plot.py --verify         # 运行数值一致性校验
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path
from typing import Sequence


EFFECTIVE_DRAWS = 9
FAITH_PER_TEN = 10


def one_target_curve(p: float, faith_price: float, max_tens: int) -> list[float]:
    """计算单目标在 0..max_tens 次十连下的信仰变动期望。"""
    ten_hit = 1.0 - (1.0 - p) ** EFFECTIVE_DRAWS
    no_hit = 1.0
    hit_expectation = 0.0
    result = [-float(faith_price)]
    for n in range(1, max_tens + 1):
        hit_at_n = no_hit * ten_hit
        hit_expectation += FAITH_PER_TEN * n * hit_at_n
        no_hit *= 1.0 - ten_hit
        result.append(hit_expectation + (FAITH_PER_TEN * n - faith_price) * no_hit)
    return result


def critical_interval(values: Sequence[float]) -> tuple[int, int] | None:
    """返回 E(N) 首次由负变正的相邻十连数。"""
    for n in range(1, len(values)):
        if values[n - 1] < 0.0 < values[n]:
            return n - 1, n
    return None


def _transition_for_mask(mask: int, target_probs: Sequence[float]) -> dict[int, float]:
    """一次十连后从 mask 到各 mask 的概率。

    每次有效抽卡至多获得一个目标；已获得目标再次出现仍留在原状态。
    """
    states: dict[int, float] = {mask: 1.0}
    for _ in range(EFFECTIVE_DRAWS):
        next_states: dict[int, float] = defaultdict(float)
        for current, probability in states.items():
            unowned_total = sum(
                p for index, p in enumerate(target_probs) if not (current >> index) & 1
            )
            next_states[current] += probability * (1.0 - unowned_total)
            for index, p in enumerate(target_probs):
                if not (current >> index) & 1 and p:
                    next_states[current | (1 << index)] += probability * p
        states = dict(next_states)
    return states


def multi_target_curve(
    target_probs: Sequence[float],
    faith_prices: Sequence[float],
    max_tens: int,
) -> list[float]:
    """计算多个目标的信仰变动期望。

    状态是已获得目标的 bitmask，统一覆盖双 UP、混合目标和毕业模型，
    避免为每种目标数量维护一份容易漂移的手写转移矩阵。
    """
    if len(target_probs) != len(faith_prices):
        raise ValueError("target_probs 和 faith_prices 长度必须一致")
    if not target_probs:
        raise ValueError("至少需要一个目标")
    if any(p < 0 or p > 1 for p in target_probs):
        raise ValueError("目标概率必须在 [0, 1] 内")
    if any(c < 0 for c in faith_prices):
        raise ValueError("信仰价格不能为负")

    full = (1 << len(target_probs)) - 1
    transitions = {
        mask: _transition_for_mask(mask, target_probs)
        for mask in range(full)
    }
    distribution = {0: 1.0}
    completion_expectation = 0.0
    result = [-float(sum(faith_prices))]

    for n in range(1, max_tens + 1):
        next_distribution: dict[int, float] = defaultdict(float)
        for mask, probability in distribution.items():
            if mask == full:
                next_distribution[full] += probability
                continue
            for next_mask, transition_probability in transitions[mask].items():
                next_distribution[next_mask] += probability * transition_probability

        completed_now = next_distribution.get(full, 0.0) - distribution.get(full, 0.0)
        completion_expectation += FAITH_PER_TEN * n * completed_now
        incomplete_expectation = 0.0
        for mask, probability in next_distribution.items():
            if mask != full:
                remaining_cost = sum(
                    faith_prices[index]
                    for index in range(len(target_probs))
                    if not (mask >> index) & 1
                )
                incomplete_expectation += (
                    FAITH_PER_TEN * n - remaining_cost
                ) * probability
        result.append(completion_expectation + incomplete_expectation)
        distribution = dict(next_distribution)
    return result


def count_transition_table(target_count: int, p: float) -> list[list[float]]:
    """返回已获得 m 种时，一次十连后获得 j 种的概率表。"""
    table: list[list[float]] = []
    for m in range(target_count + 1):
        starting_mask = (1 << m) - 1
        transitions = _transition_for_mask(starting_mask, [p] * target_count)
        row = [0.0] * (target_count + 1)
        for mask, probability in transitions.items():
            row[bin(mask).count("1")] += probability
        table.append(row)
    return table


def state_distributions(target_count: int, p: float, max_tens: int) -> list[list[float]]:
    """各次十连后，已获得 0..target_count 个等价目标的概率。"""
    transition = count_transition_table(target_count, p)
    distributions = [[1.0] + [0.0] * target_count]
    for _ in range(max_tens):
        previous = distributions[-1]
        distributions.append([
            sum(mass * row[j] for mass, row in zip(previous, transition))
            for j in range(target_count + 1)
        ])
    return distributions


def strategy_distribution(
    initial_faith: int = 0,
    target_count: int = 4,
    p: float = 0.007375,
    target_faith: int = 150,
) -> list[float]:
    """按“有足够信仰就停止兑换，否则继续十连”计算抽井分类概率。"""
    transition = count_transition_table(target_count, p)
    active: dict[tuple[int, int], float] = {(0, 0): 1.0}
    stopped = [0.0] * (target_count + 1)

    while active:
        next_active: dict[tuple[int, int], float] = defaultdict(float)
        for (tens, owned), probability in active.items():
            if (
                owned == target_count
                or initial_faith + FAITH_PER_TEN * tens
                >= target_faith * (target_count - owned)
            ):
                stopped[owned] += probability
                continue
            for new_owned, transition_probability in enumerate(transition[owned]):
                if transition_probability:
                    next_active[(tens + 1, new_owned)] += probability * transition_probability
        active = dict(next_active)
    return stopped


def _models() -> tuple[list[dict], list[dict]]:
    """返回单目标和多目标模型配置。"""
    single = [
        {"name": "常规单UP", "p": 0.0295, "faith": 150, "max": 15, "file": "常规单UP抽取的信仰变动期望.png"},
        {"name": "常规双UP单个目标", "p": 0.01475, "faith": 150, "max": 15, "file": "常规双UP抽取的信仰变动期望.png"},
        {"name": "贵人", "p": 0.01, "faith": 300, "max": 30, "file": "贵人抽取的信仰变动期望.png"},
        {"name": "联动4UP单个角色", "p": 0.007375, "faith": 150, "max": 15, "file": "联动4UP抽取的信仰变动期望.png"},
        {"name": "头像框", "p": 0.009, "faith": 100, "max": 10, "file": "装扮UP抽取头像框的信仰变动期望.png"},
        {"name": "无头像框装扮3UP", "p": 0.0245, "faith": 50, "max": 5, "file": None},
        {"name": "无头像框装扮4UP", "p": 0.018375, "faith": 50, "max": 5, "file": None},
        {"name": "无头像框装扮5UP", "p": 0.0147, "faith": 50, "max": 5, "file": "装扮UP无头像框抽取的信仰变动期望.png"},
        {"name": "有头像框其他装扮3UP", "p": 0.03225, "faith": 50, "max": 5, "file": None},
        {"name": "有头像框其他装扮4UP", "p": 0.0215, "faith": 50, "max": 5, "file": None},
        {"name": "有头像框其他装扮5UP", "p": 0.016125, "faith": 50, "max": 5, "file": "装扮UP有头像框抽取其他装扮的信仰变动期望.png"},
    ]
    multi = [
        {"name": "常规双UP全都要", "probs": [0.01475] * 2, "faith": [150] * 2, "max": 30, "file": "常规双UP全都要的信仰变动期望.png"},
        {"name": "联动4UP特定两个", "probs": [0.007375] * 2, "faith": [150] * 2, "max": 30, "file": "联动4UP-只要其中特定两个的信仰变动期望.png"},
        {"name": "联动4UP特定三个", "probs": [0.007375] * 3, "faith": [150] * 3, "max": 30, "file": "联动4UP-只要其中特定三个的信仰变动期望.png"},
        {"name": "联动4UP全都要", "probs": [0.007375] * 4, "faith": [150] * 4, "max": 30, "file": "联动4UP-全都要的信仰变动期望.png"},
        {"name": "联动角色+头像框", "probs": [0.007375, 0.009], "faith": [150, 100], "max": 30, "file": "联动4UP-只要特定角色和头像框的信仰变动期望.png"},
        {"name": "联动4UP毕业", "probs": [0.007375] * 4 + [0.009] + [0.016125] * 4, "faith": [150] * 4 + [100] + [50] * 4, "max": 30, "file": "联动4UP-毕业的信仰变动期望.png"},
    ]
    return single, multi


def print_curve(name: str, values: Sequence[float], interval: tuple[int, int] | None) -> None:
    print(f"\n{name}")
    for n, value in enumerate(values):
        print(f"  {n:2d} 次十连: {value:8.2f}")
    print(f"  临界十连数: {interval or '未在范围内找到'}")


def render_plots(output_root: Path) -> None:
    """重绘 Markdown 引用的图；无图形界面也可运行。"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Songti SC", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams.update(
        {
            "font.size": 18,
            "axes.titlesize": 22,
            "axes.labelsize": 18,
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
            "legend.fontsize": 14,
        }
    )

    def draw_single(
        configs: Sequence[dict],
        filename: str,
        title: str,
        *,
        show_legend: bool = True,
        line_colors: Sequence[str] = ("red", "green", "blue"),
        vertical_colors: Sequence[str] = ("blue", "green"),
    ) -> None:
        destination = output_root / "pic" / filename
        destination.parent.mkdir(exist_ok=True)
        plt.figure(figsize=(10, 6))
        for index, config in enumerate(configs):
            values = one_target_curve(config["p"], config["faith"], config["max"])
            plt.plot(
                range(len(values)),
                values,
                "o-",
                color=line_colors[index % len(line_colors)],
                linewidth=2,
                markersize=7,
            )
        plt.axhline(0, color="black", linewidth=1.5)
        intervals = [
            critical_interval(one_target_curve(c["p"], c["faith"], c["max"]))
            for c in configs
        ]
        critical_points = sorted({point for interval in intervals if interval for point in interval})
        for index, point in enumerate(critical_points):
            color = vertical_colors[index % len(vertical_colors)]
            label = f"N = {point}" if show_legend else "_nolegend_"
            plt.axvline(point, color=color, linestyle="--", linewidth=1.5, label=label)
        plt.xlabel("给定十连数 N")
        plt.ylabel("信仰变动期望 E(N)")
        plt.title(title)
        if show_legend:
            plt.legend(
                loc="upper left",
                framealpha=0.8,
                borderpad=0.35,
                labelspacing=0.25,
                handlelength=2.0,
            )
        plt.tight_layout()
        plt.savefig(destination, dpi=150)
        plt.close()

    single_configs = _models()[0]
    for config in single_configs:
        if config["file"] is None:
            continue
        draw_single([config], config["file"], config["name"] + "的信仰变动期望")
    draw_single(
        [c for c in single_configs if c["name"].startswith("无头像框装扮")],
        "装扮UP无头像框抽取的信仰变动期望.png",
        "装扮 UP 无头像框抽取的信仰变动期望\n红线: 3UP, 绿线: 4UP, 蓝线: 5UP",
        show_legend=False,
        line_colors=("red", "green", "blue"),
        vertical_colors=("purple", "gold"),
    )
    draw_single(
        [c for c in single_configs if c["name"].startswith("有头像框其他装扮")],
        "装扮UP有头像框抽取其他装扮的信仰变动期望.png",
        "装扮 UP 有头像框抽取其他装扮的信仰变动期望\n红线: 3UP, 绿线: 4UP, 蓝线: 5UP",
        show_legend=False,
        line_colors=("red", "green", "blue"),
        vertical_colors=("hotpink", "purple", "gold"),
    )
    for config in _models()[1]:
        values = multi_target_curve(config["probs"], config["faith"], config["max"])
        destination = output_root / "pic2" / config["file"]
        destination.parent.mkdir(exist_ok=True)
        interval = critical_interval(values)
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(values)), values, "o-", color="red", linewidth=2, markersize=7)
        plt.axhline(0, color="black", linewidth=1.5)
        if interval:
            plt.axvline(interval[0], color="blue", linestyle="--", linewidth=1.5, label=f"N = {interval[0]}")
            plt.axvline(interval[1], color="green", linestyle="--", linewidth=1.5, label=f"N = {interval[1]}")
        plt.xlabel("给定十连数 N")
        plt.ylabel("信仰变动期望 E(N)")
        title = config["name"] + "的信仰变动期望"
        if config["name"] == "联动角色+头像框":
            title = (
                "联动1角色+1头像框的信仰变动期望\n"
                "角色p_1=0.7375%(150信仰)+头像框p_2=0.9%(100信仰)"
            )
        elif config["name"] == "联动4UP毕业":
            title = "联动4UP毕业的信仰变动期望\n4角色+1头像框+4装扮"
        plt.title(title)
        if interval:
            plt.legend(
                loc="upper left",
                framealpha=0.8,
                borderpad=0.35,
                labelspacing=0.25,
                handlelength=2.0,
            )
        plt.tight_layout()
        plt.savefig(destination, dpi=150)
        plt.close()


def verify() -> None:
    """校验文档中关键数字，失败时抛出 AssertionError。"""
    single, multi = _models()
    expected_single = {
        "常规单UP": (5, 6),
        "常规双UP单个目标": (7, 8),
        "贵人": (14, 15),
        "联动4UP单个角色": (10, 11),
        "头像框": (7, 8),
    }
    for config in single:
        values = one_target_curve(config["p"], config["faith"], config["max"])
        if config["name"] in expected_single:
            assert critical_interval(values) == expected_single[config["name"]]
    expected_multi = {
        "常规双UP全都要": (10, 11),
        "联动4UP特定两个": (13, 14),
        "联动4UP特定三个": (16, 17),
        "联动4UP全都要": (18, 19),
        "联动角色+头像框": (12, 13),
        "联动4UP毕业": (19, 20),
    }
    for config in multi:
        values = multi_target_curve(config["probs"], config["faith"], config["max"])
        assert critical_interval(values) == expected_multi[config["name"]]
    distribution = strategy_distribution()
    expected = [9.4971096267e-8, 0.0004475229874, 0.08952465383, 0.7418617002, 0.1681660280]
    assert all(math.isclose(a, b, rel_tol=0, abs_tol=1e-10) for a, b in zip(distribution, expected))
    assert math.isclose(sum(distribution), 1.0, abs_tol=1e-12)
    print("校验通过：单目标、多目标和四角色抽井分类结果均与文档基准一致。")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plots", action="store_true", help="重绘 Markdown 使用的图片")
    parser.add_argument("--verify", action="store_true", help="运行关键结果校验")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    if args.verify:
        verify()
    else:
        single, multi = _models()
        print("======== 雀魂卡池信仰变动期望统一分析 ========")
        for config in single:
            values = one_target_curve(config["p"], config["faith"], config["max"])
            print_curve(config["name"], values, critical_interval(values))
        for config in multi:
            values = multi_target_curve(config["probs"], config["faith"], config["max"])
            print_curve(config["name"], values, critical_interval(values))
        distribution = strategy_distribution()
        print("\n联动4UP全要、0 信仰开局的抽井分类概率：")
        for owned, probability in enumerate(distribution):
            print(f"  抽{owned}井{4-owned}: {probability:.10%}")
    if args.plots:
        render_plots(root)
        print(f"\n图片已写入：{root / 'pic'} 和 {root / 'pic2'}")


if __name__ == "__main__":
    main()
