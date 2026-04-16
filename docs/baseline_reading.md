# Store Sales Baseline 阅读记录

## 阅读目标

本阶段目标是理解当前 baseline 如何从原始 CSV 变成可提交的 `submission.csv`，重点不是改代码，而是确认：

- 数据如何读取
- 哪些表在哪里 merge
- 特征如何生成
- 验证如何切分
- 如何避免未来信息泄漏
- 为什么需要递归预测
- 模型如何训练和输出

## 总体执行链路

```text
CLI 命令
  -> PipelineConfig
  -> load_competition_data()
  -> filter_training_window()
  -> build_validation_windows()
  -> 每个验证窗口：
       split_train_validation_window()
       fit_training_pipeline()
       recursive_forecast()
       rmsle()
  -> 用完整训练集训练 final_model
  -> recursive_forecast(test)
  -> artifacts/submission.csv
```

对应代码文件：

| 文件 | 负责内容 |
| --- | --- |
| `src/store_sales/cli.py` | 命令行入口，把参数转成配置 |
| `src/store_sales/config.py` | 存放 pipeline 参数 |
| `src/store_sales/data.py` | 读取和基础清洗原始 CSV |
| `src/store_sales/features.py` | 构造日历、外部变量、节假日、transactions、lag、rolling 特征 |
| `src/store_sales/modeling.py` | 编码类别特征、训练模型、预测并还原 sales |
| `src/store_sales/pipeline.py` | 串起训练、验证、递归预测、指标和提交文件 |

## 1. `data.py`：读取原始 CSV

核心函数：

```python
load_competition_data(config)
```

它做了几件事：

- 检查必需文件是否存在。
- 读取 `train.csv`、`test.csv`、`stores.csv`、`oil.csv`、`holidays_events.csv`。
- 如果存在，则读取 `transactions.csv` 和 `items.csv`。
- 把 `date` 转成 datetime。
- 给关键字段指定 dtype，减少内存占用。
- 将 `stores.csv` 的 `type` 重命名为 `store_type`，避免和 holidays 的 `type` 冲突。
- 按日期、门店、family 排序。
- 将训练集 `sales` 裁剪为非负。
- 将 `onpromotion` 缺失值填 0。

判断：

- 这里不做复杂特征，只做“安全读入”和基础规范化。
- `transactions.csv` 在这里只是读入，不直接 merge 到 train/test。

## 2. `features.py`：构造特征

### 2.1 FeatureContext

`build_feature_context(train_history, data)` 会提前准备一些可复用特征表：

- `stores`
- `oil_features`
- `national_holidays`
- `regional_holidays`
- `local_holidays`
- `weekday_transactions`
- `month_transactions`

关键点：

- `train_history` 是当前 fold 允许看到的历史训练数据。
- transactions 聚合只基于 `train_history` 截止日期之前的数据。
- 因此验证 fold 不会使用验证日期当天的真实 transactions。

### 2.2 oil 特征

`prepare_oil_features(oil)` 做了：

- 按日频补齐日期。
- 对 `dcoilwtico` 插值、前后填充。
- 构造：
  - `oil_price`
  - `oil_change_7`
  - `oil_mean_7`
  - `oil_mean_28`

判断：

- oil 是外生变量，覆盖测试期，可以按日期对齐使用。
- 当前滚动均值包含当前日期油价，这在“油价已知”的假设下可以接受。

### 2.3 holiday 特征

`prepare_holiday_features(holidays, locale)` 会按影响范围拆开：

- National
- Regional
- Local

它还会：

- 过滤 `transferred=True`
- 构造：
  - `*_holiday_count`
  - `*_is_holiday`
  - `*_is_event`
  - `*_is_work_day`

在 `add_known_exogenous_features()` 里 merge：

- National：按 `date`
- Regional：按 `date + state`
- Local：按 `date + city`

判断：

- 这比单一 `is_holiday` 更合理。
- 代码没有把 Local holiday 错误扩展到全国。

### 2.4 transactions 特征

`prepare_transaction_features(train_history, transactions, by)` 只做历史聚合：

- 按 `store_nbr + day_of_week` 计算平均 transactions。
- 按 `store_nbr + month` 计算平均 transactions。

关键防泄漏逻辑：

```python
tx = tx[tx["date"] <= train_history["date"].max()].copy()
```

这意味着每个验证 fold 只能使用该 fold 训练截止日期之前的 transactions。

判断：

- 这是正确方向。
- 它没有把验证期当天真实 transactions 直接 merge 进去。

### 2.5 calendar 特征

`add_calendar_features()` 构造：

- `day_of_week`
- `day_of_month`
- `day_of_year`
- `week_of_year`
- `month`
- `year`
- `quarter`
- `is_weekend`
- `is_month_start`
- `is_month_end`
- `is_quarter_start`
- `is_quarter_end`
- `is_payday`
- `days_since_earthquake`
- `earthquake_window_30`
- `dow_sin/dow_cos`
- `month_sin/month_cos`
- `doy_sin/doy_cos`

判断：

- 这些都是预测未来时已知的日历信息，可以安全使用。

