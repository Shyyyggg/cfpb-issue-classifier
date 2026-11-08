# -*- coding: utf-8 -*-
"""split.py 测试：时间外划分与消费者级去重（防泄漏）。"""
from src.parser import Complaint
from src.split import (dedup_consumer, leakage_check, temporal_split,
                       temporal_sort)


def _c(date, issue, narrative="", zip_code="75001", company="ACME"):
    return Complaint(date_received=date, issue=issue, narrative=narrative,
                     zip_code=zip_code, company=company,
                     product="Debt collection")


def test_temporal_split_preserves_time_order():
    """时间外划分：训练集所有日期都早于测试集。"""
    data = [
        _c("2024-01-01", "A"), _c("2024-01-03", "B"),
        _c("2024-01-02", "C"), _c("2024-01-05", "D"),
        _c("2024-01-04", "E"),
    ]
    train, test = temporal_split(data, test_ratio=0.4)
    # 5 条数据，test_ratio=0.4 -> 训练 3 条（前 60%）、测试 2 条（后 40%）
    assert len(train) == 3 and len(test) == 2
    assert max(c.date_received for c in train) <= min(c.date_received for c in test)


def test_temporal_split_rejects_bad_ratio():
    try:
        temporal_split([_c("2024-01-01", "A")], test_ratio=1.5)
        assert False, "应当抛出 ValueError"
    except ValueError:
        pass


def test_temporal_sort_is_deterministic():
    data = [_c("2024-01-02", "A"), _c("2024-01-01", "B")]
    s1 = temporal_sort(data)
    s2 = temporal_sort(data)
    assert [c.date_received for c in s1] == [c.date_received for c in s2]
    assert s1[0].date_received == "2024-01-01"


def test_dedup_consumer_removes_template_complaints():
    """相同叙事文本的批量投诉应被去重。"""
    data = [
        _c("2024-01-01", "A", narrative="They keep calling about a debt."),
        _c("2024-01-02", "A", narrative="They keep calling about a debt."),
        _c("2024-01-03", "B", narrative="Different complaint here."),
    ]
    kept, dup = dedup_consumer(data)
    assert len(kept) == 2
    assert dup == 1


def test_dedup_consumer_falls_back_to_zip_company():
    """无叙事时，用 ZIP+公司 判定重复。"""
    data = [
        _c("2024-01-01", "A", narrative="", zip_code="75001", company="ACME"),
        _c("2024-01-02", "A", narrative="", zip_code="75001", company="ACME"),
        _c("2024-01-03", "B", narrative="", zip_code="75002", company="ACME"),
    ]
    kept, dup = dedup_consumer(data)
    assert len(kept) == 2 and dup == 1


def test_leakage_check_detects_overlap():
    """去重后的 train/test 不应有消费者重叠。"""
    data = [
        _c("2024-01-01", "A", narrative="unique one"),
        _c("2024-01-02", "B", narrative="unique two"),
        _c("2024-01-03", "C", narrative="unique three"),
        _c("2024-01-04", "D", narrative="unique four"),
    ]
    train, test = temporal_split(data, 0.5)
    leak = leakage_check(train, test)
    assert leak["leak_free"] is True
    assert leak["overlap_records"] == 0


def test_leakage_check_flags_duplicate_across_split():
    """若同一消费者跨 split，泄漏检查应能发现。"""
    train = [_c("2024-01-01", "A", narrative="same person text")]
    test = [_c("2024-01-02", "A", narrative="same person text")]
    leak = leakage_check(train, test)
    assert leak["overlap_records"] == 1
    assert leak["leak_free"] is False
