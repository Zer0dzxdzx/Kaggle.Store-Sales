# Store Sales 可复现性说明

更新日期：2026-05-09

## 这份文档的用途

这份文档回答一个作品集项目最关键的问题：

> 其他人拿到这个仓库后，能不能在本地重新跑出主要结果？

当前目标不是把所有历史实验都一键重跑，而是先保证三件事可复现：

- 能从 Kaggle 原始 CSV 重新运行 pipeline。
- 能重新生成当前主验证口径下的 validation outputs。
- 能重新生成用于 Kaggle 提交格式的 `submission.csv`。

需要注意：Kaggle public score 本身不能只靠本地代码复现，它来自线上提交后的 leaderboard。当前 public score 记录见 `docs/final_result_summary.md` 和 `docs/experiment_log.csv`。

## 复现边界

| 内容 | 是否可复现 | 说明 |
| --- | --- | --- |
| 原始数据读取 | 可以 | 需要用户自行从 Kaggle 下载数据到 `data/raw/` |
| 特征工程 | 可以 | 由 `src/store_sales/features.py` 生成 |
| 时间序列验证 | 可以 | 使用固定 explicit validation windows |
| 递归预测 | 可以 | 验证和提交都使用同一套递归预测逻辑 |
| `submission.csv` | 可以 | 本地生成后可上传 Kaggle |
| Kaggle public score | 不能完全本地复现 | 必须提交到 Kaggle leaderboard 才能得到 |
| 历史 artifact 文件 | 不要求完全一致 | `artifacts/` 被 gitignore，重新运行会生成新的本地产物 |

## 环境要求

推荐环境：

- Python `3.11+`
- macOS / Linux shell
- `pip`
- Kaggle Store Sales 原始 CSV

项目依赖写在 `pyproject.toml` 中。当前主模型使用 LightGBM，所以推荐安装带 LightGBM 的 extra：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[lightgbm]'
```

如果只想跑非 LightGBM baseline，可以安装基础依赖：

```bash
python3 -m pip install -e .
```

安装后先检查 CLI 是否可用：

```bash
PYTHONPATH=src python3 -m store_sales.cli --help
```

如果要运行轻量测试：

```bash
python3 -m pip install -e '.[test]'
python3 -m pytest -q
```

这些测试不依赖 Kaggle 全量数据，主要检查 validation windows、submission 格式、lag safety 和 recursive forecast。

如果要确认 LightGBM 是否安装成功：

```bash
python3 -c "import lightgbm; print(lightgbm.__version__)"
```

## 数据放置

从 Kaggle 下载 `Store Sales - Time Series Forecasting` 数据后，把 CSV 放到：

```text
data/raw/
```

validation 和特征工程必需文件：

```text
data/raw/train.csv
data/raw/test.csv
data/raw/stores.csv
data/raw/oil.csv
data/raw/holidays_events.csv
```

完整复现 submission 还需要：

```text
data/raw/sample_submission.csv
```

可选文件：

```text
data/raw/transactions.csv
data/raw/items.csv
```

当前 pipeline 会使用 `transactions.csv` 做历史聚合特征；如果没有该文件，代码仍可运行，但结果可能和当前记录不完全一致。`sample_submission.csv` 只在生成 `submission.csv` 时强制需要；如果只跑 `--skip-submission` 的 validation smoke check，可以暂时缺少它。`items.csv` 当前主 pipeline 不依赖。

数据目录不提交到 Git：

- `data/raw/` 包含 Kaggle 原始数据，受比赛数据规则约束。
- `artifacts/` 包含本地训练和提交产物，通常体积较大。

## 推荐复现顺序

### 1. 先跑一个 smoke check

这个命令用于确认数据路径、依赖和 pipeline 基本可用。它只跑最后一个 16 天验证窗口，不生成提交文件。

```bash
PYTHONPATH=src python3 -m store_sales.cli run \
  --data-dir data/raw \
  --output-dir artifacts/repro/smoke_histgbdt \
  --train-start-date 2015-01-01 \
  --validation-horizon 16 \
  --validation-windows 1 \
  --feature-profile baseline \
  --model-type hist_gbdt \
  --skip-submission
```

预期产物：

```text
artifacts/repro/smoke_histgbdt/validation_metrics.json
artifacts/repro/smoke_histgbdt/validation_summary.csv
artifacts/repro/smoke_histgbdt/validation_predictions.csv
artifacts/repro/smoke_histgbdt/validation_predictions_fold_01.csv
```

检查方式：

```bash
ls artifacts/repro/smoke_histgbdt
```

如果这一步失败，先不要跑 LightGBM，优先检查数据文件是否齐全、虚拟环境是否激活、`PYTHONPATH=src` 是否带上。

### 2. 复现当前主验证协议

当前正式验证协议是 `August / pre-test explicit windows`，不是随机切分。

```bash
PYTHONPATH=src python3 -m store_sales.cli run \
  --data-dir data/raw \
  --output-dir artifacts/repro/lightgbm_baseline_validation \
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

预期产物：

```text
artifacts/repro/lightgbm_baseline_validation/validation_metrics.json
artifacts/repro/lightgbm_baseline_validation/validation_summary.csv
artifacts/repro/lightgbm_baseline_validation/validation_predictions.csv
artifacts/repro/lightgbm_baseline_validation/validation_predictions_fold_01.csv
artifacts/repro/lightgbm_baseline_validation/validation_predictions_fold_02.csv
artifacts/repro/lightgbm_baseline_validation/validation_predictions_fold_03.csv
artifacts/repro/lightgbm_baseline_validation/validation_predictions_fold_04.csv
```