### 2.6 lag 和 rolling 特征

训练时由 `add_training_lag_features()` 构造：

- `sales_lag_*`
- `sales_roll_mean_*`
- `sales_roll_std_*`
- `promo_lag_*`
- `promo_roll_sum_*`

关键防泄漏逻辑：

- sales lag 使用 `groupby(...).shift(lag)`。
- rolling 特征使用 `series.shift(1).rolling(...)`。

这表示：

- 预测某一天时，只使用这一天之前的历史 sales。
- 不使用当天真实 sales 参与当天特征。

## 3. `pipeline.py`：验证和递归预测

### 3.1 时间验证窗口

`build_validation_windows()` 根据：

- `validation_horizon`
- `validation_windows`
- `validation_step_days`

生成多个时间窗口。

当前项目常用：

```text
validation_horizon = 16
validation_windows = 3
validation_step_days = 16
```

得到 3 个不重叠的 16 天验证窗口。

判断：

- 这是时间序列验证，不是随机切分。
- 它更接近真实测试场景。

### 3.2 单个 fold 如何训练

每个验证窗口执行：

```text
train_part = validation_start 之前的数据
validation_part = validation_start 到 validation_end 的数据
```

然后：

```text
fit_training_pipeline(train_part)
recursive_forecast(history=train_part, future=validation_part)
```

判断：

- 模型只能用验证窗口之前的数据训练。
- 验证窗口真实 `sales` 只在最后算 RMSLE 时使用，不参与预测特征。

### 3.3 为什么 recursive_forecast 是核心

`recursive_forecast()` 的作用是模拟真实提交：

1. 用历史真实 sales 建立 `sales_history`。
2. 用历史和未来已知的 `onpromotion` 建立 `promotion_history`。
3. 按日期从前到后预测。
4. 每预测完一天，就把当天预测值写回 `sales_history`。
5. 下一天的 `sales_lag_1` 等特征就可以使用前一天预测值。

关键代码逻辑：

```text
day_predictions = model_bundle.predict(day_features)
sales_history[forecast_date] = day_predictions
```

判断：

- 这避免了多步预测时偷看未来真实 sales。
- 这也是为什么本项目比“直接一次性 predict validation/test”更贴近比赛。

## 4. `modeling.py`：模型训练与预测

### 4.1 类别编码

当前使用自定义 `OrdinalEncoder`：

- 对 `family`
- `city`
- `state`
- `store_type`

做整数编码。

判断：

- 对树模型可以接受。
- 对线性模型 ridge 不太公平，这也是 ridge 结果很差的原因之一。

### 4.2 目标变换

训练时：

```python
y_train = np.log1p(train_frame["sales"])
```

预测时：

```python
predictions = np.expm1(predictions)
predictions = np.clip(predictions, 0.0, None)
```

判断：

- 这和 RMSLE 指标一致。
- 预测结果最终会被裁剪为非负。

### 4.3 当前模型

当前支持：

- `seasonal_naive`
- `ridge`
- `hist_gbdt`
- `lightgbm`

当前主 baseline 是：

```text
hist_gbdt
```

## 5. `cli.py`：怎么运行

训练、验证、生成提交：

```bash
python3 -m store_sales.cli run \
  --data-dir data/raw \
  --output-dir artifacts \
  --train-start-date 2015-01-01 \
  --validation-windows 3 \
  --validation-step-days 16 \
  --feature-profile baseline \
  --model-type hist_gbdt
```

多模型对比：

```bash
python3 -m store_sales.cli compare \
  --data-dir data/raw \
  --output-dir artifacts/experiments \
  --report-dir reports/model_comparison \
  --experiments seasonal_naive ridge_baseline histgbdt_baseline \
  --validation-windows 3 \
  --validation-step-days 16
```

## 阶段 2 结论

| 问题 | 当前 baseline 的做法 |
| --- | --- |
| 如何读取数据？ | `data.py` 读取 CSV、转换日期、设置 dtype、排序、处理基础缺失 |
| 哪些表被 merge？ | `stores`、`oil`、National/Regional/Local holidays、历史聚合后的 transactions |
| 如何避免 transactions 泄漏？ | 每个 fold 只用 `train_history` 截止日期之前的 transactions 做聚合 |
| 如何避免 sales lag 泄漏？ | 训练 lag 使用 `shift`；递归预测用前一天预测值更新历史 |
| 如何验证？ | 多窗口时间切分，每个窗口只用过去训练、未来验证 |
| 如何提交？ | 用完整训练集训练 final model，对 `test.csv` 递归预测，输出 `id,sales` |

## 你需要自己复述的问题

1. `data.py` 为什么只做基础读取，而不在这里做复杂特征？
2. `features.py` 里 `stores.csv` 是怎么 merge 的？
3. 当前代码如何避免使用验证期真实 transactions？
4. 训练时为什么 lag 特征要用 `shift(1)`？
5. `recursive_forecast()` 为什么每预测完一天要把预测值写回 `sales_history`？
6. 为什么模型训练目标用 `log1p(sales)`？
