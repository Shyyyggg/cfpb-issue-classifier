# -*- coding: utf-8 -*-
"""
parser.py — CFPB 投诉 CSV 的流式解析与校验。

设计要点：
- 8.9 GB 文件无法整体载入内存，全部按行流式处理；
- 叙事文本字段内嵌换行符，必须用 csv 模块而非按物理行切分；
- 产品名称存在历史 schema 变更（同一产品的不同写法），统一归一化。
"""
import csv
import re
from dataclasses import dataclass, field
from typing import Iterator, Optional

csv.field_size_limit(10 ** 9)

COLUMNS = [
    "date_received", "product", "sub_product", "issue", "sub_issue",
    "narrative", "company_public_response", "company", "state",
    "zip_code", "tags", "submitted_via", "date_sent_to_company",
    "company_response", "timely_response", "complaint_id",
]
N_COLUMNS = len(COLUMNS)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}:\d{2})?")

# 历史 schema 变更导致的产品重名，归一到当前口径
PRODUCT_NORMALIZATION = {
    "Credit reporting, credit repair services, or other personal consumer reports":
        "Credit reporting or other personal consumer reports",
    "Credit reporting":
        "Credit reporting or other personal consumer reports",
    "Bank account or service": "Checking or savings account",
    "Credit card or prepaid card": "Credit card",
    "Prepaid card": "Credit card",
    "Money transfers": "Money transfer, virtual currency, or money service",
    "Virtual currency": "Money transfer, virtual currency, or money service",
    "Payday loan, title loan, or personal loan":
        "Payday loan, title loan, personal loan, or advance loan",
    "Consumer Loan": "Payday loan, title loan, personal loan, or advance loan",
    "Payday loan": "Payday loan, title loan, personal loan, or advance loan",
}

UNKNOWN = "UNKNOWN"


@dataclass
class Complaint:
    """一条投诉的计算表示。空/缺失字段统一为 UNKNOWN，便于下游统计。"""
    date_received: str = UNKNOWN
    product: str = UNKNOWN
    sub_product: str = UNKNOWN
    issue: str = UNKNOWN
    sub_issue: str = UNKNOWN
    narrative: str = ""
    company: str = UNKNOWN
    state: str = UNKNOWN
    zip_code: str = UNKNOWN
    submitted_via: str = UNKNOWN
    company_response: str = UNKNOWN
    timely_response: str = UNKNOWN
    complaint_id: str = UNKNOWN

    @property
    def year(self) -> Optional[str]:
        d = self.date_received
        return d[:4] if len(d) >= 4 and d[:4].isdigit() else None

    @property
    def has_narrative(self) -> bool:
        return bool(self.narrative.strip())


@dataclass
class ParseStats:
    """解析过程的审计计数器。"""
    total_rows: int = 0
    valid_rows: int = 0
    bad_rows: int = 0
    bad_reasons: dict = field(default_factory=dict)

    def reject(self, reason: str) -> None:
        self.bad_rows += 1
        self.bad_reasons[reason] = self.bad_reasons.get(reason, 0) + 1


def normalize_product(name: str) -> str:
    """产品名归一化；空值与未知名返回 UNKNOWN。"""
    n = (name or "").strip()
    if not n:
        return UNKNOWN
    return PRODUCT_NORMALIZATION.get(n, n)


def is_valid_date(s: str) -> bool:
    """接受 YYYY-MM-DD 或 ISO8601 时间戳；拒绝空串与畸形值。"""
    return bool(s) and bool(DATE_RE.match(s))


def row_to_complaint(row: list) -> Complaint:
    """将 16 列原始行转换为 Complaint，并做基础清洗。"""
    vals = [(v or "").strip() for v in row[:N_COLUMNS]]
    return Complaint(
        date_received=vals[0],
        product=normalize_product(vals[1]),
        sub_product=vals[2] or UNKNOWN,
        issue=vals[3] or UNKNOWN,
        sub_issue=vals[4] or UNKNOWN,
        narrative=row[5] if len(row) > 5 else "",
        company=(vals[7].strip('"') or UNKNOWN),
        state=(vals[8].upper() or UNKNOWN),
        zip_code=vals[9] or UNKNOWN,
        submitted_via=vals[11] or UNKNOWN,
        company_response=vals[13] or UNKNOWN,
        timely_response=vals[14] or UNKNOWN,
        complaint_id=vals[15] or UNKNOWN,
    )


def parse_complaints(path: str, stats: Optional[ParseStats] = None
                     ) -> Iterator[Complaint]:
    """
    流式解析整个 CSV，逐条产出有效 Complaint。
    不完整行（列数不足）与日期非法的行被拒绝并计入 stats。
    """
    if stats is None:
        stats = ParseStats()
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return
        for row in reader:
            stats.total_rows += 1
            if len(row) < N_COLUMNS:
                stats.reject("column_count")
                continue
            if not is_valid_date(row[0].strip()):
                stats.reject("bad_date")
                continue
            stats.valid_rows += 1
            yield row_to_complaint(row)
