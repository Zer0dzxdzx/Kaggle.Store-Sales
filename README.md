# Store Sales Baseline

这是一个面向 Kaggle `Store Sales - Time Series Forecasting` 比赛的可运行基线项目，重点是：

- 模块化的数据读取、特征工程、验证与预测流程
- 使用最后一个预测窗口做贴近比赛场景的递归验证
- 默认使用 `scikit-learn` 的 `HistGradientBoostingRegressor`
- 预留 `LightGBM` 后端接口，后续可直接在 Kaggle Notebook 切换

比赛题目解读与详细说明见 [docs/store_sales_competition_guide.md](docs/store_sales_competition_guide.md)。
项目执行过程记录见 [docs/project_log.md](docs/project_log.md)。
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
  --model-type hist_gbdt
```

输出内容：

- `artifacts/validation_metrics.json`
- `artifacts/validation_predictions.csv`
- `artifacts/submission.csv`

## 说明

- 默认本地验证窗口为训练集最后 `16` 天，作为回测起点；你可以通过 `--validation-horizon` 自行调整。
- 训练目标做了 `log1p` 变换，预测后再 `expm1` 还原，并裁剪为非负值。
- 如果环境里装了 `lightgbm`，可以改成 `--model-type lightgbm`。

## 下一步建议

当前版本是工程化基线，适合作为后续迭代起点。你下一步可以继续加：

1. 多窗口时间验证
2. 更强的树模型参数搜索
3. 家族级别或门店级别的分层建模
4. 混合模型，例如趋势模型 + 树模型残差修正
