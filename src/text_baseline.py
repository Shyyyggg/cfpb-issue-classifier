# -*- coding: utf-8 -*-
"""
text_baseline.py — TF-IDF + 逻辑回归文本基线。

这是阶段 2 的简单基线，供阶段 3 的比较方法对照。设计要点：
- 只用"有叙事文本"的样本（全库约 23.1% 覆盖），因为 TF-IDF 是文本特征；
- 沿用 split.py 的时间外划分 + 消费者级去重，避免泄漏；
- 报告准确率 + 宏 F1，并重复 5 个随机种子给出置信区间（均值±标准差）；
- 同时给出"只用元数据（Product 单特征）的逻辑回归"作对照，
  说明文本线 vs 元数据线的差异。

依赖：scikit-learn（TF-IDF 与逻辑回归用标准库实现，评估指标仍用自写的
evaluate.py，保证可审查复算）。

用法：
    python -m src.text_baseline --data <csv路径> --sample 200000 --seed 42 \
        --seeds 42 43 44 45 46 --out results/text_baseline_eval.json
"""
import argparse
import json
import os
from collections import Counter
from typing import List, Tuple

from .parser import Complaint
from .sampler import reservoir_sample
from .split import dedup_consumer, temporal_split
from .evaluate import accuracy, macro_f1


def _text_features(complaints: List[Complaint]) -> Tuple[List[str], List[str]]:
    """返回 (文本列表, 标签列表)，只保留有叙事的样本。"""
    texts, labels = [], []
    for c in complaints:
        if c.has_narrative:
            texts.append(c.narrative)
            labels.append(c.issue)
    return texts, labels


