# -*- coding: utf-8 -*-
"""
figures.py — 重新生成第一阶段报告的全部图表。

输入：
  ../agg.json               全量聚合统计（由 aggregate.py 生成）
  results/baseline_eval.json 基线评估结果（由 src/evaluate.py 生成）
输出：figures/fig1_trend.png / fig2_issue_dist.png / fig3_baseline.png
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIGDIR = os.path.join(ROOT, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150

BLUE, ORANGE, GRAY, GREEN, RED = "#2563eb", "#ea580c", "#94a3b8", "#059669", "#dc2626"


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def fig1_trend():
    agg = load(os.path.join("..", "agg.json"))
    years = [(y, c) for y, c in agg["by_year"] if "2012" <= y <= "2026"]
    xs = [y for y, _ in years]
    ys = [c for _, c in years]
    colors = [GRAY if y == "2026" else BLUE for y in xs]
    fig, ax = plt.subplots(figsize=(6.4, 3.1))
    ax.bar(xs, ys, color=colors, width=0.66)
    for x, yv in zip(xs, ys):
        if x in ("2012", "2018", "2024", "2025"):
            ax.text(x, yv + max(ys) * 0.015, f"{yv/10000:.0f}万",
                    ha="center", fontsize=8)
    ax.text(xs.index("2026"), ys[-1] + max(ys) * 0.015, f"{ys[-1]/10000:.0f}万*",
            ha="center", fontsize=8, color="#475569")
    ax.set_ylabel("投诉量（条）", fontsize=9)
    ax.tick_params(labelsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("年度投诉量（2012–2026）  *2026 年数据截至 7 月 5 日",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig1_trend.png"))
    plt.close(fig)


def fig2_issue_dist():
    agg = load(os.path.join("..", "agg.json"))
    top = agg["by_issue"][:8]
    total = agg["meta"]["total_rows"]
    other = total - sum(v for _, v in top)
    labels = [k for k, _ in top] + ["其他 173 类"]
    vals = [v for _, v in top] + [other]
    cn = {
        "Incorrect information on your report": "报告信息不正确",
        "Improper use of your report": "报告被不当使用",
        "Problem with a company's investigation into an existing problem":
            "对公司调查不满",
        "Problem with a credit reporting company's investigation into an existing problem":
            "对征信局调查不满",
        "Attempts to collect debt not owed": "催收不存在的债务",
        "Written notification about debt": "债务书面通知问题",
        "Managing an account": "账户管理问题",
        "Took or threatened to take negative or legal action": "威胁采取负面/法律行动",
    }
    labels = [cn.get(l, l) for l in labels]
    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    ypos = range(len(labels))[::-1]
    ax.barh(list(ypos), vals, color=[RED, RED, ORANGE, ORANGE, BLUE, BLUE, BLUE, BLUE, GRAY],
            height=0.62)
    ax.set_yticks(list(ypos), labels, fontsize=8.5)
    for yp, v in zip(ypos, vals):
        ax.text(v + max(vals) * 0.01, yp, f"{v/total*100:.1f}%",
                va="center", fontsize=8)
    ax.set_xlim(0, max(vals) * 1.16)
    ax.set_xlabel("投诉量（条）", fontsize=9)
    ax.tick_params(axis="x", labelsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Top 问题类型分布（红色=信用报告类问题，占绝对主导）",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig2_issue_dist.png"))
    plt.close(fig)


def fig3_baseline():
    ev = load(os.path.join("results", "baseline_eval.json"))
    rule = ev["rule_baseline"]
    maj = ev["majority_baseline"]
    fig, ax = plt.subplots(figsize=(5.6, 2.9))
    cats = ["准确率", "宏 F1"]
    rule_v = [rule["accuracy"], rule["macro_f1"]]
    maj_v = [maj["accuracy"], maj["macro_f1"]]
    x = range(len(cats))
    w = 0.34
    b1 = ax.bar([i - w / 2 for i in x], rule_v, w, label="规则基线（Product→Issue）",
                color=BLUE)
    b2 = ax.bar([i + w / 2 for i in x], maj_v, w, label="多数类基线", color=GRAY)
    for bs in (b1, b2):
        for b in bs:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.015,
                    f"{b.get_height():.3f}", ha="center", fontsize=8.5)
    ax.set_xticks(list(x), cats, fontsize=9.5)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("指标值", fontsize=9)
    ax.tick_params(labelsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8.5, frameon=False)
    n = ev["rule_baseline"]["n_test"]
    ax.set_title(f"基线评估（留出测试集 n={n:,}，seed=42）", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig3_baseline.png"))
    plt.close(fig)


if __name__ == "__main__":
    fig1_trend()
    fig2_issue_dist()
    fig3_baseline()
    print("图表已生成 ->", FIGDIR)
