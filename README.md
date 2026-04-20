# Store Sales Baseline

这是一个面向 Kaggle `Store Sales - Time Series Forecasting` 比赛的可运行基线项目，重点是：

- 模块化的数据读取、特征工程、验证与预测流程
- 使用最后一个预测窗口做贴近比赛场景的递归验证
- 默认使用 `scikit-learn` 的 `HistGradientBoostingRegressor`
- 预留 `LightGBM` 后端接口，后续可直接在 Kaggle Notebook 切换

比赛题目解读与详细说明见 [docs/store_sales_competition_guide.md](docs/store_sales_competition_guide.md)。
项目执行过程记录见 [docs/project_log.md](docs/project_log.md)。
学习进程表见 [docs/project_progress_table.md](docs/project_progress_table.md)。
数据表阅读记录见 [docs/data_tables_reading.md](docs/data_tables_reading.md)。
Baseline 阅读记录见 [docs/baseline_reading.md](docs/baseline_reading.md)。
EDA 解读记录见 [docs/eda_interpretation.md](docs/eda_interpretation.md)。
误差分析阅读记录见 [docs/error_analysis_reading.md](docs/error_analysis_reading.md)。
特征实验记录见 [docs/feature_experiments.md](docs/feature_experiments.md)。
结构化实验日志见 [docs/experiment_log.csv](docs/experiment_log.csv)。

## 目录结构

```text
.
├── artifacts/            # 输出目录
├── data/
│   └── raw/              # 放置 Kaggle 原始 CSV
├── src/
│   └── store_sales/
│       ├── cli.py
│       ├── config.py
│       ├── data.py
│       ├── features.py
│       ├── metrics.py
│       ├── modeling.py
│       └── pipeline.py
└── pyproject.toml
```

## 数据准备

将 Kaggle 下载的原始文件放到 `data/raw/` 下，至少包括：

- `train.csv`
- `test.csv`
- `stores.csv`
- `oil.csv`
- `holidays_events.csv`

如果你有这些文件，也会自动利用：

- `transactions.csv`
- `items.csv`

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 运行

```bash
python3 -m store_sales.cli run \
  --data-dir data/raw \
  --output-dir artifacts \
  --train-start-date 2015-01-01 \
  --validation-windows 3 \
  --validation-step-days 16 \
  --feature-profile baseline \
  --log-experiment \
  --experiment-name baseline_histgbdt_multi_window_v1 \
  --model-type hist_gbdt
```

输出内容：

- `artifacts/validation_metrics.json`
- `artifacts/validation_summary.csv`
- `artifacts/validation_predictions.csv`
- `artifacts/validation_predictions_fold_*.csv`
- `artifacts/submission.csv`
- `docs/experiment_log.csv`，仅在使用 `--log-experiment` 或 `--experiment-name` 时自动追加

## 说明

- 默认本地验证窗口为训练集最后 `16` 天，作为回测起点；你可以通过 `--validation-horizon` 自行调整。
- 可通过 `--validation-windows` 开启多窗口验证，`--validation-step-days` 控制相邻验证窗口之间的步长。
- 训练目标做了 `log1p` 变换，预测后再 `expm1` 还原，并裁剪为非负值。
- 如果环境里装了 `lightgbm`，可以改成 `--model-type lightgbm`。
- 可通过 `--feature-profile compact|baseline|extended|low_demand` 切换特征工程方案。
- `low_demand` 会在 baseline 特征基础上增加 family 和 store-family 历史低需求统计特征。

## 模型对比

运行多模型验证对比：

```bash
python3 -m store_sales.cli compare \
  --data-dir data/raw \
  --output-dir artifacts/experiments \
  --report-dir reports/model_comparison \
  --experiments seasonal_naive ridge_baseline histgbdt_baseline \
  --validation-windows 3 \
  --validation-step-days 16
```

输出内容：

- `reports/model_comparison/comparison_results.csv`
- `reports/model_comparison/comparison_report.md`
- `artifacts/experiments/<experiment_name>/validation_summary.csv`

当前已记录的三模型对比结果：

- `histgbdt_baseline`：三窗口 mean RMSLE `0.401601`
- `seasonal_naive`：三窗口 mean RMSLE `0.458129`
- `ridge_baseline`：三窗口 mean RMSLE `2.734132`

说明：如果 `--validation-step-days` 小于 `--validation-horizon`，验证窗口会重叠；当前默认 `16/16` 不重叠。`ridge_baseline` 使用当前序数编码特征，主要作为负向对照。

## EDA

生成可视化分析报告：

```bash
PYTHONPATH=src python3 -m store_sales.eda \
  --data-dir data/raw \
  --output-dir reports/eda \
  --validation-summary artifacts/validation_summary.csv
```

输出内容：

- `reports/eda/eda_report.md`
- `reports/eda/figures/*.png`
- `reports/eda/tables/*.csv`

## 误差分析

生成 family、store、promotion bin 和 fold 误差分析：

```bash
PYTHONPATH=src python3 -m store_sales.error_analysis \
  --data-dir data/raw \
  --artifacts-dir artifacts \
  --output-dir reports/error_analysis
```

输出内容：

- `reports/error_analysis/error_analysis_report.md`
- `reports/error_analysis/tables/family_error.csv`
- `reports/error_analysis/tables/store_error.csv`
- `reports/error_analysis/tables/promotion_bin_error.csv`
- `reports/error_analysis/tables/fold_comparison.csv`

说明：family、store、promotion bin 表是跨 validation folds 的汇总；fold comparison 只做验证窗口级别对比。

## 下一步建议

当前版本是工程化基线，适合作为后续迭代起点。你下一步可以继续加：

1. 多窗口时间验证
2. 更强的树模型参数搜索
3. 家族级别或门店级别的分层建模
4. 混合模型，例如趋势模型 + 树模型残差修正
