# LightGBM Tuning on August / Pre-Test Windows

本报告比较多个 validation run 在同一组显式时间窗口上的表现。Lower RMSLE is better.

## Decision Rule

- 先看 mean RMSLE。
- 再看 worst fold，避免只改善平均值但牺牲某个时间窗口。
- 如果某个 profile 是根据某个 fold 设计的，还要检查它是否能在历史同季窗口稳定改善。

## Run Summary

| run_name | validation_rmsle_mean | validation_rmsle_std | validation_rmsle_min | validation_rmsle_max | worst_fold_id | train_rows_min | train_rows_max | artifacts_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lightgbm_baseline | 0.486767 | 0.070236 | 0.400730 | 0.583115 | 3 | 1053162 | 2972376 | artifacts/validation/lightgbm_tuning/lightgbm_baseline |
| lightgbm_shrinkage_es | 0.499285 | 0.124943 | 0.403487 | 0.710339 | 3 | 1053162 | 2972376 | artifacts/validation/lightgbm_tuning/lightgbm_shrinkage_es |
| lightgbm_conservative_es | 0.507772 | 0.120996 | 0.414622 | 0.711345 | 3 | 1053162 | 2972376 | artifacts/validation/lightgbm_tuning/lightgbm_conservative_es |
| lightgbm_regularized_es | 0.519939 | 0.126331 | 0.406631 | 0.717537 | 3 | 1053162 | 2972376 | artifacts/validation/lightgbm_tuning/lightgbm_regularized_es |

## Fold Comparison

| fold_id | validation_start | validation_end | baseline_rmsle | lightgbm_shrinkage_es_rmsle | lightgbm_shrinkage_es_delta_vs_lightgbm_baseline | lightgbm_regularized_es_rmsle | lightgbm_regularized_es_delta_vs_lightgbm_baseline | lightgbm_conservative_es_rmsle | lightgbm_conservative_es_delta_vs_lightgbm_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2014-08-16 | 2014-08-31 | 0.442921 | 0.403487 | -0.039434 | 0.406631 | -0.036290 | 0.418322 | -0.024599 |
| 2 | 2015-08-16 | 2015-08-31 | 0.520300 | 0.473901 | -0.046400 | 0.542609 | 0.022308 | 0.486800 | -0.033500 |
| 3 | 2016-08-16 | 2016-08-31 | 0.583115 | 0.710339 | 0.127224 | 0.717537 | 0.134422 | 0.711345 | 0.128230 |
| 4 | 2017-07-31 | 2017-08-15 | 0.400730 | 0.409412 | 0.008682 | 0.412980 | 0.012250 | 0.414622 | 0.013892 |

## Interpretation

- 当前 mean RMSLE 最低的是 `lightgbm_baseline`，mean=`0.486767`。
- Baseline `lightgbm_baseline` 的 mean RMSLE 是 `0.486767`。
- 如果本地 historical windows 与 Kaggle public score 方向冲突，优先相信 public score，同时回头修正验证设计。
