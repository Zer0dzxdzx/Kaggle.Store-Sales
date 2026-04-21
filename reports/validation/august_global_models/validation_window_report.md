# Global Model and Feature Comparison on August / Pre-Test Windows

本报告比较多个 validation run 在同一组显式时间窗口上的表现。Lower RMSLE is better.

## Decision Rule

- 先看 mean RMSLE。
- 再看 worst fold，避免只改善平均值但牺牲某个时间窗口。
- 如果某个 profile 是根据某个 fold 设计的，还要检查它是否能在历史同季窗口稳定改善。

## Run Summary

| run_name | validation_rmsle_mean | validation_rmsle_std | validation_rmsle_min | validation_rmsle_max | worst_fold_id | train_rows_min | train_rows_max | artifacts_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| histgbdt_baseline | 0.490514 | 0.100302 | 0.394681 | 0.656282 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_baseline |
| histgbdt_compact | 0.492959 | 0.108543 | 0.372194 | 0.666164 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_compact |
| histgbdt_extended | 0.500922 | 0.100165 | 0.383794 | 0.633934 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_extended |
| seasonal_naive | 0.624068 | 0.134493 | 0.472397 | 0.821798 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/seasonal_naive |
| ridge_baseline | 2.892314 | 0.133261 | 2.683288 | 3.042849 | 2 | 1053162 | 2972376 | artifacts/validation/august_windows/ridge_baseline |

## Fold Comparison

| fold_id | seasonal_naive_rmsle | seasonal_naive_delta_vs_histgbdt_baseline | ridge_baseline_rmsle | ridge_baseline_delta_vs_histgbdt_baseline | histgbdt_compact_rmsle | histgbdt_compact_delta_vs_histgbdt_baseline | validation_start | validation_end | baseline_rmsle | histgbdt_extended_rmsle | histgbdt_extended_delta_vs_histgbdt_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.472397 | 0.077716 | 2.683288 | 2.288608 | 0.372194 | -0.022487 | 2014-08-16 | 2014-08-31 | 0.394681 | 0.383794 | -0.010887 |
| 2 | 0.668832 | 0.189481 | 3.042849 | 2.563499 | 0.490898 | 0.011547 | 2015-08-16 | 2015-08-31 | 0.479351 | 0.558534 | 0.079183 |
| 3 | 0.821798 | 0.165516 | 2.883020 | 2.226738 | 0.666164 | 0.009882 | 2016-08-16 | 2016-08-31 | 0.656282 | 0.633934 | -0.022348 |
| 4 | 0.533245 | 0.101503 | 2.960097 | 2.528355 | 0.442582 | 0.010839 | 2017-07-31 | 2017-08-15 | 0.431742 | 0.427425 | -0.004318 |

## Interpretation

- 当前 mean RMSLE 最低的是 `histgbdt_baseline`，mean=`0.490514`。
- Baseline `histgbdt_baseline` 的 mean RMSLE 是 `0.490514`。
- 如果本地 historical windows 与 Kaggle public score 方向冲突，优先相信 public score，同时回头修正验证设计。
- `histgbdt_compact` 在 fold 1 更好，但 fold 2/3/4 都比 baseline 差，mean RMSLE 也更差。
- `histgbdt_extended` 在 fold 1/3/4 更好，但 fold 2 大幅变差，导致 mean RMSLE 差于 baseline。
- `seasonal_naive` 和 `ridge_baseline` 明显弱于 tree baseline，只适合作为参考基准，不适合作为下一版提交候选。
- 本轮没有发现比 baseline 更稳的全局特征或模型方案；下一步如果继续模型方向，应优先补 LightGBM 或做 tree baseline 与稳健 seasonal benchmark 的 blending，而不是继续扩大 lag/window。
