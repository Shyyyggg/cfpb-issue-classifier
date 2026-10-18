# -*- coding: utf-8 -*-
"""基线与评估的可复现性测试。"""
import pytest

from src.baseline import GlobalMajorityBaseline, RuleBaselineClassifier
from src.evaluate import accuracy, macro_f1, per_class_f1
from src.parser import Complaint, UNKNOWN, parse_complaints
from src.sampler import reservoir_sample, train_test_split


def _load(csv_path):
    return list(parse_complaints(csv_path))


def test_rule_baseline_learns_product_majority(csv_path):
    rows = _load(csv_path)
    clf = RuleBaselineClassifier().fit(rows)
    cr = next(r for r in rows if r.product.startswith("Credit reporting"))
    label, conf = clf.predict(cr)
    assert label == "Incorrect information on your report"
    assert conf == pytest.approx(1.0)
    dc = next(r for r in rows if r.product == "Debt collection")
    label, _ = clf.predict(dc)
    assert label == "Attempts to collect debt not owed"  # 2/3 多数


def test_unseen_product_falls_back_to_global_majority(csv_path):
    rows = _load(csv_path)
    clf = RuleBaselineClassifier().fit(rows)
    ghost = Complaint(product="Mortgage", issue="x")  # 训练集中没有的产品
    label, conf = clf.predict(ghost)
    # 全局最高频 Issue 有两个并列（各 2 条），按出现顺序取先者
    assert label == "Incorrect information on your report"
    assert conf == pytest.approx(2 / 6)


def test_fit_on_empty_raises():
    with pytest.raises(ValueError):
        RuleBaselineClassifier().fit([])
    with pytest.raises(ValueError):
        GlobalMajorityBaseline().fit([])


def test_metrics_bounds_and_correctness():
    y_true = ["a", "a", "b", "b"]
    y_pred = ["a", "b", "b", "b"]
    assert accuracy(y_true, y_pred) == pytest.approx(0.75)
    f1s = per_class_f1(y_true, y_pred)
    assert 0.0 <= f1s["a"]["f1"] <= 1.0
    assert 0.0 <= f1s["b"]["f1"] <= 1.0
    assert f1s["a"]["recall"] == pytest.approx(0.5)
    assert f1s["a"]["precision"] == pytest.approx(1.0)
    m = macro_f1(y_true, y_pred)
    assert 0.0 <= m <= 1.0


def test_reservoir_sampling_is_deterministic(csv_path):
    s1, _ = reservoir_sample(csv_path, 4, seed=7)
    s2, _ = reservoir_sample(csv_path, 4, seed=7)
    assert [c.complaint_id for c in s1] == [c.complaint_id for c in s2]
    s3, _ = reservoir_sample(csv_path, 4, seed=99)
    assert len(s3) == 4


def test_reservoir_rejects_nonpositive_size(csv_path):
    with pytest.raises(ValueError):
        reservoir_sample(csv_path, 0)


def test_split_is_deterministic_and_disjoint(csv_path):
    rows = _load(csv_path)
    tr1, te1 = train_test_split(rows, 0.33, seed=42)
    tr2, te2 = train_test_split(rows, 0.33, seed=42)
    assert [c.complaint_id for c in tr1] == [c.complaint_id for c in tr2]
    assert [c.complaint_id for c in te1] == [c.complaint_id for c in te2]
    assert {c.complaint_id for c in tr1}.isdisjoint({c.complaint_id for c in te1})
    assert len(tr1) + len(te1) == len(rows)


def test_split_rejects_bad_ratio(csv_path):
    rows = _load(csv_path)
    with pytest.raises(ValueError):
        train_test_split(rows, 1.5)


def test_end_to_end_pipeline_beats_majority(csv_path):
    """端到端冒烟测试：规则基线在微型数据上不差于多数类基线。"""
    rows = _load(csv_path)
    train, test = train_test_split(rows, 0.34, seed=42)
    rule = RuleBaselineClassifier().fit(train)
    maj = GlobalMajorityBaseline().fit(train)
    yr = [c.issue for c in test]
    pr = [rule.predict(c)[0] for c in test]
    pm = [maj.predict(c)[0] for c in test]
    assert accuracy(yr, pr) >= accuracy(yr, pm)