def _train_lr_tfidf(train_texts, train_labels, test_texts,
                    min_df=2, max_features=20000, C=1.0, seed=42):
    """训练 TF-IDF + 逻辑回归，返回测试集预测标签。"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    vec = TfidfVectorizer(
        min_df=min_df, max_features=max_features,
        ngram_range=(1, 2), sublinear_tf=True, stop_words="english",
    )
    X_train = vec.fit_transform(train_texts)
    X_test = vec.transform(test_texts)

    clf = LogisticRegression(
        max_iter=200, C=C, solver="lbfgs",
        class_weight="balanced", random_state=seed,
    )
    clf.fit(X_train, train_labels)
    return clf.predict(X_test)


def _train_lr_meta(train_complaints, test_complaints, seed=42):
    """只用 Product 单特征（one-hot）的逻辑回归对照。"""
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression

    def feats(cs):
        return [{"product": c.product} for c in cs]

    vec = DictVectorizer(sparse=True)
    X_train = vec.fit_transform(feats(train_complaints))
    X_test = vec.transform(feats(test_complaints))
    y_train = [c.issue for c in train_complaints]
    y_test = [c.issue for c in test_complaints]

    clf = LogisticRegression(max_iter=200, solver="lbfgs",
                             class_weight="balanced", random_state=seed)
    clf.fit(X_train, y_train)
    return clf.predict(X_test), y_test


def main() -> None:
    ap = argparse.ArgumentParser(description="CFPB 文本基线（TF-IDF+逻辑回归）")
    ap.add_argument("--data", required=True, help="complaints.csv 路径")
    ap.add_argument("--sample", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=42, help="抽样与划分种子")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46],
                    help="模型训练的多重种子（用于置信区间）")
    ap.add_argument("--test-ratio", type=float, default=0.2)
    ap.add_argument("--out", default="results/text_baseline_eval.json")
    args = ap.parse_args()

    print(f"[1/5] 蓄水池抽样 {args.sample:,} 条（seed={args.seed}）...", flush=True)
    sample, stats = reservoir_sample(args.data, args.sample, args.seed)

    print("[2/5] 消费者去重 + 时间外划分...", flush=True)
    deduped, dup_count = dedup_consumer(sample)
    train, test = temporal_split(deduped, args.test_ratio)

    # 文本线：只用有叙事的样本
    tr_texts, tr_labels = _text_features(train)
    te_texts, te_labels = _text_features(test)
    print(f"[3/5] 文本样本: 训练 {len(tr_texts):,} / 测试 {len(te_texts):,} "
          f"（叙事覆盖率 {len(te_texts)/len(test):.1%}）")

    print(f"[4/5] 训练 TF-IDF+逻辑回归（{len(args.seeds)} 个种子）...", flush=True)
    text_accs, text_f1s = [], []
    for s in args.seeds:
        pred = _train_lr_tfidf(tr_texts, tr_labels, te_texts, seed=s)
        text_accs.append(accuracy(te_labels, list(pred)))
        text_f1s.append(macro_f1(te_labels, list(pred)))
        print(f"      seed={s}: acc={text_accs[-1]:.4f}, macroF1={text_f1s[-1]:.4f}")

    # 元数据对照线（单种子即可）
    # 关键：为公平比较，元数据对照也在"有叙事的测试子集"上评估，
    # 这样它与文本基线在完全相同的测试样本上比较。
    print("[5/5] 元数据对照（Product 单特征逻辑回归）...", flush=True)
    # 找出"有叙事"的测试集下标对应的 Complaint 对象
    test_with_narr = [c for c in test if c.has_narrative]
    meta_pred, meta_y = _train_lr_meta(train, test_with_narr, seed=args.seed)
    meta_acc = accuracy(meta_y, list(meta_pred))
    meta_f1 = macro_f1(meta_y, list(meta_pred))

    # 额外记录：元数据基线在"全量测试集"上的表现，作为产品分布漂移的证据
    meta_full_pred, meta_full_y = _train_lr_meta(train, test, seed=args.seed)
    meta_full_acc = accuracy(meta_full_y, list(meta_full_pred))
    meta_full_f1 = macro_f1(meta_full_y, list(meta_full_pred))

    def mean_std(xs):
        m = sum(xs) / len(xs)
        var = sum((x - m) ** 2 for x in xs) / len(xs)
        return round(m, 4), round(var ** 0.5, 4)

    t_acc_m, t_acc_s = mean_std(text_accs)
    t_f1_m, t_f1_s = mean_std(text_f1s)

    result = {
        "config": {"data": os.path.basename(args.data), "sample": args.sample,
                   "seed": args.seed, "seeds": args.seeds,
                   "test_ratio": args.test_ratio},
        "parse_stats": {"total_rows": stats.total_rows,
                        "valid_rows": stats.valid_rows},
        "dedup": {"before": len(sample), "after": len(deduped),
                  "removed": dup_count},
        "split": {"n_train": len(train), "n_test": len(test),
                  "n_text_train": len(tr_texts), "n_text_test": len(te_texts)},
        "text_baseline": {
            "accuracy_mean": t_acc_m, "accuracy_std": t_acc_s,
            "macro_f1_mean": t_f1_m, "macro_f1_std": t_f1_s,
            "per_seed_accuracy": [round(x, 4) for x in text_accs],
            "per_seed_macro_f1": [round(x, 4) for x in text_f1s],
            "n_classes_in_test": len(set(te_labels)),
        },
        "meta_baseline": {"accuracy": round(meta_acc, 4),
                          "macro_f1": round(meta_f1, 4),
                          "n_test": len(meta_y),
                          "note": "在'有叙事测试子集'上评估，与文本基线公平可比"},
        "meta_baseline_full_test": {
            "accuracy": round(meta_full_acc, 4),
            "macro_f1": round(meta_full_f1, 4),
            "n_test": len(meta_full_y),
            "note": "在全量测试集上评估，反映产品分布漂移的严重程度"},
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print(f"完成 -> {args.out}")
    print(f"  文本基线:   acc={t_acc_m}±{t_acc_s}, macroF1={t_f1_m}±{t_f1_s}")
    print(f"  元数据对照(有叙事测试集): acc={meta_acc}, macroF1={meta_f1}")
    print(f"  元数据对照(全量测试集):   acc={meta_full_acc}, macroF1={meta_full_f1}")


if __name__ == "__main__":
    main()
