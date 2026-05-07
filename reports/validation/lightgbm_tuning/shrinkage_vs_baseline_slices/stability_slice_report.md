# Stability Slice Report: `lightgbm_shrinkage_es` vs `lightgbm_baseline`

本报告用于解释 public-like 稳定性风险：一个 profile 即使 mean validation 更好，也可能在某些非目标切片或 test-like 分布上更差。

## Overall Windows

| fold_id | validation_start | validation_end | validation_rmsle_baseline | validation_rmsle_experiment | rmsle_delta |
| --- | --- | --- | --- | --- | --- |
| 1 | 2014-08-16 | 2014-08-31 | 0.442921 | 0.403487 | -0.039434 |
| 2 | 2015-08-16 | 2015-08-31 | 0.520300 | 0.473901 | -0.046400 |
| 3 | 2016-08-16 | 2016-08-31 | 0.583115 | 0.710339 | 0.127224 |
| 4 | 2017-07-31 | 2017-08-15 | 0.400730 | 0.409412 | 0.008682 |

- Mean RMSLE delta: `0.012518`.

## Target vs Non-Target

| target_group | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales | mean_predicted_sales_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| target_family | 3456 | 0.572111 | 0.671464 | 0.099353 | 22.151042 | 11.518546 | 7.474618 | -4.043928 |
| non_target_family | 110592 | 0.489086 | 0.509003 | 0.019917 | 391.875773 | 392.620551 | 385.131365 | -7.489186 |

## Non-Target Family Side Effects

- Non-target families worsened: `21`.
- Non-target families improved: `11`.

Top worsened non-target families:

| family | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BREAD/BAKERY | 3456 | 0.365734 | 0.508561 | 0.142827 | 503.204686 | 488.773865 | 494.722740 |
| DAIRY | 3456 | 0.378927 | 0.517447 | 0.138520 | 755.686921 | 750.627088 | 742.184420 |
| CLEANING | 3456 | 0.397133 | 0.530999 | 0.133866 | 1074.590856 | 1115.721289 | 1081.300850 |
| DELI | 3456 | 0.319435 | 0.445522 | 0.126087 | 276.775384 | 273.959369 | 276.881528 |
| EGGS | 3456 | 0.437229 | 0.509303 | 0.072073 | 181.616609 | 170.388817 | 172.076053 |
| BEVERAGES | 3456 | 0.454871 | 0.513742 | 0.058872 | 2628.432002 | 2670.019992 | 2595.071971 |
| GROCERY I | 3456 | 0.444012 | 0.497455 | 0.053443 | 3857.389001 | 3882.374155 | 3763.723475 |
| LIQUOR,WINE,BEER | 3456 | 0.572055 | 0.625161 | 0.053106 | 79.511574 | 73.949431 | 75.607595 |
| FROZEN FOODS | 3456 | 0.393049 | 0.444054 | 0.051005 | 117.647710 | 113.475136 | 115.651009 |
| PERSONAL CARE | 3456 | 0.416474 | 0.450289 | 0.033816 | 279.929109 | 268.313373 | 269.430601 |

## Promotion Bin Stability

| promotion_bin | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_onpromotion | experiment_mean_onpromotion |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 80820 | 0.542051 | 0.577447 | 0.035396 | 0.000000 | 0.000000 |
| 6-10 | 6345 | 0.284873 | 0.296295 | 0.011423 | 7.675177 | 7.675177 |
| 11-50 | 7386 | 0.296084 | 0.306766 | 0.010682 | 23.278635 | 23.278635 |
| 2-5 | 9170 | 0.365332 | 0.316150 | -0.049182 | 3.079935 | 3.079935 |
| 1 | 8815 | 0.394305 | 0.344585 | -0.049719 | 1.000000 | 1.000000 |

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
| PERSONAL CARE | 11-50 | 244.000000 | 473.000000 | 0.014450 | 0.000616 | 0.217632 | 0.218248 |
| BEAUTY | 1 | 433.000000 | 390.000000 | 0.009882 | 0.014852 | 0.398423 | 0.413274 |
| HOME AND KITCHEN II | 2-5 | 249.000000 | 344.000000 | 0.009882 | 0.001175 | 0.507212 | 0.508387 |
| HOME AND KITCHEN I | 1 | 494.000000 | 348.000000 | 0.007874 | 0.003379 | 0.471625 | 0.475004 |
| EGGS | 1 | 791.000000 | 398.000000 | 0.007023 | 0.003614 | 0.355607 | 0.359221 |
| PREPARED FOODS | 0 | 2623.000000 | 821.000000 | 0.005796 | 0.021703 | 0.450962 | 0.472665 |
| FROZEN FOODS | 0 | 1874.000000 | 619.000000 | 0.005278 | 0.072145 | 0.476331 | 0.548476 |
| HOME AND KITCHEN II | 1 | 594.000000 | 260.000000 | 0.003911 | 0.011607 | 0.412068 | 0.423675 |
| BEAUTY | 2-5 | 192.000000 | 154.000000 | 0.003718 | 0.003396 | 0.365906 | 0.369301 |
| LIQUOR,WINE,BEER | 1 | 212.000000 | 158.000000 | 0.003683 | 0.016439 | 0.460564 | 0.477003 |

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

- `lightgbm_shrinkage_es` has non-target family regressions. This is a plausible reason why public score can worsen even when mean validation improves.
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
