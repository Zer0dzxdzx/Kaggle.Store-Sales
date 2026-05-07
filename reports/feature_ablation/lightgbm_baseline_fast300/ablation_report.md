# Feature Ablation Report

Lower RMSLE is better. Positive delta means removing the feature group made validation worse, so the group appears useful under this validation setup.
Negative delta means removing the group improved validation, so the group is a removal or redesign candidate.
Compare this report only with runs that use the same model type, feature profile, validation windows, and model parameter overrides.

## Setup

- Model type: `lightgbm`
- LightGBM preset: `baseline`
- Model params: `force_row_wise=True|n_estimators=300|verbosity=-1`
- Feature profile: `baseline`
- Early stopping rounds: ``
- Early stopping validation days: `0`
- Train start date: `2013-01-01`
- Validation horizon: `16`
- Validation windows: `4`
- Validation step days: `16`
- Explicit windows: `2014-08-16:2014-08-31|2015-08-16:2015-08-31|2016-08-16:2016-08-31|2017-07-31:2017-08-15`
- Skipped groups: ``

## Baseline

- Mean RMSLE: `0.498996`
- Worst fold RMSLE: `0.594955`

## Results

| run_name | ablation_group | ablated_feature_count | validation_rmsle_mean | validation_rmsle_max | mean_delta_vs_baseline | worst_delta_vs_baseline | ablation_signal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| without_sales_rolling | sales_rolling | 8 | 0.560107 | 0.650559 | 0.061111 | 0.055603 | useful |
| without_promotion | promotion | 6 | 0.541026 | 0.631955 | 0.042030 | 0.036999 | useful |
| without_earthquake | earthquake | 2 | 0.519179 | 0.673452 | 0.020182 | 0.078497 | useful |
| without_calendar | calendar | 19 | 0.515354 | 0.582703 | 0.016358 | -0.012253 | mixed_mean_worse_worst_better |
| without_store_metadata | store_metadata | 4 | 0.512200 | 0.620031 | 0.013204 | 0.025076 | useful |
| without_holidays | holidays | 12 | 0.506892 | 0.612915 | 0.007896 | 0.017960 | useful |
| without_identity | identity | 2 | 0.504694 | 0.599011 | 0.005698 | 0.004056 | useful |
| without_transactions | transactions | 2 | 0.502873 | 0.617616 | 0.003877 | 0.022661 | useful |
| baseline | baseline | 0 | 0.498996 | 0.594955 | 0.000000 | 0.000000 | neutral |
| without_oil | oil | 4 | 0.498194 | 0.588949 | -0.000803 | -0.006006 | removal_candidate |
| without_sales_lags | sales_lags | 4 | 0.490233 | 0.611028 | -0.008763 | 0.016073 | mixed_mean_better_worst_worse |

## Interpretation

- Strongest useful original feature group: `sales_rolling` (mean delta `0.061111`).
- Strongest robust removal candidate: `oil` (mean delta `-0.000803`).
- Largest mixed result: `calendar` (`mixed_mean_worse_worst_better`; mean delta `0.016358`, worst delta `-0.012253`). Treat this as follow-up evidence, not a direct keep/drop decision.

## Ablated Columns

### `sales_rolling`

Remove rolling sales mean/std features.

`sales_roll_mean_7|sales_roll_std_7|sales_roll_mean_14|sales_roll_std_14|sales_roll_mean_28|sales_roll_std_28|sales_roll_mean_56|sales_roll_std_56`

### `promotion`

Remove current and historical promotion features.

`onpromotion|promo_lag_1|promo_lag_7|promo_lag_14|promo_roll_sum_7|promo_roll_sum_14`

### `earthquake`

Remove earthquake recency/window features.

`days_since_earthquake|earthquake_window_30`

### `calendar`

Remove regular calendar, payday, and cyclic time features.

`day_of_week|day_of_month|day_of_year|week_of_year|month|year|quarter|is_weekend|is_month_start|is_month_end|is_quarter_start|is_quarter_end|is_payday|dow_sin|dow_cos|month_sin|month_cos|doy_sin|doy_cos`

### `store_metadata`

Remove store city, state, type, and cluster metadata.

`city|state|store_type|cluster`

### `holidays`

Remove national, regional, and local holiday/event/work-day indicators.

`national_holiday_count|national_is_holiday|national_is_event|national_is_work_day|regional_holiday_count|regional_is_holiday|regional_is_event|regional_is_work_day|local_holiday_count|local_is_holiday|local_is_event|local_is_work_day`

### `identity`

Remove direct store/family identifiers while keeping history features keyed by them.

`store_nbr|family`

### `transactions`

Remove historical store transaction aggregates.

`transactions_weekday_mean|transactions_month_mean`

### `oil`

Remove oil price level/change/rolling mean features.

`oil_price|oil_change_7|oil_mean_7|oil_mean_28`

### `sales_lags`

Remove raw sales lag features.

`sales_lag_1|sales_lag_7|sales_lag_14|sales_lag_28`
