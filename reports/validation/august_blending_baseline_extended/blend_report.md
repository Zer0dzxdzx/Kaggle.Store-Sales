# Baseline + Extended Blending on August / Pre-Test Windows

本报告测试 `histgbdt_baseline` 与 `histgbdt_extended` 的简单 prediction blending。Lower RMSLE is better.

## Decision Rule

- 先看 mean RMSLE 是否低于 baseline。
- 再看 worst fold，避免平均分小幅改善但最差窗口恶化。
- 这里只做 validation blending；除非验证稳定优于 baseline，否则不生成 Kaggle submission。

## Run Summary

| run_name | validation_rmsle_mean | validation_rmsle_std | validation_rmsle_min | validation_rmsle_max | worst_fold_id | train_rows_min | train_rows_max | artifacts_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| blend_histgbdt_baseline_histgbdt_extended_base_w550 | 0.486839 | 0.098917 | 0.384264 | 0.645720 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w550 |
| blend_histgbdt_baseline_histgbdt_extended_base_w500 | 0.486846 | 0.098688 | 0.383647 | 0.644631 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w500 |
| blend_histgbdt_baseline_histgbdt_extended_base_w600 | 0.486927 | 0.099135 | 0.384983 | 0.646821 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w600 |
| blend_histgbdt_baseline_histgbdt_extended_base_w450 | 0.486956 | 0.098451 | 0.383134 | 0.643552 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w450 |
| blend_histgbdt_baseline_histgbdt_extended_base_w650 | 0.487102 | 0.099339 | 0.385806 | 0.647937 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w650 |
| blend_histgbdt_baseline_histgbdt_extended_base_w400 | 0.487184 | 0.098208 | 0.382724 | 0.642480 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w400 |
| blend_histgbdt_baseline_histgbdt_extended_base_w700 | 0.487359 | 0.099528 | 0.386734 | 0.649068 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w700 |
| blend_histgbdt_baseline_histgbdt_extended_base_w350 | 0.487547 | 0.097968 | 0.382418 | 0.641415 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w350 |
| blend_histgbdt_baseline_histgbdt_extended_base_w750 | 0.487694 | 0.099702 | 0.387769 | 0.650216 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w750 |
| blend_histgbdt_baseline_histgbdt_extended_base_w300 | 0.488071 | 0.097738 | 0.382220 | 0.640354 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w300 |
| blend_histgbdt_baseline_histgbdt_extended_base_w800 | 0.488106 | 0.099859 | 0.388914 | 0.651383 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w800 |
| blend_histgbdt_baseline_histgbdt_extended_base_w850 | 0.488592 | 0.099999 | 0.390172 | 0.652572 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w850 |
| blend_histgbdt_baseline_histgbdt_extended_base_w900 | 0.489154 | 0.100120 | 0.391548 | 0.653783 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w900 |
| blend_histgbdt_baseline_histgbdt_extended_base_w950 | 0.489793 | 0.100221 | 0.393048 | 0.655019 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w950 |
| blend_histgbdt_baseline_histgbdt_extended_base_w980 | 0.490215 | 0.100272 | 0.394011 | 0.655773 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w980 |
| blend_histgbdt_baseline_histgbdt_extended_base_w990 | 0.490363 | 0.100287 | 0.394343 | 0.656027 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/blends_baseline_extended/blend_histgbdt_baseline_histgbdt_extended_base_w990 |
| histgbdt_baseline | 0.490514 | 0.100302 | 0.394681 | 0.656282 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_baseline |
| histgbdt_extended | 0.500922 | 0.100165 | 0.383794 | 0.633934 | 3 | 1053162 | 2972376 | artifacts/validation/august_windows/histgbdt_extended |

## Fold Comparison

| fold_id | validation_start | validation_end | baseline_rmsle | histgbdt_extended_rmsle | histgbdt_extended_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w990_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w990_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w980_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w980_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w950_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w950_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w900_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w900_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w850_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w850_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w800_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w800_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w750_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w750_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w700_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w700_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w650_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w650_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w600_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w600_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w550_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w550_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w500_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w500_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w450_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w450_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w400_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w400_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w350_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w350_delta_vs_histgbdt_baseline | blend_histgbdt_baseline_histgbdt_extended_base_w300_rmsle | blend_histgbdt_baseline_histgbdt_extended_base_w300_delta_vs_histgbdt_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2014-08-16 | 2014-08-31 | 0.394681 | 0.383794 | -0.010887 | 0.394343 | -0.000338 | 0.394011 | -0.000670 | 0.393048 | -0.001633 | 0.391548 | -0.003133 | 0.390172 | -0.004509 | 0.388914 | -0.005767 | 0.387769 | -0.006912 | 0.386734 | -0.007947 | 0.385806 | -0.008875 | 0.384983 | -0.009698 | 0.384264 | -0.010417 | 0.383647 | -0.011034 | 0.383134 | -0.011547 | 0.382724 | -0.011957 | 0.382418 | -0.012262 | 0.382220 | -0.012460 |
| 2 | 2015-08-16 | 2015-08-31 | 0.479351 | 0.558534 | 0.079183 | 0.479422 | 0.000072 | 0.479500 | 0.000150 | 0.479773 | 0.000422 | 0.480343 | 0.000993 | 0.481053 | 0.001702 | 0.481902 | 0.002552 | 0.482897 | 0.003546 | 0.484047 | 0.004696 | 0.485366 | 0.006015 | 0.486872 | 0.007522 | 0.488590 | 0.009239 | 0.490549 | 0.011198 | 0.492791 | 0.013440 | 0.495369 | 0.016018 | 0.498357 | 0.019006 | 0.501859 | 0.022508 |
| 3 | 2016-08-16 | 2016-08-31 | 0.656282 | 0.633934 | -0.022348 | 0.656027 | -0.000255 | 0.655773 | -0.000509 | 0.655019 | -0.001263 | 0.653783 | -0.002499 | 0.652572 | -0.003710 | 0.651383 | -0.004899 | 0.650216 | -0.006066 | 0.649068 | -0.007214 | 0.647937 | -0.008345 | 0.646821 | -0.009460 | 0.645720 | -0.010562 | 0.644631 | -0.011651 | 0.643552 | -0.012730 | 0.642480 | -0.013801 | 0.641415 | -0.014867 | 0.640354 | -0.015928 |
| 4 | 2017-07-31 | 2017-08-15 | 0.431742 | 0.427425 | -0.004318 | 0.431659 | -0.000084 | 0.431576 | -0.000166 | 0.431332 | -0.000410 | 0.430942 | -0.000800 | 0.430573 | -0.001169 | 0.430224 | -0.001519 | 0.429895 | -0.001848 | 0.429586 | -0.002156 | 0.429298 | -0.002445 | 0.429030 | -0.002713 | 0.428782 | -0.002960 | 0.428555 | -0.003187 | 0.428348 | -0.003394 | 0.428162 | -0.003580 | 0.427997 | -0.003746 | 0.427852 | -0.003891 |

## Interpretation

- 当前 mean RMSLE 最低的是 `blend_histgbdt_baseline_histgbdt_extended_base_w550`，mean=`0.486839`。
- Baseline `histgbdt_baseline` 的 mean RMSLE 是 `0.490514`。
- 最优 blending 相比 baseline 的 mean RMSLE delta 为 `-0.003675`。
- 最优 blending 有 `1` 个 fold 差于 baseline；最大回退出现在 fold `2`，delta=`0.009239`。
- 只有通过 stability slice checks 后，才应考虑生成 Kaggle submission。
