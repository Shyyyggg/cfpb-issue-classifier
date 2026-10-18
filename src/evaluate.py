# -*- coding: utf-8 -*-
"""
evaluate.py — 基线评估：准确率 + 宏 F1 + 分类别明细。

用法：
    python -m src.evaluate --data <csv路径> --sample 200000 --seed 42 \
        --out results/baseline_eval.json

指标全部自行实现（无第三方评估依赖），保证结果可被审查复算。
"""
import argparse
import json
import os
from collections import Counter
from typing import Dict, List

from .baseline import GlobalMajorityBaseline, RuleBaselineClassifier
from .sampler import reservoir_sample, train_test_split


def per_class_f1(y_true: List[str], y_pred: List[str]) -> Dict[str, dict]:
    """每个类别的 precision / recall / F1 与支持数。"""
    labels = sorted(set(y_true) | set(y_pred))
    out = {}
    for lab in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p == lab)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != lab and p == lab)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p != lab)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[lab] = {"precision": round(precision, 4), "recall": round(recall, 4),
                    "f1": round(f1, 4), "support": sum(1 for t in y_true if t == lab)}
    return out


def macro_f1(y_true: List[str], y_pred: List[str]) -> float:
    per = per_class_f1(y_true, y_pred)
    return sum(v["f1"] for v in per.values()) / len(per) if per else 0.0


def accuracy(y_true: List[str], y_pred: List[str]) -> float:
    if not y_true:
        return 0.0
    return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)


def evaluate(model, test) -> dict:
    y_true = [c.issue for c in test]
    y_pred = [model.predict(c)[0] for c in test]
    return {
        "accuracy": round(accuracy(y_true, y_pred), 4),
        "macro_f1": round(macro_f1(y_true, y_pred), 4),
        "n_test": len(test),
        "n_classes": len(set(y_true)),
        "top_classes": Counter(y_true).most_common(10),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="CFPB 投诉 Issue 分类基线评估")
    ap.add_argument("--data", required=True, help="complaints.csv 路径")
    ap.add_argument("--sample", type=int, default=200000, help="蓄水池抽样量")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--test-ratio", type=float, default=0.2)
    ap.add_argument("--out", default="results/baseline_eval.json")
    args = ap.parse_args()

    print(f"[1/3] 蓄水池抽样 {args.sample:,} 条（seed={args.seed}）...", flush=True)
    sample, stats = reservoir_sample(args.data, args.sample, args.seed)
    print(f"      扫描 {stats.total_rows:,} 行，有效 {stats.valid_rows:,}，"
          f"拒绝 {stats.bad_rows:,}（{stats.bad_reasons}）")

    train, test = train_test_split(sample, args.test_ratio, args.seed)
    print(f"[2/3] 划分完成：训练 {len(train):,} / 测试 {len(test):,}")

    rule = RuleBaselineClassifier().fit(train)
    majority = GlobalMajorityBaseline().fit(train)

    print("[3/3] 评估中...")
    result = {
        "config": {"data": os.path.basename(args.data), "sample": args.sample,
                   "seed": args.seed, "test_ratio": args.test_ratio},
        "parse_stats": {"total_rows": stats.total_rows,
                        "valid_rows": stats.valid_rows,
                        "bad_rows": stats.bad_rows,
                        "bad_reasons": stats.bad_reasons},
        "rule_baseline": evaluate(rule, test),
        "majority_baseline": evaluate(majority, test),
        "majority_label": majority.major_label,
        "n_rules_learned": len(rule.product_rule),
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"完成 -> {args.out}")
    print(f"  规则基线:   acc={result['rule_baseline']['accuracy']}, "
          f"macroF1={result['rule_baseline']['macro_f1']}")
    print(f"  多数类基线: acc={result['majority_baseline']['accuracy']}, "
          f"macroF1={result['majority_baseline']['macro_f1']}")


if __name__ == "__main__":
    main()
