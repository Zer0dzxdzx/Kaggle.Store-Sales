# Kaggle Store Sales Forecasting

这是一个面向 Kaggle `Store Sales - Time Series Forecasting` 比赛的零售需求预测项目。项目目标不是只提交一次结果，而是构建一个可复现、可解释、可迭代的数据科学 workflow：从多表数据理解、特征工程、时间序列验证，到误差诊断、模型对比和 submission 决策。

## 项目快照

| 项目维度 | 当前状态 |
| --- | --- |
| 预测任务 | 预测 `2017-08-16` 到 `2017-08-31` 的门店-商品家族销量 |
| 数据粒度 | `date + store_nbr + family` |
| 评价指标 | RMSLE，越低越好 |
| 当前 best public score | `0.50834`，来自 `LightGBM baseline` |
| 原始 HistGBDT baseline public score | `0.58410` |
| 当前主验证协议 | `August / pre-test explicit windows + recursive forecasting + stability checks` |
| 当前项目定位 | 核心建模 workflow 已完成，正在做作品集化收尾 |

## 这个项目展示了什么

- 多表数据整合：使用 `train/test`、`stores`、`oil`、`holidays_events` 和 `transactions` 构建预测样本。
- 防止数据泄漏：区分预测时已知信息和未来未知信息，`transactions` 只做历史聚合，销量 lag 使用严格历史数据。
- 时间序列验证：不用随机切分，使用多窗口和显式历史窗口，并用递归预测模拟真实 16 天提交场景。
- 特征工程：构造日历、发薪日、地震事件、油价、节假日、门店静态信息、促销历史、销量 lag 和 rolling features。
- 模型对比：比较 seasonal naive、ridge、HistGBDT、LightGBM、simple blending 和 LightGBM tuning 候选。
- 误差诊断：按 family、store、promotion bin、fold 和 test-like slices 拆解模型风险。
- 实验复盘：记录成功和失败实验，尤其是本地验证变好但 Kaggle public score 变差的案例。

## 当前结果

| 方案 | 验证口径 | 本地 RMSLE | Kaggle public score | 结论 |
| --- | --- | ---: | ---: | --- |
| `histgbdt_baseline` | 早期三窗口 validation | `0.401601` | `0.58410` | 首个可提交 baseline |
| `school_supplies_aug_promo` | 早期三窗口 validation | `0.398186` | `0.59096` | 本地改善但线上变差，不保留 |
| `histgbdt_baseline` | August / pre-test windows | `0.490514` | `0.58410` | 历史诊断参考 |
| `lightgbm_baseline` | August / pre-test windows | `0.486767` | `0.50834` | 当前 best submission |
| `lightgbm_shrinkage_es` | August / pre-test windows | `0.499285` |  | 第一轮 tuning 未超过 baseline |

重要说明：

- 不同验证口径下的 RMSLE 不能直接横向比较。
- 当前正式 submission 参考是 `lightgbm_baseline`。
- `school_supplies_aug_promo` 是一个很有价值的失败案例：它说明本地 mean RMSLE 变好不代表线上泛化一定更好。
- Kaggle public score 记录见 [docs/experiment_log.csv](docs/experiment_log.csv) 和 [docs/project_log.md](docs/project_log.md)。

## 快速开始

### 1. 安装环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[lightgbm]'
```

如果暂时不运行 LightGBM，也可以只安装基础依赖：

```bash
pip install -e .
```

### 2. 准备数据

将 Kaggle 下载的原始 CSV 放到 `data/raw/` 下。

必需文件：

```text
data/raw/
├── train.csv
├── test.csv
├── sample_submission.csv
├── stores.csv
├── oil.csv
└── holidays_events.csv
```

可选文件：

- `transactions.csv`：如果存在，会用于历史门店交易量聚合特征。
- `items.csv`：当前主 pipeline 不依赖它。

`data/raw/` 不提交到 Git，避免上传比赛原始数据。

### 3. 跑一个基础 pipeline

```bash
PYTHONPATH=src python3 -m store_sales.cli run \
  --data-dir data/raw \
  --output-dir artifacts/baseline_histgbdt \
  --train-start-date 2015-01-01 \
  --validation-windows 3 \
  --validation-step-days 16 \
  --feature-profile baseline \
  --model-type hist_gbdt
```

主要输出：

- `artifacts/baseline_histgbdt/validation_metrics.json`
- `artifacts/baseline_histgbdt/validation_summary.csv`
- `artifacts/baseline_histgbdt/validation_predictions_fold_*.csv`
- `artifacts/baseline_histgbdt/submission.csv`

### 4. 复现当前主验证口径

```bash
PYTHONPATH=src python3 -m store_sales.cli run \
  --data-dir data/raw \
  --output-dir artifacts/validation/august_windows/lightgbm_baseline \
  --train-start-date 2013-01-01 \
  --validation-horizon 16 \
  --validation-window 2014-08-16:2014-08-31 \
  --validation-window 2015-08-16:2015-08-31 \
  --validation-window 2016-08-16:2016-08-31 \
  --validation-window 2017-07-31:2017-08-15 \
  --feature-profile baseline \
  --model-type lightgbm \
  --skip-submission
