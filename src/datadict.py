# -*- coding: utf-8 -*-
"""
datadict.py — 数据字典 / 数据卡片生成。

对 16 个字段逐条文档化：字段名、类型、含义、示例值、缺失处理方式。
输出一份 Markdown 数据字典（可直接作为报告附录），也输出 JSON 供程序使用。

用法：
    python -m src.datadict --out docs/data_dictionary.md
"""
import json
import os

# 16 个字段的元信息（与 parser.COLUMNS 顺序一致）
FIELDS = [
    ("date_received", "日期", "投诉被 CFPB 接收的日期（ISO8601）",
     "2024-01-25T19:56:56.000Z", "缺失/非法日期整条拒绝"),
    ("product", "分类", "产品大类（已按历史 schema 归一化）",
     "Credit reporting or other personal consumer reports", "空值记为 UNKNOWN"),
    ("sub_product", "分类", "产品子类", "Credit reporting",
     "空值记为 UNKNOWN"),
    ("issue", "标签", "问题类型（本项目预测目标，181 类）",
     "Incorrect information on your report", "空值记为 UNKNOWN"),
    ("sub_issue", "分类", "问题子类", "Account status incorrect",
     "空值记为 UNKNOWN"),
    ("narrative", "文本", "消费者自述（自由文本，平均 1020 字符）",
     "They keep calling about a debt I do not owe.", "空串表示未提供"),
    ("company_public_response", "文本", "公司对 CFPB 的公开回应",
     "Company has responded to the consumer...", "空值记为 UNKNOWN"),
    ("company", "分类", "被投诉公司名", "Experian Information Solutions Inc.",
     "空值记为 UNKNOWN，去除首尾引号"),
    ("state", "分类", "消费者所在州（大写两位缩写）", "TN",
     "空值记为 UNKNOWN，统一转大写"),
    ("zip_code", "分类", "消费者邮编（5 位）", "38141", "空值记为 UNKNOWN"),
    ("tags", "分类", "标签（如 Servicemember）", "Older American",
     "空值记为 UNKNOWN"),
    ("submitted_via", "分类", "提交渠道", "Web", "空值记为 UNKNOWN"),
    ("date_sent_to_company", "日期", "投诉转交公司的日期",
     "2024-01-25T19:56:59.000Z", "缺失不拒绝"),
    ("company_response", "分类", "公司给消费者的处理结果",
     "Closed with non-monetary relief", "空值记为 UNKNOWN"),
    ("timely_response", "布尔", "公司是否及时响应（Yes/No）", "Yes",
     "空值记为 UNKNOWN"),
    ("complaint_id", "标识", "投诉唯一编号", "8223945", "空值记为 UNKNOWN"),
]


def to_markdown() -> str:
    lines = ["# CFPB 投诉数据字典", ""]
    lines.append("数据来源：CFPB Consumer Complaint Database（公开数据，"
                 "许可：公共领域 / 开放数据）。")
    lines.append("观测单位：一条消费者投诉；全量约 16,545,376 条记录，"
                 "16 个字段。")
    lines.append("")
    lines.append("| # | 字段名 | 类型 | 含义 | 示例 | 缺失处理 |")
    lines.append("|---|--------|------|------|------|----------|")
    for i, (name, ftype, desc, example, handling) in enumerate(FIELDS, 1):
        lines.append(f"| {i} | `{name}` | {ftype} | {desc} | "
                     f"{example} | {handling} |")
    lines.append("")
    lines.append("> 注：`issue` 是本项目的预测目标（多类分类标签），"
                 "其余字段为可用输入特征。")
    return "\n".join(lines)


def to_json() -> list:
    return [{"index": i, "name": name, "type": ftype, "description": desc,
             "example": example, "missing_handling": handling}
            for i, (name, ftype, desc, example, handling) in enumerate(FIELDS, 1)]


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="生成数据字典")
    ap.add_argument("--out", default="docs/data_dictionary.md")
    args = ap.parse_args()

    md = to_markdown()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)

    # 同时写一份 JSON
    json_out = os.path.splitext(args.out)[0] + ".json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(to_json(), f, ensure_ascii=False, indent=1)

    print(f"数据字典已生成 -> {args.out}")
    print(f"JSON 版本       -> {json_out}")


if __name__ == "__main__":
    main()
