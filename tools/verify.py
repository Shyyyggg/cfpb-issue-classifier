# -*- coding: utf-8 -*-
"""
verify.py — 一键验证脚本。

按 README 的说明逐步执行，检查每个步骤是否产出预期结果：
  1. 运行全部自动化测试
  2. 在仓库内样本数据上运行评估流水线
  3. 重新生成报告图表
  4. 校验关键产物文件存在且非空

用法：python tools/verify.py
退出码 0 = 全部通过；1 = 存在失败项。
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

CHECKS = []


def run(name, cmd, expect_files=None):
    print(f"[运行] {name}")
    print(f"       $ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    ok = p.returncode == 0
    tail = (p.stdout or "").strip().splitlines()
    for line in tail[-3:]:
        print(f"       {line}")
    if not ok:
        print(f"       [失败] {p.stderr.strip()[:300]}")
        CHECKS.append((name, False))
        return
    if expect_files:
        missing = [f for f in expect_files
                   if not os.path.exists(os.path.join(ROOT, f))
                   or os.path.getsize(os.path.join(ROOT, f)) == 0]
        if missing:
            print(f"       [失败] 缺少产物: {missing}")
            CHECKS.append((name, False))
            return
    CHECKS.append((name, True))
    print(f"       [通过]")


def main():
    print("=" * 62)
    print("项目可复现性验证")
    print("=" * 62)

    run("1. 自动化测试（pytest）", [PY, "-m", "pytest", "tests/", "-q"])

    run("2. 评估流水线（仓库样本数据）",
        [PY, "-m", "src.evaluate", "--data", "data/sample.csv",
         "--sample", "4000", "--seed", "42", "--out", "results/verify_eval.json"],
        expect_files=["results/verify_eval.json"])

    run("3. 重新生成报告图表", [PY, "tools/figures.py"],
        expect_files=["figures/fig1_trend.png", "figures/fig2_issue_dist.png",
                      "figures/fig3_baseline.png"])

    run("3b. 重新生成阶段2图表", [PY, "tools/figures_phase2.py"],
        expect_files=["figures/fig4_class_imbalance.png", "figures/fig5_missing.png",
                      "figures/fig6_narrative_trend.png", "figures/fig7_baseline_phase2.png"])

    run("4. 产物完整性检查", [PY, "-c", (
        "import os,json;"
        "json.load(open('results/verify_eval.json',encoding='utf-8'));"
        "json.load(open('results/eda_report.json',encoding='utf-8'));"
        "json.load(open('results/split_report.json',encoding='utf-8'));"
        "json.load(open('results/text_baseline_eval.json',encoding='utf-8'));"
        "print('评估/EDA/划分/文本基线 JSON 均可解析');"
        "print('样本数据行数:', sum(1 for _ in open('data/sample.csv',encoding='utf-8',errors='replace'))-1)"
    )])

    print("=" * 62)
    passed = sum(1 for _, o in CHECKS if o)
    for name, ok in CHECKS:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    print(f"合计: {passed}/{len(CHECKS)} 通过")
    print("=" * 62)
    sys.exit(0 if passed == len(CHECKS) else 1)


if __name__ == "__main__":
    main()
