# -*- coding: utf-8 -*-
"""eda.py 与 datadict.py 测试：统计正确性与数据字典完整性。"""
from src.parser import Complaint
from src.eda import class_imbalance, missing_patterns, narrative_coverage_by_year
from src.datadict import to_json, to_markdown


def _c(date, issue, narrative="", sub_issue="X", state="TX", zip_code="75001"):
    return Complaint(date_received=date, issue=issue, narrative=narrative,
                     sub_issue=sub_issue, state=state, zip_code=zip_code)


def test_class_imbalance_counts_and_share():
    data = [
        _c("2024-01-01", "A"), _c("2024-01-02", "A"),
        _c("2024-01-03", "A"), _c("2024-01-04", "B"),
    ]
    ci = class_imbalance(data)
    assert ci["n_records"] == 4
    assert ci["n_classes"] == 2
    # top10 里 A 的支持数应为 3，占比 0.75
    top = {k: v for k, v, _ in ci["top10"]}
    assert top["A"] == 3
    assert abs(ci["top10"][0][2] - 0.75) < 1e-9


def test_missing_patterns_counts_narrative():
    data = [
        _c("2024-01-01", "A", narrative="hello"),
        _c("2024-01-02", "B", narrative=""),
        _c("2024-01-03", "C", narrative=""),
    ]
    mp = missing_patterns(data)
    assert mp["narrative"]["missing"] == 2
    assert abs(mp["narrative"]["rate"] - round(2 / 3, 4)) < 1e-9


def test_narrative_coverage_by_year():
    data = [
        _c("2024-01-01", "A", narrative="x"),
        _c("2024-01-02", "B", narrative=""),
        _c("2023-01-01", "C", narrative="y"),
    ]
    cov = narrative_coverage_by_year(data)
    assert cov["2024"]["total"] == 2
    assert cov["2024"]["with_narrative"] == 1
    assert abs(cov["2024"]["coverage"] - 0.5) < 1e-9
    assert cov["2023"]["coverage"] == 1.0


def test_datadict_covers_all_16_fields():
    j = to_json()
    assert len(j) == 16
    names = [x["name"] for x in j]
    # 关键字段必须齐全
    for required in ["date_received", "product", "issue", "narrative",
                     "complaint_id"]:
        assert required in names
    # issue 是目标字段
    issue = next(x for x in j if x["name"] == "issue")
    assert issue["type"] == "标签"


def test_datadict_markdown_has_table():
    md = to_markdown()
    assert md.startswith("# CFPB 投诉数据字典")
    assert "| 字段名 |" in md or "| # |" in md
    assert md.count("|") > 50  # 16 行表格应有大量分隔符
