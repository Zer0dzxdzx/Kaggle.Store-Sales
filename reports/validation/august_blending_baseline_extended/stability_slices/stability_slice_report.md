# Stability Slice Report: `blend_histgbdt_baseline_histgbdt_extended_base_w550` vs `histgbdt_baseline`

本报告用于解释 public-like 稳定性风险：一个 profile 即使 mean validation 更好，也可能在某些非目标切片或 test-like 分布上更差。

## Overall Windows

| fold_id | validation_start | validation_end | validation_rmsle_baseline | validation_rmsle_experiment | rmsle_delta |
| --- | --- | --- | --- | --- | --- |
| 1 | 2014-08-16 | 2014-08-31 | 0.394681 | 0.384264 | -0.010417 |
| 2 | 2015-08-16 | 2015-08-31 | 0.479351 | 0.488590 | 0.009239 |
| 3 | 2016-08-16 | 2016-08-31 | 0.656282 | 0.645720 | -0.010562 |
| 4 | 2017-07-31 | 2017-08-15 | 0.431742 | 0.428782 | -0.002960 |

- Mean RMSLE delta: `-0.003675`.

## Target vs Non-Target

| target_group | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales | mean_predicted_sales_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| target_family | 3456 | 0.681330 | 0.681433 | 0.000103 | 22.151042 | 7.748145 | 7.361123 | -0.387022 |
| non_target_family | 110592 | 0.493954 | 0.489896 | -0.004058 | 391.875773 | 372.652839 | 373.167650 | 0.514811 |

## Non-Target Family Side Effects

- Non-target families worsened: `7`.
- Non-target families improved: `25`.

Top worsened non-target families:

| family | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIQUOR,WINE,BEER | 3456 | 0.601621 | 0.620334 | 0.018712 | 79.511574 | 69.698511 | 68.658769 |
| GROCERY I | 3456 | 0.474039 | 0.482435 | 0.008396 | 3857.389001 | 3654.444889 | 3654.600551 |
| PRODUCE | 3456 | 0.550261 | 0.557287 | 0.007026 | 1627.535043 | 1550.442918 | 1558.538465 |
| FROZEN FOODS | 3456 | 0.421913 | 0.424226 | 0.002313 | 117.647710 | 113.003700 | 112.887999 |
| PREPARED FOODS | 3456 | 0.411788 | 0.414051 | 0.002263 | 94.480681 | 88.205088 | 88.712134 |
| BABY CARE | 3456 | 0.331980 | 0.333886 | 0.001906 | 0.143519 | 0.336842 | 0.343609 |
| DAIRY | 3456 | 0.432745 | 0.433780 | 0.001035 | 755.686921 | 719.490272 | 723.074731 |

## Promotion Bin Stability

| promotion_bin | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_onpromotion | experiment_mean_onpromotion |
| --- | --- | --- | --- | --- | --- | --- |
| 2-5 | 9170 | 0.349739 | 0.360318 | 0.010579 | 3.079935 | 3.079935 |
| 1 | 8815 | 0.366693 | 0.375223 | 0.008530 | 1.000000 | 1.000000 |
| 51+ | 1512 | 0.223664 | 0.230394 | 0.006730 | 86.517196 | 86.517196 |
| 11-50 | 7386 | 0.367848 | 0.369762 | 0.001915 | 23.278635 | 23.278635 |
| 6-10 | 6345 | 0.347289 | 0.347732 | 0.000443 | 7.675177 | 7.675177 |

## Validation/Test Distribution Drift

Top family-promotion share drift:

| family | promotion_bin | validation_rows | test_rows | validation_share | test_share | test_minus_validation_share | abs_share_delta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIQUOR,WINE,BEER | 0 | 2492.000000 | 116.000000 | 0.021850 | 0.004068 | -0.017782 | 0.017782 |
| BEVERAGES | 11-50 | 1397.000000 | 844.000000 | 0.012249 | 0.029602 | 0.017352 | 0.017352 |
| HOME AND KITCHEN II | 0 | 2613.000000 | 207.000000 | 0.022911 | 0.007260 | -0.015651 | 0.015651 |
| PERSONAL CARE | 11-50 | 244.000000 | 473.000000 | 0.002139 | 0.016590 | 0.014450 | 0.014450 |
| HOME CARE | 0 | 1683.000000 | 11.000000 | 0.014757 | 0.000386 | -0.014371 | 0.014371 |
| GROCERY I | 51+ | 550.000000 | 543.000000 | 0.004823 | 0.019045 | 0.014222 | 0.014222 |
| BEAUTY | 0 | 2831.000000 | 320.000000 | 0.024823 | 0.011223 | -0.013600 | 0.013600 |
| CLEANING | 11-50 | 1416.000000 | 704.000000 | 0.012416 | 0.024691 | 0.012276 | 0.012276 |
| HOME CARE | 6-10 | 751.000000 | 530.000000 | 0.006585 | 0.018589 | 0.012004 | 0.012004 |
| DAIRY | 11-50 | 771.000000 | 511.000000 | 0.006760 | 0.017922 | 0.011162 | 0.011162 |

