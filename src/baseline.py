# -*- coding: utf-8 -*-
"""
baseline.py — 规则基线分类器。

思路：投诉的 Issue（问题类型）与 Product（产品）高度相关，
基线学习「每个产品下最高频的 Issue」映射；对未见过的产品，
回退到全局最高频 Issue。同时提供一个不使用任何特征的
全局多数类基线作为对照。

这是阶段 1 的可解释基线，也是阶段 3 中所有模型的比较锚点。
"""
from collections import Counter
from typing import Dict, Iterable, Tuple

from .parser import Complaint, UNKNOWN


class GlobalMajorityBaseline:
    """无任何特征的朴素基线：永远预测全局最高频 Issue。"""

    def __init__(self) -> None:
        self.major_label: str = UNKNOWN
        self.major_share: float = 0.0

    def fit(self, complaints: Iterable[Complaint]) -> "GlobalMajorityBaseline":
        counter = Counter(c.issue for c in complaints)
        if not counter:
            raise ValueError("训练集为空，无法拟合基线")
        label, count = counter.most_common(1)[0]
        self.major_label = label
        self.major_share = count / sum(counter.values())
        return self

    def predict(self, complaint: Complaint) -> Tuple[str, float]:
        return self.major_label, self.major_share


class RuleBaselineClassifier:
    """Product → 最高频 Issue 的规则基线。"""

    def __init__(self, min_support: int = 1) -> None:
        self.min_support = min_support
        self.product_rule: Dict[str, Tuple[str, float]] = {}
        self.fallback = GlobalMajorityBaseline()

    def fit(self, complaints: Iterable[Complaint]) -> "RuleBaselineClassifier":
        data = list(complaints)
        if not data:
            raise ValueError("训练集为空，无法拟合基线")
        self.fallback.fit(data)
        by_product: Dict[str, Counter] = {}
        for c in data:
            by_product.setdefault(c.product, Counter())[c.issue] += 1
        for product, counter in by_product.items():
            label, count = counter.most_common(1)[0]
            if count >= self.min_support:
                self.product_rule[product] = (label, count / sum(counter.values()))
        return self

    def predict(self, complaint: Complaint) -> Tuple[str, float]:
        rule = self.product_rule.get(complaint.product)
        if rule is None:
            return self.fallback.predict(complaint)
        return rule
