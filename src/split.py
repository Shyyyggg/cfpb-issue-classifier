# -*- coding: utf-8 -*-
"""
split.py — 时间外划分（temporal split）+ 消费者级去重，防止数据泄漏。

为什么这么做（阶段 1 遗留问题的修正）：
阶段 1 用的是随机划分。但 CFPB 数据里，同一个消费者可能会批量提交
大量模板化投诉（尤其是"催收"和"信用报告"类，叙事披露率从 2017 年的
47.5% 一路降到 2025 年的 22.5% 也侧面印证了这种模板化）。如果随机切分，
同一个人的投诉会同时出现在训练集和测试集里，模型相当于"背答案"，
指标会虚高。这属于数据泄漏。

本模块做了两件事：
1. 时间外划分：按投诉接收时间排序，前一部分做训练、后一部分做测试，
   模拟"用历史数据预测未来投诉"的真实部署场景。
2. 消费者级去重：根据 ZIP 码 + 投诉叙事文本（或公司+州）判定是否同一
   消费者的批量投诉，保证同一个消费者只出现在训练集或测试集其中一边。

用法：
    python -m src.split --data <csv路径> --sample 300000 --seed 42 \
        --out results/split_report.json
"""
import argparse
import json
import os
from typing import Dict, List, Tuple

from .parser import Complaint, ParseStats
from .sampler import reservoir_sample


def temporal_sort(complaints: List[Complaint]) -> List[Complaint]:
    """按投诉接收时间升序排序；时间相同按 ID 稳定排序，保证可复现。"""
    return sorted(complaints, key=lambda c: (c.date_received, c.complaint_id))


def temporal_split(complaints: List[Complaint], test_ratio: float = 0.2
                   ) -> Tuple[List[Complaint], List[Complaint]]:
    """
    时间外划分：前 (1-test_ratio) 作训练，后 test_ratio 作测试。
    不洗牌——顺序本身就是要保证"训练时间早于测试时间"。
    """
    if not 0 < test_ratio < 1:
        raise ValueError("test_ratio 必须在 (0,1) 区间")
    ordered = temporal_sort(complaints)
    cut = int(len(ordered) * (1 - test_ratio))
    return ordered[:cut], ordered[cut:]


def _consumer_key(c: Complaint) -> str:
    """
    构造"疑似同一消费者"的判定键。
    优先级：叙事文本（若能精确匹配则几乎可断定是同一模板批量提交）；
    否则用 (ZIP, 公司) 组合，因为 ZIP + 具体公司在小范围内指向性强。
    """
    if c.has_narrative:
        # 取叙事前 64 字符作为指纹，避免整段长文本做键
        return "narr:" + c.narrative.strip()[:64]
    return f"{c.zip_code}|{c.company}"


def dedup_consumer(complaints: List[Complaint]) -> List[Complaint]:
    """
    消费者级去重：相同 _consumer_key 的记录只保留一条。
    返回去重后的列表（保持时间顺序），并返回去重统计。
    """
    seen = set()
    kept = []
    dup_count = 0
    for c in complaints:
        key = _consumer_key(c)
        if key in seen:
            dup_count += 1
            continue
        seen.add(key)
        kept.append(c)
    return kept, dup_count


def leakage_check(train: List[Complaint], test: List[Complaint],
                  ) -> Dict[str, int]:
    """
    泄漏检查：统计训练集与测试集之间"疑似同一消费者"的重叠数。
    重叠应为 0；若 >0 说明划分仍有泄漏风险。
    """
    train_keys = {_consumer_key(c) for c in train}
    overlap = sum(1 for c in test if _consumer_key(c) in train_keys)
    return {
        "train_unique_consumers": len(train_keys),
        "test_records": len(test),
        "overlap_records": overlap,
        "leak_free": overlap == 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="CFPB 时间外划分与泄漏检查")
    ap.add_argument("--data", required=True, help="complaints.csv 路径")
    ap.add_argument("--sample", type=int, default=300000, help="蓄水池抽样量")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--test-ratio", type=float, default=0.2)
    ap.add_argument("--out", default="results/split_report.json")
    args = ap.parse_args()

    print(f"[1/4] 蓄水池抽样 {args.sample:,} 条（seed={args.seed}）...", flush=True)
    sample, stats = reservoir_sample(args.data, args.sample, args.seed)
    print(f"      有效 {stats.valid_rows:,} 条，拒绝 {stats.bad_rows:,} 条")

    print("[2/4] 消费者级去重...", flush=True)
    deduped, dup_count = dedup_consumer(sample)
    print(f"      去重前 {len(sample):,} -> 去重后 {len(deduped):,}"
          f"（移除 {dup_count:,} 条疑似重复）")

    print("[3/4] 时间外划分（按接收时间，前 80% 训练 / 后 20% 测试）...", flush=True)
    train, test = temporal_split(deduped, args.test_ratio)
    print(f"      训练 {len(train):,} / 测试 {len(test):,}")

    print("[4/4] 泄漏检查...", flush=True)
    leak = leakage_check(train, test)

    # 时间边界信息，写进报告用
    train_dates = [c.date_received for c in train]
    test_dates = [c.date_received for c in test]

    report = {
        "config": {"data": os.path.basename(args.data), "sample": args.sample,
                   "seed": args.seed, "test_ratio": args.test_ratio},
        "parse_stats": {"total_rows": stats.total_rows,
                        "valid_rows": stats.valid_rows,
                        "bad_rows": stats.bad_rows,
                        "bad_reasons": stats.bad_reasons},
        "dedup": {"before": len(sample), "after": len(deduped),
                  "removed": dup_count},
        "split": {"n_train": len(train), "n_test": len(test),
                  "train_min_date": min(train_dates),
                  "train_max_date": max(train_dates),
                  "test_min_date": min(test_dates),
                  "test_max_date": max(test_dates)},
        "leakage": leak,
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"完成 -> {args.out}")
    print(f"  时间边界: 训练[{report['split']['train_min_date'][:10]} ~ "
          f"{report['split']['train_max_date'][:10]}]  "
          f"测试[{report['split']['test_min_date'][:10]} ~ "
          f"{report['split']['test_max_date'][:10]}]")
    print(f"  泄漏检查: overlap={leak['overlap_records']}, "
          f"leak_free={leak['leak_free']}")


if __name__ == "__main__":
    main()
