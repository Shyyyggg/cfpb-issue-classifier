# -*- coding: utf-8 -*-
"""
sampler.py — 蓄水池抽样（reservoir sampling）。

全量 1654 万行单遍流式抽样，内存占用 O(n)，n 为样本量；
固定随机种子保证可复现（同一文件同一种子必得同样本）。
"""
import random
from typing import Iterator, List

from .parser import Complaint, ParseStats, parse_complaints


def reservoir_sample(path: str, n: int, seed: int = 42
                     ) -> "tuple[List[Complaint], ParseStats]":
    if n <= 0:
        raise ValueError("样本量必须为正整数")
    rng = random.Random(seed)
    stats = ParseStats()
    sample: List[Complaint] = []
    for i, c in enumerate(parse_complaints(path, stats)):
        if i < n:
            sample.append(c)
        else:
            j = rng.randint(0, i)
            if j < n:
                sample[j] = c
    return sample, stats


def train_test_split(sample: List[Complaint], test_ratio: float = 0.2,
                     seed: int = 42) -> "tuple[List[Complaint], List[Complaint]]":
    """固定种子的确定性划分：先按 ID 排序消除文件顺序影响，再洗牌切分。"""
    if not 0 < test_ratio < 1:
        raise ValueError("test_ratio 必须在 (0,1) 区间")
    ordered = sorted(sample, key=lambda c: (c.complaint_id, c.date_received))
    rng = random.Random(seed)
    idx = list(range(len(ordered)))
    rng.shuffle(idx)
    cut = int(len(idx) * (1 - test_ratio))
    train = [ordered[i] for i in idx[:cut]]
    test = [ordered[i] for i in idx[cut:]]
    return train, test