当前记录中的参考值：

| 指标 | 参考值 |
| --- | ---: |
| mean RMSLE | `0.486767` |
| RMSLE std | `0.070236` |
| worst fold RMSLE | `0.583115` |
| worst fold id | `3` |

由于依赖版本、LightGBM 底层实现和机器环境可能有细微差异，复现时允许最后几位小数有轻微波动。真正要检查的是：验证窗口一致、fold 数量一致、结果量级一致、不会出现异常泄漏或格式错误。

### 3. 重新生成 submission

如果要生成 Kaggle 可提交文件，去掉 `--skip-submission`，并使用新的输出目录避免覆盖历史产物：

```bash
PYTHONPATH=src python3 -m store_sales.cli run \
  --data-dir data/raw \
  --output-dir artifacts/repro/lightgbm_baseline_submission \
  --train-start-date 2013-01-01 \
  --validation-horizon 16 \
  --validation-window 2014-08-16:2014-08-31 \
  --validation-window 2015-08-16:2015-08-31 \
  --validation-window 2016-08-16:2016-08-31 \
  --validation-window 2017-07-31:2017-08-15 \
  --feature-profile baseline \
  --model-type lightgbm
```

预期产物：

```text
artifacts/repro/lightgbm_baseline_submission/submission.csv
artifacts/repro/lightgbm_baseline_submission/validation_summary.csv
artifacts/repro/lightgbm_baseline_submission/validation_metrics.json
```

`submission.csv` 应该满足：

- 列名为 `id,sales`。
- 行数和 `data/raw/sample_submission.csv` 一致。
- `id` 顺序和 sample submission 一致。
- `sales` 非负、非缺失、非无穷。

当前历史 best submission 路径是：

```text
artifacts/submissions/lightgbm_baseline_v1/submission.csv
```

但这个路径属于历史本地产物，不要求别人 clone 仓库后天然存在。复现时建议使用 `artifacts/repro/` 下的新目录。

## 如何检查结果是否可信

### 检查 validation summary

```bash
head artifacts/repro/lightgbm_baseline_validation/validation_summary.csv
```

应看到 4 个 fold，对应：

```text
2014-08-16:2014-08-31
2015-08-16:2015-08-31
2016-08-16:2016-08-31
2017-07-31:2017-08-15
```

### 检查 submission 格式

```bash
python3 -c "import pandas as pd; s=pd.read_csv('artifacts/repro/lightgbm_baseline_submission/submission.csv'); print(s.shape); print(s.head()); print(s['sales'].isna().sum(), (s['sales'] < 0).sum())"
```

预期：

- shape 第一维应等于 `sample_submission.csv` 行数。
- 缺失值数量为 `0`。
- 负数预测数量为 `0`。

### 检查结果来源

当前项目结果的可信来源按优先级是：

1. `docs/final_result_summary.md`
2. `reports/validation/august_lightgbm/run_summary.csv`
3. `reports/validation/august_lightgbm/stability_slices/stability_slice_report.md`
4. `docs/experiment_log.csv`
5. `docs/project_log.md`

如果这些文件里的数值和重新运行结果略有差异，先检查：

- 是否安装了 LightGBM。
- 是否使用了 `--model-type lightgbm`。
- 是否使用了全部 4 个 `--validation-window`。
- 是否使用 `--train-start-date 2013-01-01`。
- 是否使用 `--feature-profile baseline`。
- `transactions.csv` 是否存在。

## 常见问题

### 报错：缺少 `train.csv` 或其他 CSV

说明 `data/raw/` 下文件不齐。先确认：

```bash
ls data/raw
```

至少应包含 `train.csv`、`test.csv`、`sample_submission.csv`、`stores.csv`、`oil.csv`、`holidays_events.csv`。

### 报错：找不到 `store_sales`

通常是没有设置 `PYTHONPATH=src`，或没有安装 editable package。两种修法任选一种：

```bash
PYTHONPATH=src python3 -m store_sales.cli --help
```

或：

```bash
python3 -m pip install -e '.[lightgbm]'
python3 -m store_sales.cli --help
```

### 报错：没有 LightGBM

安装 LightGBM extra：

```bash
python3 -m pip install -e '.[lightgbm]'
```

如果暂时不想安装 LightGBM，可以先用 `--model-type hist_gbdt` 跑 smoke check，但不能用它复现当前 champion。

### 运行时间较长

这是正常的。当前数据是 `date + store_nbr + family` 粒度，多窗口递归验证会重复训练和预测。调试环境优先跑 smoke check，正式复现再跑 4 个 explicit windows。

## 可复现性说明口径

公开项目中，可复现性主要体现在三个层次：

- 原始 Kaggle 数据不进入 Git，但 `data/raw/` 的文件要求、依赖安装命令和运行命令都有明确说明。
- 本地验证结果可以通过固定的 validation windows 重新生成，包括 `validation_summary.csv`、fold predictions 和 submission 文件。
- Kaggle public score 属于外部评测结果，只在实验日志和结果总结中记录，不伪装成本地可复现指标。
