# August / Pre-Test Validation Windows

本报告比较多个 validation run 在同一组显式时间窗口上的表现。Lower RMSLE is better.

## Decision Rule

- 先看 mean RMSLE。
- 再看 worst fold，避免只改善平均值但牺牲某个时间窗口。
- 如果某个 profile 是根据某个 fold 设计的，还要检查它是否能在历史同季窗口稳定改善。

## Run Summary

| run_name | validation_rmsle_mean | validation_rmsle_std | validation_rmsle_min | validation_rmsle_max | worst_fold_id | train_rows_min | train_rows_max | artifacts_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| histgbdt_school_supplies_aug_promo | 0.486425 | 0.102037 | 0.390796 | 0.655352 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_school_supplies_aug_promo |
| histgbdt_baseline | 0.490514 | 0.100302 | 0.394681 | 0.656282 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_baseline |

## Fold Comparison

| fold_id | validation_start | validation_end | baseline_rmsle | histgbdt_school_supplies_aug_promo_rmsle | histgbdt_school_supplies_aug_promo_delta_vs_histgbdt_baseline |
| --- | --- | --- | --- | --- | --- |
| 1 | 2014-08-16 | 2014-08-31 | 0.394681 | 0.390796 | -0.003885 |
| 2 | 2015-08-16 | 2015-08-31 | 0.479351 | 0.475061 | -0.004289 |
| 3 | 2016-08-16 | 2016-08-31 | 0.656282 | 0.655352 | -0.000930 |
| 4 | 2017-07-31 | 2017-08-15 | 0.431742 | 0.424491 | -0.007251 |

## Interpretation

- 当前 mean RMSLE 最低的是 `histgbdt_school_supplies_aug_promo`，mean=`0.486425`。
- Baseline `histgbdt_baseline` 的 mean RMSLE 是 `0.490514`。
- 如果本地 historical windows 与 Kaggle public score 方向冲突，优先相信 public score，同时回头修正验证设计。
- 这次正好出现方向冲突：August / pre-test windows 仍然认为 `school_supplies_aug_promo` 更好，但 Kaggle public score 是 `0.59096`，差于 baseline 的 `0.58410`。
- 结论：仅加入历史 8 月窗口仍不足以筛掉这个失败实验。下一步不能只依赖 mean RMSLE，需要增加 public-like 稳定性检查，例如非目标 family 副作用、promotion 分布切片、store/family 分组漂移。
