# Stability Slice Report: `histgbdt_school_supplies_aug_promo` vs `histgbdt_baseline`

本报告用于解释 public-like 稳定性风险：一个 profile 即使 mean validation 更好，也可能在某些非目标切片或 test-like 分布上更差。

## Overall Windows

| fold_id | validation_start | validation_end | validation_rmsle_baseline | validation_rmsle_experiment | rmsle_delta |
| --- | --- | --- | --- | --- | --- |
| 1 | 2014-08-16 | 2014-08-31 | 0.394681 | 0.390796 | -0.003885 |
| 2 | 2015-08-16 | 2015-08-31 | 0.479351 | 0.475061 | -0.004289 |
| 3 | 2016-08-16 | 2016-08-31 | 0.656282 | 0.655352 | -0.000930 |
| 4 | 2017-07-31 | 2017-08-15 | 0.431742 | 0.424491 | -0.007251 |

- Mean RMSLE delta: `-0.004089`.

## Target vs Non-Target

| target_group | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales | mean_predicted_sales_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non_target_family | 110592 | 0.493954 | 0.493476 | -0.000478 | 391.875773 | 372.652839 | 372.837665 | 0.184826 |
| target_family | 3456 | 0.681330 | 0.599242 | -0.082087 | 22.151042 | 7.748145 | 17.061944 | 9.313799 |

## Non-Target Family Side Effects

- Non-target families worsened: `16`.
- Non-target families improved: `16`.

Top worsened non-target families:

| family | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_actual_sales | baseline_mean_predicted_sales | experiment_mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DELI | 3456 | 0.388225 | 0.395593 | 0.007368 | 276.775384 | 269.621002 | 270.481086 |
| MAGAZINES | 3456 | 0.493388 | 0.497972 | 0.004584 | 3.734375 | 2.809734 | 2.824950 |
| CLEANING | 3456 | 0.450690 | 0.453756 | 0.003067 | 1074.590856 | 1049.422121 | 1055.587246 |
| BEVERAGES | 3456 | 0.495000 | 0.497000 | 0.002000 | 2628.432002 | 2521.201552 | 2518.736366 |
| PET SUPPLIES | 3456 | 0.485206 | 0.487148 | 0.001941 | 4.966435 | 4.387411 | 4.367261 |
| BEAUTY | 3456 | 0.499939 | 0.501735 | 0.001796 | 4.563368 | 3.694179 | 3.662735 |
| SEAFOOD | 3456 | 0.504996 | 0.506547 | 0.001551 | 21.671714 | 19.436353 | 19.422601 |
| GROCERY II | 3456 | 0.636994 | 0.638453 | 0.001459 | 22.179688 | 20.550951 | 20.463974 |
| BABY CARE | 3456 | 0.331980 | 0.333359 | 0.001378 | 0.143519 | 0.336842 | 0.345713 |
| PREPARED FOODS | 3456 | 0.411788 | 0.413085 | 0.001298 | 94.480681 | 88.205088 | 87.737799 |

## Promotion Bin Stability

| promotion_bin | baseline_row_count | baseline_rmsle | experiment_rmsle | rmsle_delta | baseline_mean_onpromotion | experiment_mean_onpromotion |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 80820 | 0.549915 | 0.550287 | 0.000372 | 0.000000 | 0.000000 |
| 51+ | 1512 | 0.223664 | 0.222336 | -0.001328 | 86.517196 | 86.517196 |
| 1 | 8815 | 0.366693 | 0.361109 | -0.005584 | 1.000000 | 1.000000 |
| 2-5 | 9170 | 0.349739 | 0.337212 | -0.012527 | 3.079935 | 3.079935 |
| 6-10 | 6345 | 0.347289 | 0.322182 | -0.025107 | 7.675177 | 7.675177 |

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
| PERSONAL CARE | 11-50 | 244.000000 | 473.000000 | 0.014450 | 0.003838 | 0.232833 | 0.236671 |
| DAIRY | 11-50 | 771.000000 | 511.000000 | 0.011162 | 0.005029 | 0.210637 | 0.215666 |
| BREAD/BAKERY | 11-50 | 332.000000 | 367.000000 | 0.009961 | 0.007607 | 0.208758 | 0.216364 |
| HOME AND KITCHEN II | 2-5 | 249.000000 | 344.000000 | 0.009882 | 0.001708 | 0.531307 | 0.533014 |
| LIQUOR,WINE,BEER | 2-5 | 630.000000 | 431.000000 | 0.009592 | 0.000477 | 0.455993 | 0.456470 |
| EGGS | 1 | 791.000000 | 398.000000 | 0.007023 | 0.000669 | 0.368295 | 0.368965 |
| PREPARED FOODS | 0 | 2623.000000 | 821.000000 | 0.005796 | 0.002977 | 0.436618 | 0.439595 |
| FROZEN FOODS | 0 | 1874.000000 | 619.000000 | 0.005278 | 0.002206 | 0.507626 | 0.509832 |
| LIQUOR,WINE,BEER | 6-10 | 122.000000 | 155.000000 | 0.004367 | 0.013826 | 0.372980 | 0.386806 |
| HOME AND KITCHEN II | 1 | 594.000000 | 260.000000 | 0.003911 | 0.000897 | 0.483378 | 0.484275 |

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

- `school_supplies_aug_promo` has non-target family regressions. This is a plausible reason why public score can worsen even when mean validation improves.
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
