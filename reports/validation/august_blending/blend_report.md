# Baseline + Seasonal Naive Blending on August / Pre-Test Windows

本报告测试 `histgbdt_baseline` 与 `seasonal_naive` 的简单 prediction blending。Lower RMSLE is better.

## Decision Rule

- 先看 mean RMSLE 是否低于 baseline。
- 再看 worst fold，避免平均分小幅改善但最差窗口恶化。
- 这里只做 validation blending；除非验证稳定优于 baseline，否则不生成 Kaggle submission。

## Run Summary

| run_name | validation_rmsle_mean | validation_rmsle_std | validation_rmsle_min | validation_rmsle_max | worst_fold_id | train_rows_min | train_rows_max | artifacts_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| histgbdt_baseline | 0.490514 | 0.100302 | 0.394681 | 0.656282 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_baseline |
| blend_histgbdt_baseline_seasonal_naive_base_w990 | 0.495169 | 0.104205 | 0.400799 | 0.669048 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends/blend_histgbdt_baseline_seasonal_naive_base_w990 |
| blend_histgbdt_baseline_seasonal_naive_base_w980 | 0.498117 | 0.106408 | 0.405252 | 0.676621 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends/blend_histgbdt_baseline_seasonal_naive_base_w980 |
| blend_histgbdt_baseline_seasonal_naive_base_w950 | 0.503823 | 0.110651 | 0.414203 | 0.691015 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends/blend_histgbdt_baseline_seasonal_naive_base_w950 |
| blend_histgbdt_baseline_seasonal_naive_base_w900 | 0.509646 | 0.115225 | 0.423014 | 0.705751 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends/blend_histgbdt_baseline_seasonal_naive_base_w900 |
| blend_histgbdt_baseline_seasonal_naive_base_w850 | 0.513770 | 0.118618 | 0.428553 | 0.716212 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends/blend_histgbdt_baseline_seasonal_naive_base_w850 |
| blend_histgbdt_baseline_seasonal_naive_base_w800 | 0.517178 | 0.121405 | 0.431497 | 0.724687 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends/blend_histgbdt_baseline_seasonal_naive_base_w800 |
| blend_histgbdt_baseline_seasonal_naive_base_w700 | 0.523219 | 0.125909 | 0.433568 | 0.738714 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends/blend_histgbdt_baseline_seasonal_naive_base_w700 |
| blend_histgbdt_baseline_seasonal_naive_base_w500 | 0.535854 | 0.132311 | 0.442578 | 0.762252 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends/blend_histgbdt_baseline_seasonal_naive_base_w500 |
| seasonal_naive | 0.624068 | 0.134493 | 0.472397 | 0.821798 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/seasonal_naive |

## Fold Comparison

| fold_id | validation_start | validation_end | baseline_rmsle | seasonal_naive_rmsle | seasonal_naive_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_seasonal_naive_base_w990_rmsle | blend_histgbdt_baseline_seasonal_naive_base_w990_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_seasonal_naive_base_w980_rmsle | blend_histgbdt_baseline_seasonal_naive_base_w980_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_seasonal_naive_base_w950_rmsle | blend_histgbdt_baseline_seasonal_naive_base_w950_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_seasonal_naive_base_w900_rmsle | blend_histgbdt_baseline_seasonal_naive_base_w900_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_seasonal_naive_base_w850_rmsle | blend_histgbdt_baseline_seasonal_naive_base_w850_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_seasonal_naive_base_w800_rmsle | blend_histgbdt_baseline_seasonal_naive_base_w800_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_seasonal_naive_base_w700_rmsle | blend_histgbdt_baseline_seasonal_naive_base_w700_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_seasonal_naive_base_w500_rmsle | blend_histgbdt_baseline_seasonal_naive_base_w500_delta_vs_histgbdt_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2014-08-16 | 2014-08-31 | 0.394681 | 0.472397 | 0.077716 | 0.400799 | 0.006119 | 0.405252 | 0.010571 | 0.414203 | 0.019523 | 0.423014 | 0.028333 | 0.428553 | 0.033873 | 0.432450 | 0.037770 | 0.437734 | 0.043054 | 0.444717 | 0.050036 |
| 2 | 2015-08-16 | 2015-08-31 | 0.479351 | 0.668832 | 0.189481 | 0.479234 | -0.000116 | 0.479134 | -0.000216 | 0.478932 | -0.000419 | 0.478915 | -0.000435 | 0.479297 | -0.000054 | 0.480077 | 0.000726 | 0.482862 | 0.003511 | 0.493871 | 0.014521 |
| 3 | 2016-08-16 | 2016-08-31 | 0.656282 | 0.821798 | 0.165516 | 0.669048 | 0.012766 | 0.676621 | 0.020339 | 0.691015 | 0.034733 | 0.705751 | 0.049470 | 0.716212 | 0.059930 | 0.724687 | 0.068406 | 0.738714 | 0.082432 | 0.762252 | 0.105970 |
| 4 | 2017-07-31 | 2017-08-15 | 0.431742 | 0.533245 | 0.101503 | 0.431594 | -0.000148 | 0.431460 | -0.000282 | 0.431143 | -0.000599 | 0.430902 | -0.000841 | 0.431018 | -0.000724 | 0.431497 | -0.000246 | 0.433568 | 0.001825 | 0.442578 | 0.010835 |

## Interpretation

- 当前 mean RMSLE 最低的是 `histgbdt_baseline`，mean=`0.490514`。
- Baseline `histgbdt_baseline` 的 mean RMSLE 是 `0.490514`。
- 本轮 simple blending 没有超过 baseline，不应生成新的提交。
