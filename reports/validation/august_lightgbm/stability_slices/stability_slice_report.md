# Stability Slice Report: `lightgbm_baseline` vs `histgbdt_baseline`

本报告用于解释 public-like 稳定性风险：一个 profile 即使 mean validation 更好，也可能在某些非目标切片或 test-like 分布上更差。

## Overall Windows

| fold_id | validation_start | validation_end | validation_rmsle_baseline | validation_rmsle_experiment | rmsle_delta |
| --- | --- | --- | --- | --- | --- |
| 1 | 2014-08-16 | 2014-08-31 | 0.394681 | 0.442921 | 0.048240 |
| 2 | 2015-08-16 | 2015-08-31 | 0.479351 | 0.520300 | 0.040950 |
| 3 | 2016-08-16 | 2016-08-31 | 0.656282 | 0.583115 | -0.073167 |
| 4 | 2017-07-31 | 2017-08-15 | 0.431742 | 0.400730 | -0.031013 |

- Mean RMSLE delta: `-0.003747`.

## Target vs Non-Target

| target_group | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales | mean_predicted_sales_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_target_family | 110592 | 0.493954 | 0.489086 | -0.004869 | 391.875773 | 372.652839 | 392.620551 | 19.967712 |
| target_family | 3456 | 0.681330 | 0.572111 | -0.109219 | 22.151042 | 7.748145 | 11.518546 | 3.770401 |

## Non-Target Family Side Effects

- Non-target families worsened: `13`.
- Non-target families improved: `19`.

Top worsened non-target families:

| family | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRODUCE | 3456 | 0.550261 | 0.631510 | 0.081250 | 1627.535043 | 1550.442918 | 1641.940622 |
| CELEBRATION | 3456 | 0.578198 | 0.616955 | 0.038757 | 9.937500 | 8.621350 | 9.488952 |
| HOME AND KITCHEN II | 3456 | 0.591666 | 0.625113 | 0.033447 | 20.253762 | 16.733023 | 17.391985 |
| HOME CARE | 3456 | 0.486270 | 0.515050 | 0.028780 | 207.771991 | 205.169975 | 208.785158 |
| HOME AND KITCHEN I | 3456 | 0.598795 | 0.627046 | 0.028251 | 20.398148 | 16.747008 | 17.419930 |
| PREPARED FOODS | 3456 | 0.411788 | 0.434475 | 0.022687 | 94.480681 | 88.205088 | 90.465114 |
| PLAYERS AND ELECTRONICS | 3456 | 0.526821 | 0.548323 | 0.021503 | 7.936921 | 6.854421 | 7.849995 |
| MEATS | 3456 | 0.435613 | 0.456857 | 0.021244 | 344.038126 | 319.380921 | 324.674198 |
| PET SUPPLIES | 3456 | 0.485206 | 0.502304 | 0.017097 | 4.966435 | 4.387411 | 4.826054 |
| LADIESWEAR | 3456 | 0.530234 | 0.545665 | 0.015431 | 8.326100 | 7.134303 | 7.783023 |

## Promotion Bin Stability

| promotion_bin | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_onpromotion | experiment_mean_onpromotion |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 8815 | 0.366693 | 0.394305 | 0.027611 | 1.000000 | 1.000000 |
| 2-5 | 9170 | 0.349739 | 0.365332 | 0.015593 | 3.079935 | 3.079935 |
| 51+ | 1512 | 0.223664 | 0.232925 | 0.009261 | 86.517196 | 86.517196 |
| 0 | 80820 | 0.549915 | 0.542051 | -0.007864 | 0.000000 | 0.000000 |
| 6-10 | 6345 | 0.347289 | 0.284873 | -0.062416 | 7.675177 | 7.675177 |

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
| CLEANING | 11-50 | 1416.000000 | 704.000000 | 0.012276 | 0.000975 | 0.317000 | 0.317975 |
| PRODUCE | 2-5 | 525.000000 | 320.000000 | 0.006620 | 0.170603 | 0.367469 | 0.538072 |
| PRODUCE | 1 | 340.000000 | 267.000000 | 0.006383 | 0.029936 | 0.275063 | 0.304999 |
| PREPARED FOODS | 0 | 2623.000000 | 821.000000 | 0.005796 | 0.014344 | 0.436618 | 0.450962 |
| PRODUCE | 51+ | 372.000000 | 164.000000 | 0.002490 | 0.083955 | 0.278311 | 0.362266 |
| LADIESWEAR | 6-10 | 35.000000 | 46.000000 | 0.001306 | 0.066700 | 0.382636 | 0.449336 |
| MEATS | 11-50 | 352.000000 | 117.000000 | 0.001017 | 0.113694 | 0.258929 | 0.372623 |
| CELEBRATION | 0 | 3376.000000 | 851.000000 | 0.000246 | 0.040013 | 0.581150 | 0.621163 |

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

- `lightgbm_baseline` has non-target family regressions. This is a plausible reason why public score can worsen even when mean validation improves.
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