```

这组窗口是当前正式验证协议的核心：

- `2014/2015/2016-08-16~08-31`：历史同季窗口
- `2017-07-31~08-15`：测试期前最后 16 天 holdout

## 关键文档

### 面向作品集和面试

- [最终结果总结](docs/final_result_summary.md)
- [项目总结](docs/resume_project_summary.md)
- [简历深挖与面试准备](docs/interview_deep_dive.md)
- [进阶升级路线图](docs/advanced_roadmap.md)

### 面向验证和提交决策

- [验证协议](docs/validation_protocol.md)
- [Submission gate](docs/submission_gate.md)
- [LightGBM tuning log](docs/lightgbm_tuning_log.md)
- [结构化实验日志](docs/experiment_log.csv)

### 面向学习和复盘

- [比赛题目说明](docs/store_sales_competition_guide.md)
- [数据表阅读记录](docs/data_tables_reading.md)
- [Baseline 阅读记录](docs/baseline_reading.md)
- [EDA 解读记录](docs/eda_interpretation.md)
- [误差分析阅读记录](docs/error_analysis_reading.md)
- [特征实验记录](docs/feature_experiments.md)
- [项目日志](docs/project_log.md)
- [学习进程表](docs/project_progress_table.md)

## 主要报告

| 报告 | 路径 | 用途 |
| --- | --- | --- |
| EDA 报告 | `reports/eda/eda_report.md` | 数据概览、趋势、family、促销和门店差异 |
| 基础误差分析 | `reports/error_analysis/error_analysis_report.md` | family/store/promotion/fold 分组误差 |
| Fold 3 交叉误差 | `reports/fold3_cross_error/fold3_cross_error_report.md` | 定位 late validation 变差来源 |
| School supplies 专题分析 | `reports/family_focus/school_office_supplies/family_focus_report.md` | 分析目标 family 的 underprediction |
| 模型对比 | `reports/model_comparison/comparison_report.md` | 早期模型对比 |
| August validation | `reports/validation/august_lightgbm/validation_window_report.md` | 当前主验证口径下的 LightGBM 结果 |
| Feature ablation | `reports/feature_ablation/lightgbm_baseline_fast300/ablation_report.md` | 第一轮特征组消融 |
| LightGBM tuning | `reports/validation/lightgbm_tuning/comparison_report.md` | 第一轮 LightGBM 参数候选对比 |

## 仓库结构

```text
.
├── data/
│   └── raw/                    # Kaggle 原始数据，gitignored
├── artifacts/                  # 训练、验证、submission 输出，gitignored
├── docs/                       # 项目说明、学习记录、验证协议和面试文档
├── reports/                    # EDA、误差分析、验证、消融和调参报告
├── src/
│   └── store_sales/
│       ├── cli.py              # CLI 入口
│       ├── config.py           # Pipeline 配置
│       ├── data.py             # 原始 CSV 读取和基础清洗
│       ├── features.py         # 特征工程和递归 lag 特征
│       ├── modeling.py         # 模型训练和预测封装
│       ├── pipeline.py         # 训练、验证、递归预测和 submission
│       ├── experiment_runner.py
│       ├── feature_ablation.py
│       ├── stability_slice_report.py
│       └── validation_window_report.py
└── pyproject.toml
```

## 常用命令

### 生成 EDA

```bash
PYTHONPATH=src python3 -m store_sales.eda \
  --data-dir data/raw \
  --output-dir reports/eda \
  --validation-summary artifacts/baseline_histgbdt/validation_summary.csv
```

### 生成基础误差分析

```bash
PYTHONPATH=src python3 -m store_sales.error_analysis \
  --data-dir data/raw \
  --artifacts-dir artifacts/baseline_histgbdt \
  --output-dir reports/error_analysis
```

### 比较多个模型

```bash
PYTHONPATH=src python3 -m store_sales.cli compare \
  --data-dir data/raw \
  --output-dir artifacts/experiments \
  --report-dir reports/model_comparison \
  --experiments seasonal_naive ridge_baseline histgbdt_baseline \
  --validation-windows 3 \
  --validation-step-days 16
```

### 运行特征消融

```bash
PYTHONPATH=src python3 -m store_sales.cli ablate \
  --data-dir data/raw \
  --output-dir artifacts/feature_ablation/lightgbm_baseline_fast300 \
  --report-dir reports/feature_ablation/lightgbm_baseline_fast300 \
  --model-type lightgbm \
  --feature-profile baseline \
  --model-param n_estimators=300
```

## 重要建模原则

### 为什么不能随机切分

这是预测未来销量的时间序列问题。随机切分可能让训练集包含比验证集更晚的日期，相当于用未来信息预测过去，会让本地验证分数失真。

### 如何避免数据泄漏

- `sales_lag_*` 使用历史日期的销量。
- rolling sales 特征使用 `shift(1)`，不包含当天真实销量。
- 验证和测试使用递归预测，预测第 2 天时只能使用第 1 天的预测值。
- `transactions.csv` 不直接按未来日期 merge，只使用训练窗口内的历史聚合。
- `onpromotion` 可以使用，因为 `test.csv` 已经公开给出未来促销信息。

### 为什么要看 stability slices

项目中出现过本地验证变好但 Kaggle public score 变差的实验。原因是一个候选方案可能改善目标切片，但伤害非目标 family 或测试期权重更高的 promotion 切片。因此当前 submission 决策不只看 mean RMSLE，还看 worst fold、non-target regression 和 test-like distribution risk。

## 当前局限

- 还没有完整 `tests/` 和 CI，下一阶段会补轻量 sanity checks。
- 当前 validation gate 是基于有限历史案例校准出来的第一版规则，不应被理解成 leaderboard 的绝对预测器。
- LightGBM baseline 是当前 best public submission，但仍存在 fold 1/2 回退和部分非目标 family regression 风险。
- 项目还没有做更高级的模型集成或 private leaderboard 级别优化。

## 下一阶段

当前优先级不是马上继续改模型，而是把项目作品集化：

1. 已补唯一可信的最终结果总结，见 [最终结果总结](docs/final_result_summary.md)。
2. 补可复现性文档。
3. 增加轻量测试和 sanity checks。
4. 写一份完整 case study。
5. 整理面试讲述稿。
