# -*- coding: utf-8 -*-
"""测试共用的微型数据集构造（10 行，覆盖边界情形）。"""
import csv
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

HEADER = ["Date received", "Product", "Sub-product", "Issue", "Sub-issue",
          "Consumer complaint narrative", "Company public response", "Company",
          "State", "ZIP code", "Tags", "Submitted via", "Date sent to company",
          "Company response to consumer", "Timely response?", "Complaint ID"]

ROWS = [
    ["2024-01-05T10:00:00.000Z", "Credit reporting", "Credit reporting",
     "Incorrect information on your report", "Account status incorrect",
     "", "", "EQUIFAX, INC.", "TX", "75001", "", "Web",
     "2024-01-05T10:01:00.000Z", "Closed with explanation", "Yes", "1001"],
    ["2024-01-06T10:00:00.000Z", "Debt collection", "Medical debt",
     "Attempts to collect debt not owed", "Debt is not yours",
     "They keep calling about a debt I do not owe.", "", "ABC COLLECTIONS",
     "fl", "32301", "", "Web", "2024-01-06T10:01:00.000Z",
     "Closed with non-monetary relief", "Yes", "1002"],
    ["2024-01-07T10:00:00.000Z", "Credit reporting", "Credit reporting",
     "Incorrect information on your report", "Account information incorrect",
     "", "", "Experian Information Solutions Inc.", "CA", "90001", "",
     "Web", "2024-01-07T10:01:00.000Z", "Closed with explanation", "Yes", "1003"],
    ["2024-01-08T10:00:00.000Z", "Debt collection", "Credit card debt",
     "Written notification about debt", "Did not receive enough information",
     "", "", "ABC COLLECTIONS", "NY", "10001", "Servicemember", "Phone",
     "2024-01-08T10:01:00.000Z", "Closed with explanation", "No", "1004"],
    ["2024-01-09T10:00:00.000Z", "Debt collection", "Medical debt",
     "Attempts to collect debt not owed", "Debt is not yours",
     "", "", "XYZ RECOVERY", "GA", "30301", "", "Web",
     "2024-01-09T10:01:00.000Z", "In progress", "Yes", "1005"],
    # 边界情形：空叙事 + 历史重名产品 + 缺失子字段
    ["2024-01-10T10:00:00.000Z", "Bank account or service", "",
     "Managing an account", "", "", "", "SOME BANK", "", "", "", "Web",
     "2024-01-10T10:01:00.000Z", "Closed", "Yes", "1006"],
    # 边界情形：非法日期 -> 应被拒绝
    ["not-a-date", "Debt collection", "", "Attempts to collect debt not owed",
     "", "", "", "ABC COLLECTIONS", "TX", "75001", "", "Web", "",
     "Closed", "Yes", "1007"],
    # 边界情形：列数不足 -> 应被拒绝
    ["2024-01-11T10:00:00.000Z", "Debt collection", "short-row"],
]


def _write(rows, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for r in rows:
            w.writerow(r)


@pytest.fixture()
def csv_path(tmp_path):
    p = tmp_path / "mini.csv"
    _write(ROWS, str(p))
    return str(p)