Overweighted non-target family-promotion regressions:

| family | promotion_bin | validation_rows | test_rows | test_minus_validation_share | rmsle_delta | baseline_rmsle | experiment_rmsle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PERSONAL CARE | 11-50 | 244.000000 | 473.000000 | 0.014450 | 0.001471 | 0.232833 | 0.234303 |
| GROCERY I | 51+ | 550.000000 | 543.000000 | 0.014222 | 0.001617 | 0.181460 | 0.183077 |
| DAIRY | 11-50 | 771.000000 | 511.000000 | 0.011162 | 0.001179 | 0.210637 | 0.211816 |
| EGGS | 1 | 791.000000 | 398.000000 | 0.007023 | 0.010036 | 0.368295 | 0.378331 |
| PRODUCE | 2-5 | 525.000000 | 320.000000 | 0.006620 | 0.025945 | 0.367469 | 0.393413 |
| LINGERIE | 2-5 | 118.000000 | 204.000000 | 0.006120 | 0.001060 | 0.516657 | 0.517717 |
| PREPARED FOODS | 0 | 2623.000000 | 821.000000 | 0.005796 | 0.001366 | 0.436618 | 0.437984 |
| DAIRY | 6-10 | 332.000000 | 199.000000 | 0.004068 | 0.002596 | 0.228343 | 0.230939 |
| HOME AND KITCHEN I | 2-5 | 203.000000 | 130.000000 | 0.002780 | 0.002834 | 0.437717 | 0.440551 |
| PRODUCE | 51+ | 372.000000 | 164.000000 | 0.002490 | 0.019188 | 0.278311 | 0.297499 |

Top store-family-promotion share drift:

| store_nbr | city | store_type | family | promotion_bin | validation_rows | test_rows | validation_share | test_share | test_minus_validation_share | abs_share_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 48 | Quito | A | LINGERIE | 0 | 64.000000 | 0.000000 | 0.000561 | 0.000000 | -0.000561 | 0.000561 |
| 45 | Quito | A | LINGERIE | 0 | 60.000000 | 0.000000 | 0.000526 | 0.000000 | -0.000526 | 0.000526 |
| 48 | Quito | A | LINGERIE | 2-5 | 0.000000 | 15.000000 | 0.000000 | 0.000526 | 0.000526 | 0.000526 |
| 46 | Quito | A | PLAYERS AND ELECTRONICS | 0 | 63.000000 | 1.000000 | 0.000552 | 0.000035 | -0.000517 | 0.000517 |
| 47 | Quito | A | LINGERIE | 0 | 56.000000 | 0.000000 | 0.000491 | 0.000000 | -0.000491 | 0.000491 |
| 47 | Quito | A | BREAD/BAKERY | 11-50 | 5.000000 | 15.000000 | 0.000044 | 0.000526 | 0.000482 | 0.000482 |
| 38 | Loja | D | HOME AND KITCHEN I | 0 | 55.000000 | 0.000000 | 0.000482 | 0.000000 | -0.000482 | 0.000482 |
| 46 | Quito | A | BREAD/BAKERY | 11-50 | 10.000000 | 16.000000 | 0.000088 | 0.000561 | 0.000473 | 0.000473 |
| 52 | Manta | A | BEVERAGES | 11-50 | 10.000000 | 16.000000 | 0.000088 | 0.000561 | 0.000473 | 0.000473 |
| 52 | Manta | A | BREAD/BAKERY | 11-50 | 11.000000 | 16.000000 | 0.000096 | 0.000561 | 0.000465 | 0.000465 |

## Interpretation

- `blend_histgbdt_baseline_histgbdt_extended_base_w550` has non-target family regressions. This is a plausible reason why public score can worsen even when mean validation improves.
- Distribution drift tables do not use `sales`; they only compare validation/test row composition by known fields.
- A candidate profile should not be promoted only because mean RMSLE improves. It must also pass non-target slice and test-like distribution checks.

## Generated Tables

- `tables/validation_comparison.csv`
- `tables/target_group_comparison.csv`
- `tables/family_comparison.csv`
- `tables/family_promotion_comparison.csv`
- `tables/promotion_bin_comparison.csv`
- `tables/family_promotion_drift.csv`
- `tables/store_family_promotion_drift.csv`
- `tables/overweighted_non_target_regressions.csv`
