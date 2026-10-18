# -*- coding: utf-8 -*-
"""
extract_sample.py — 从全量 CSV 提取前 N 条有效记录作为仓库样本数据。

样本仅用于单元测试与演示运行，不代表全量分布；
全量评估请使用 src/evaluate.py 的蓄水池抽样。
"""
import csv
import sys

csv.field_size_limit(10 ** 9)

HEADER = ("Date received,Product,Sub-product,Issue,Sub-issue,"
          "Consumer complaint narrative,Company public response,Company,"
          "State,ZIP code,Tags,Submitted via,Date sent to company,"
          "Company response to consumer,Timely response?,Complaint ID")


def main(src: str, dst: str, n: int = 5000) -> None:
    kept = 0
    with open(src, "r", encoding="utf-8", errors="replace", newline="") as fin, \
            open(dst, "w", encoding="utf-8", newline="") as fout:
        reader = csv.reader(fin)
        next(reader, None)
        writer = csv.writer(fout)
        writer.writerow(HEADER.split(","))
        for row in reader:
            if len(row) >= 16 and row[0][:4].isdigit():
                writer.writerow(row[:16])
                kept += 1
                if kept >= n:
                    break
    print(f"已提取 {kept} 条 -> {dst}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python tools/extract_sample.py <源csv> <目标csv> [N]")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 5000)
