# -*- coding: utf-8 -*-
"""
eda.py — 探索性数据分析（EDA）：类别不平衡、缺失模式、叙事披露率。

本模块只做"有目的的统计"，每个数字都对应报告里的一个结论：
1. Issue 类别不平衡量化（头部类占比、类数量、尾部类支持度）
2. 关键字段的缺失率
3. 叙事文本披露率随年份的变化趋势（佐证"模板化批量投诉"假设）

用法：
    python -m src.eda --data <csv路径> --sample 300000 --seed 42 \
        --out results/eda_report.json
"""
import argparse
import json
import os
from collections import Counter
from typing import Dict, List

from .parser import Complaint, UNKNOWN
from .sampler import reservoir_sample


def class_imbalance(complaints: List[Complaint]) -> Dict:
    """类别不平衡：总类数、头部类占比、尾部类（支持度 < 10）数量。"""
    counter = Counter(c.issue for c in complaints)
    total = len(complaints)
    n_classes = len(counter)
    top = counter.most_common(10)
    top_share = sum(v for _, v in top) / total if total else 0.0
    # 尾部类：支持度很低、几乎无法被学到的类
    tail = [(k, v) for k, v in counter.items() if v < 10]
    return {
        "n_records": total,
        "n_classes": n_classes,
        "top10": [[k, v, round(v / total, 4)] for k, v in top],
        "top10_share": round(top_share, 4),
        "n_tail_classes": len(tail),
        "tail_support_total": sum(v for _, v in tail),
    }


def missing_patterns(complaints: List[Complaint]) -> Dict:
    """关键字段缺失率（UNKNOWN 或空串视为缺失）。"""
    n = len(complaints)
    fields = {
        "sub_product": lambda c: c.sub_product == UNKNOWN,
        "sub_issue": lambda c: c.sub_issue == UNKNOWN,
        "narrative": lambda c: not c.has_narrative,
        "state": lambda c: c.state == UNKNOWN,
        "zip_code": lambda c: c.zip_code == UNKNOWN,
        "company_response": lambda c: c.company_response == UNKNOWN,
        "timely_response": lambda c: c.timely_response == UNKNOWN,
    }
    out = {}
    for name, is_missing in fields.items():
        missing = sum(1 for c in complaints if is_missing(c))
        out[name] = {"missing": missing, "rate": round(missing / n, 4)}
    out["n_records"] = n
    return out


def narrative_coverage_by_year(complaints: List[Complaint]) -> Dict:
    """叙事文本披露率按年份变化：揭示模板化投诉趋势。"""
    by_year: Dict[str, Counter] = {}
    for c in complaints:
        y = c.year
        if y is None:
            continue
        by_year.setdefault(y, Counter())["total"] += 1
        if c.has_narrative:
            by_year[y]["with_narrative"] += 1
    out = {}
    for y in sorted(by_year):
        cnt = by_year[y]
        out[y] = {
            "total": cnt["total"],
            "with_narrative": cnt.get("with_narrative", 0),
            "coverage": round(cnt.get("with_narrative", 0) / cnt["total"], 4),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="CFPB 数据探索性分析")
    ap.add_argument("--data", required=True, help="complaints.csv 路径")
    ap.add_argument("--sample", type=int, default=300000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="results/eda_report.json")
    args = ap.parse_args()

    print(f"[1/2] 蓄水池抽样 {args.sample:,} 条（seed={args.seed}）...", flush=True)
    sample, stats = reservoir_sample(args.data, args.sample, args.seed)

    print("[2/2] 计算 EDA 指标...", flush=True)
    report = {
        "config": {"data": os.path.basename(args.data), "sample": args.sample,
                   "seed": args.seed},
        "parse_stats": {"total_rows": stats.total_rows,
                        "valid_rows": stats.valid_rows,
                        "bad_rows": stats.bad_rows},
        "class_imbalance": class_imbalance(sample),
        "missing_patterns": missing_patterns(sample),
        "narrative_coverage_by_year": narrative_coverage_by_year(sample),
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    ci = report["class_imbalance"]
    mp = report["missing_patterns"]
    print(f"完成 -> {args.out}")
    print(f"  类别数={ci['n_classes']}，Top10 占比={ci['top10_share']:.1%}，"
          f"尾部类(支持<10)={ci['n_tail_classes']} 个")
    print(f"  叙事缺失率={mp['narrative']['rate']:.1%}，"
          f"sub_issue 缺失率={mp['sub_issue']['rate']:.1%}")


if __name__ == "__main__":
    main()
