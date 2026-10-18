# CFPB 投诉问题类型分类器 — 阶段 1 原型

基于 CFPB 消费者投诉数据库的规则基线分类器：给定投诉的结构化字段，
预测其问题类型（Issue）。本仓库为课程项目阶段 1 提交物。

## 环境设置

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

要求 Python ≥ 3.10。核心流水线仅依赖标准库；`pytest` 用于测试，`matplotlib` 用于图表。

## 数据获取

1. 从 CFPB 官网下载消费者投诉 CSV（Consumer Complaint Database），
   放置于本机任意路径（约 8.9 GB，16,545,376 条记录，截至 2026-07-05）。
2. 仓库内 `data/sample.csv` 为前 5,000 条有效记录样本，仅供测试与演示，
   不代表全量分布。

## 运行评估（可复现）

```bash
# 全量流式抽样评估（约 3 分钟，内存 O(sample)）
python -m src.evaluate --data /path/to/complaints.csv --sample 200000 --seed 42 \
    --out results/baseline_eval.json

# 快速演示（使用仓库内样本）
python -m src.evaluate --data data/sample.csv --sample 4000 --seed 42
```

蓄水池抽样与训练/测试划分均由 `--seed` 固定，同一环境重复运行结果完全一致。

## 运行测试

```bash
pytest tests/ -v        # 11 个测试
```

## 重新生成报告图表

```bash
python tools/figures.py   # 读取 results/ 与聚合统计，输出 figures/*.png
```

## 仓库结构

```
src/parser.py     流式 CSV 解析、字段校验、产品名归一化
src/sampler.py    蓄水池抽样与确定性训练/测试划分
src/baseline.py   规则基线（Product→高频 Issue）与多数类对照基线
src/evaluate.py   准确率/宏 F1 评估（指标自行实现，可审查复算）
tools/            样本提取与图表生成脚本
tests/            11 个自动化测试（含边界输入）
```

## 公开声明

- 数据来源：CFPB Consumer Complaint Database（公开数据）。
- 生成式 AI 辅助：本项目的代码框架与报告初稿使用了 AI 助手辅助生成，
  全部数字均来自本地可复现运行；团队成员负责审查与验证。
