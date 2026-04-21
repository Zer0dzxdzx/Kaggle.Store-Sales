# LightGBM Baseline on August / Pre-Test Windows

本报告比较多个 validation run 在同一组显式时间窗口上的表现。Lower RMSLE is better.

## Decision Rule

- 先看 mean RMSLE。
- 再看 worst fold，避免只改善平均值但牺牲某个时间窗口。
- 如果某个 profile 是根据某个 fold 设计的，还要检查它是否能在历史同季窗口稳定改善。

## Run Summary

| run_name | validation_rmsle_mean | validation_rmsle_std | validation_rmsle_min | validation_rmsle_max | worst_fold_id | train_rows_min | train_rows_max | artifacts_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lightgbm_baseline | 0.486767 | 0.070236 | 0.400730 | 0.583115 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/lightgbm_baseline |
| blend_histgbdt_baseline_histgbdt_extended_w550 | 0.486839 | 0.098917 | 0.384264 | 0.645720 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w550 |
| histgbdt_baseline | 0.490514 | 0.100302 | 0.394681 | 0.656282 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_baseline |
| histgbdt_extended | 0.500922 | 0.100165 | 0.383794 | 0.633934 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_extended |

## Fold Comparison

| fold_id | validation_start | validation_end | baseline_rmsle | lightgbm_baseline_rmsle | lightgbm_baseline_delta_vs_histgbdt_baseline | histgbdt_extended_rmsle | histgbdt_extended_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_w550_rmsle | blend_histgbdt_baseline_histgbdt_extended_w550_delta_vs_histgbdt_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2014-08-16 | 2014-08-31 | 0.394681 | 0.442921 | 0.048240 | 0.383794 | -0.010887 | 0.384264 | -0.010417 |
| 2 | 2015-08-16 | 2015-08-31 | 0.479351 | 0.520300 | 0.040950 | 0.558534 | 0.079183 | 0.488590 | 0.009239 |
| 3 | 2016-08-16 | 2016-08-31 | 0.656282 | 0.583115 | -0.073167 | 0.633934 | -0.022348 | 0.645720 | -0.010562 |
| 4 | 2017-07-31 | 2017-08-15 | 0.431742 | 0.400730 | -0.031013 | 0.427425 | -0.004318 | 0.428782 | -0.002960 |

## Interpretation

- 当前 mean RMSLE 最低的是 `lightgbm_baseline`，mean=`0.486767`。
- Baseline `histgbdt_baseline` 的 mean RMSLE 是 `0.490514`。
- 如果本地 historical windows 与 Kaggle public score 方向冲突，优先相信 public score，同时回头修正验证设计。
- `lightgbm_baseline` 的 mean RMSLE 和 worst fold 都优于 `histgbdt_baseline`，但改善主要来自 fold 3/4。
- `lightgbm_baseline` 在 fold 1/2 明显差于 baseline：fold 1 delta=`+0.048240`，fold 2 delta=`+0.040950`。
- `lightgbm_baseline` 的 worst fold 从 baseline 的 `0.656282` 降到 `0.583115`，说明它对最差窗口有明显修正。
- 与 simple blend 相比，`lightgbm_baseline` mean RMSLE 略低于 `blend_histgbdt_baseline_histgbdt_extended_w550`：`0.486767` vs `0.486839`。
- 结论：LightGBM 是当前最有价值的新候选，但不能只凭 mean RMSLE 直接替换 baseline；需要结合 stability slice checks 和 Kaggle public score 验证。
