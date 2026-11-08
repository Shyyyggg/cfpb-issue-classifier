# CFPB 投诉问题类型分类器

基于 CFPB 消费者投诉数据库，给定投诉的结构化字段与叙事文本，
预测其问题类型（Issue）。本仓库为课程项目的累积提交：

- **阶段 1**（tag `phase-1-submission`）：问题定义 + 规则基线原型。
- **阶段 2**（tag `phase-2-submission`）：数据与实验设计——数据字典、
  探索性分析、防泄漏时间外划分、TF-IDF + 逻辑回归文本基线。

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
pytest tests/ -v        # 28 个测试
```

## 一键验证（推荐）

```bash
python tools/verify.py
```

依次执行：全部自动化测试 → 样本数据评估流水线 → 重新生成图表 → 产物完整性
检查。全部通过时输出 `4/4 通过` 并以退出码 0 结束；任一失败则退出码 1。

## 阶段 2 数据与实验设计

```bash
# 探索性分析（类别不平衡、缺失模式、叙事披露率趋势）
python -m src.eda --data /path/to/complaints.csv --sample 300000 --seed 42 \
    --out results/eda_report.json

# 防泄漏划分（时间外 + 消费者级去重 + 泄漏检查）
python -m src.split --data /path/to/complaints.csv --sample 300000 --seed 42 \
    --out results/split_report.json

# 文本基线（TF-IDF + 逻辑回归，5 种子置信区间）
python -m src.text_baseline --data /path/to/complaints.csv --sample 200000 \
    --seed 42 --seeds 42 43 44 45 46 --out results/text_baseline_eval.json

# 生成数据字典
python -m src.datadict --out docs/data_dictionary.md

# 生成阶段 2 图表
python tools/figures_phase2.py
```

## 重新生成报告图表

```bash
python tools/figures.py          # 阶段 1 图表
python tools/figures_phase2.py   # 阶段 2 图表
```

## 仓库结构

```
src/parser.py       流式 CSV 解析、字段校验、产品名归一化
src/sampler.py      蓄水池抽样与确定性训练/测试划分
src/baseline.py     规则基线（Product→高频 Issue）与多数类对照基线
src/evaluate.py     准确率/宏 F1 评估（指标自行实现，可审查复算）
src/split.py        时间外划分 + 消费者级去重 + 泄漏检查（阶段 2）
src/eda.py          探索性分析（阶段 2）
src/text_baseline.py TF-IDF + 逻辑回归文本基线（阶段 2）
src/datadict.py     数据字典生成（阶段 2）
tools/              样本提取与图表生成脚本
tests/              28 个自动化测试（含边界输入与防泄漏检查）
docs/               数据字典、提示词记录等文档
```

## 公开声明

- 数据来源：CFPB Consumer Complaint Database（公开数据）。
- 生成式 AI 辅助：本项目的代码框架与报告初稿使用了 AI 助手辅助生成，
  全部数字均来自本地可复现运行；团队成员负责审查与验证。
