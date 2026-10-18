# -*- coding: utf-8 -*-
"""解析器测试：边界输入与归一化行为。"""
from src.parser import (ParseStats, is_valid_date, normalize_product,
                    parse_complaints)


def test_parse_counts_valid_and_rejected(csv_path):
    stats = ParseStats()
    rows = list(parse_complaints(csv_path, stats))
    # 8 行数据：6 行有效，1 行非法日期，1 行列数不足
    assert stats.total_rows == 8
    assert stats.valid_rows == 6
    assert stats.bad_rows == 2
    assert stats.bad_reasons.get("bad_date") == 1
    assert stats.bad_reasons.get("column_count") == 1
    assert len(rows) == 6


def test_normalize_product_merges_historical_names(csv_path):
    rows = list(parse_complaints(csv_path))
    # "Credit reporting" 与 "Bank account or service" 应归一到当前口径
    products = {r.product for r in rows}
    assert "Credit reporting or other personal consumer reports" in products
    assert "Checking or savings account" in products
    assert "Credit reporting" not in products
    assert "Bank account or service" not in products


def test_normalize_product_handles_empty_and_unknown():
    assert normalize_product("") == "UNKNOWN"
    assert normalize_product("   ") == "UNKNOWN"
    assert normalize_product("Some New Product") == "Some New Product"


def test_date_validation_accepts_and_rejects():
    assert is_valid_date("2024-01-25T19:56:56.000Z")
    assert is_valid_date("2011-12-01")
    assert not is_valid_date("")
    assert not is_valid_date("not-a-date")
    assert not is_valid_date("01/25/2024")  # 非 ISO 格式拒绝


def test_empty_narrative_accepted_and_flagged(csv_path):
    rows = list(parse_complaints(csv_path))
    narr_flags = [r.has_narrative for r in rows]
    assert narr_flags.count(True) == 1   # 仅第 2 行有叙事
    assert narr_flags.count(False) == 5  # 空叙事不导致拒绝


def test_state_normalized_to_upper(csv_path):
    rows = list(parse_complaints(csv_path))
    states = {r.state for r in rows if r.state != "UNKNOWN"}
    assert "FL" in states and "fl" not in states


def test_missing_optional_fields_become_unknown(csv_path):
    rows = list(parse_complaints(csv_path))
    bank = next(r for r in rows if r.company == "SOME BANK")
    assert bank.sub_product == "UNKNOWN"
    assert bank.state == "UNKNOWN"
    assert bank.zip_code == "UNKNOWN"
