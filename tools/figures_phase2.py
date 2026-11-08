# -*- coding: utf-8 -*-
"""
figures_phase2.py — 重新生成第二阶段报告的全部图表。

输入：
  results/eda_report.json            EDA 结果（由 src/eda.py 生成）
  results/text_baseline_eval.json    文本基线结果（由 src/text_baseline.py 生成）
  results/split_report.json          划分与泄漏报告（由 src/split.py 生成）
输出：
  figures/fig4_class_imbalance.png   类别不平衡
  figures/fig5_missing.png           字段缺失率
  figures/fig6_narrative_trend.png   叙事披露率趋势
  figures/fig7_baseline_phase2.png   文本基线对比

用法：python tools/figures_phase2.py
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

BLUE, ORANGE, GRAY, GREEN, RED = ("#2563eb", "#ea580c", "#94a3b8",
                                  "#059669", "#dc2626")


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def fig4_class_imbalance():
    eda = load(os.path.join("results", "eda_report.json"))
    ci = eda["class_imbalance"]
    top = ci["top10"]
    labels = [k for k, _, _ in top]
    shares = [s for _, _, s in top]
    # 简化标签：截断过长的英文
    labels = [l if len(l) <= 32 else l[:30] + "…" for l in labels]
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ypos = range(len(labels))[::-1]
    colors = [RED if ("report" in l or "credit" in l.lower()) else BLUE
              for l in labels]
    ax.barh(list(ypos), shares, color=colors, height=0.6)
    ax.set_yticks(list(ypos), labels, fontsize=8)
    for yp, s in zip(ypos, shares):
        ax.text(s + 0.005, yp, f"{s*100:.1f}%", va="center", fontsize=8)
    ax.set_xlim(0, max(shares) * 1.18)
    ax.set_xlabel("占总样本比例", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(f"Top10 问题类型占比（总 {ci['n_classes']} 类，"
                 f"Top10 合计 {ci['top10_share']*100:.1f}%）",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig4_class_imbalance.png"))
    plt.close(fig)


def fig5_missing():
    eda = load(os.path.join("results", "eda_report.json"))
    mp = eda["missing_patterns"]
    # 排除 n_records
    fields = {k: v for k, v in mp.items() if k != "n_records"}
    names = list(fields.keys())
    rates = [v["rate"] * 100 for v in fields.values()]
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    colors = [RED if r > 70 else (ORANGE if r > 40 else BLUE)
              for r in rates]
    ax.bar(names, rates, color=colors, width=0.6)
    for i, r in enumerate(rates):
        ax.text(i, r + 0.8, f"{r:.1f}%", ha="center", fontsize=8)
    ax.set_ylabel("缺失率（%）", fontsize=9)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=8)
    ax.set_ylim(0, 105)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("关键字段缺失率（红色=高缺失）", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig5_missing.png"))
    plt.close(fig)


def fig6_narrative_trend():
    eda = load(os.path.join("results", "eda_report.json"))
    cov = eda["narrative_coverage_by_year"]
    years = sorted(cov.keys())
    rates = [cov[y]["coverage"] * 100 for y in years]
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    ax.plot(years, rates, marker="o", color=BLUE, linewidth=1.6, markersize=4)
    for x, y in zip(years, rates):
        ax.text(x, y + 1.0, f"{y:.0f}%", ha="center", fontsize=7.5)
    ax.set_ylabel("叙事文本披露率（%）", fontsize=9)
    ax.set_xlabel("年份", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_ylim(0, 60)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("叙事文本披露率 2017 年达峰后波动下降（佐证模板化批量投诉）",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig6_narrative_trend.png"))
    plt.close(fig)


def fig7_baseline_phase2():
    tb = load(os.path.join("results", "text_baseline_eval.json"))
    text = tb["text_baseline"]
    meta = tb["meta_baseline"]
    cats = ["准确率", "宏 F1"]
    text_v = [text["accuracy_mean"], text["macro_f1_mean"]]
    text_e = [text["accuracy_std"], text["macro_f1_std"]]
    meta_v = [meta["accuracy"], meta["macro_f1"]]
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    x = range(len(cats))
    w = 0.34
    b1 = ax.bar([i - w / 2 for i in x], text_v, w, yerr=text_e,
                capsize=4, label="文本基线（TF-IDF+逻辑回归）", color=BLUE)
    b2 = ax.bar([i + w / 2 for i in x], meta_v, w,
                label="元数据对照（Product 单特征）", color=GRAY)
    for bs, vals in ((b1, text_v), (b2, meta_v)):
        for b, v in zip(bs, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01,
                    f"{v:.3f}", ha="center", fontsize=8.5)
    ax.set_xticks(list(x), cats, fontsize=9.5)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("指标值", fontsize=9)
    ax.tick_params(labelsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, frameon=False)
    ax.set_title("第二阶段基线（时间外划分，文本 vs 元数据）",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig7_baseline_phase2.png"))
    plt.close(fig)


if __name__ == "__main__":
    fig4_class_imbalance()
    fig5_missing()
    fig6_narrative_trend()
    fig7_baseline_phase2()
    print("第二阶段图表已生成 ->", FIGDIR)
