# Store Sales Error Analysis

This report uses validation fold predictions only. It is for local diagnosis, not Kaggle leaderboard scoring.
Family, store, and promotion-bin errors are pooled across all validation folds unless stated otherwise.

## Key Findings

- Worst family by RMSLE: `LINGERIE` with RMSLE `0.624478`.
- Worst store by RMSLE: store `19` with RMSLE `0.491158`.
- Worst promotion bin by RMSLE: `0` with RMSLE `0.451749`.
- Fold comparison is fold-level only; it shows trend by validation window, not segment-level causes.

## Inputs

- Data directory: `data/raw`
- Artifacts directory: `artifacts/experiments/histgbdt_school_supplies_aug_promo_v1`
- Prediction files: `artifacts/experiments/histgbdt_school_supplies_aug_promo_v1/validation_predictions_fold_01.csv, artifacts/experiments/histgbdt_school_supplies_aug_promo_v1/validation_predictions_fold_02.csv, artifacts/experiments/histgbdt_school_supplies_aug_promo_v1/validation_predictions_fold_03.csv`

## Family Error

| family | row_count | rmsle | actual_zero_rate | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- |
| LINGERIE | 2592 | 0.624478 | 0.100694 | 6.959105 | 5.597509 |
| GROCERY II | 2592 | 0.621956 | 0.016204 | 32.392747 | 29.466743 |
| SCHOOL AND OFFICE SUPPLIES | 2592 | 0.592639 | 0.551312 | 22.792824 | 11.412872 |
| CELEBRATION | 2592 | 0.565740 | 0.021219 | 13.373843 | 11.539967 |
| HARDWARE | 2592 | 0.529935 | 0.384259 | 1.481481 | 1.121289 |
| MAGAZINES | 2592 | 0.527038 | 0.155478 | 6.474537 | 5.415297 |
| AUTOMOTIVE | 2592 | 0.505543 | 0.032407 | 7.285108 | 6.149795 |
| LADIESWEAR | 2592 | 0.502331 | 0.292824 | 11.266204 | 10.720301 |
| LIQUOR,WINE,BEER | 2592 | 0.497560 | 0.000772 | 97.365741 | 90.194905 |
| SEAFOOD | 2592 | 0.475707 | 0.084491 | 20.549882 | 18.929465 |

## Store Error

| store_nbr | city | state | store_type | cluster | row_count | rmsle | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19 | Guaranda | Bolivar | C | 15 | 1584 | 0.491158 | 284.544595 | 277.743642 |
| 26 | Guayaquil | Guayas | D | 10 | 1584 | 0.469581 | 152.435699 | 151.279856 |
| 22 | Puyo | Pastaza | C | 7 | 1584 | 0.461990 | 219.654736 | 205.396674 |
| 14 | Riobamba | Chimborazo | C | 7 | 1584 | 0.461310 | 250.403280 | 242.341523 |
| 32 | Guayaquil | Guayas | C | 3 | 1584 | 0.450542 | 153.747769 | 128.481835 |
| 30 | Guayaquil | Guayas | C | 3 | 1584 | 0.443101 | 202.236705 | 188.814220 |
| 10 | Quito | Pichincha | C | 15 | 1584 | 0.440840 | 200.736710 | 188.188597 |
| 36 | Libertad | Guayas | E | 10 | 1584 | 0.440376 | 366.358669 | 337.684241 |
| 25 | Salinas | Santa Elena | D | 1 | 1584 | 0.438153 | 257.164970 | 219.833086 |
| 35 | Playas | Guayas | C | 3 | 1584 | 0.434691 | 163.967742 | 154.404874 |

## Promotion Bin Error

| promotion_bin | row_count | rmsle | mean_actual_sales | mean_predicted_sales | mean_onpromotion |
| --- | --- | --- | --- | --- | --- |
| 0 | 48752 | 0.451749 | 57.814675 | 55.956068 | 0.000000 |
| 1 | 6777 | 0.419067 | 92.143089 | 89.607880 | 1.000000 |
| 2-5 | 7801 | 0.369702 | 230.279561 | 233.290824 | 3.269965 |
| 6-10 | 7012 | 0.251878 | 719.066165 | 777.128130 | 7.794210 |
| 11-50 | 12382 | 0.263918 | 1573.738688 | 1587.061811 | 23.461073 |
| 51+ | 2812 | 0.149671 | 3951.036789 | 3858.397941 | 79.523471 |

## Fold Comparison

| fold_id | validation_start | validation_end | row_count | rmsle | rmsle_delta_vs_previous_fold | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2017-06-29 | 2017-07-14 | 28512 | 0.381600 |  | 484.802112 | 482.299437 |
| 2 | 2017-07-15 | 2017-07-30 | 28512 | 0.400273 | 0.018674 | 481.763042 | 465.914278 |
| 3 | 2017-07-31 | 2017-08-15 | 28512 | 0.412684 | 0.012411 | 467.142950 | 493.466327 |

## Generated Tables

- `tables/family_error.csv`
- `tables/store_error.csv`
- `tables/promotion_bin_error.csv`
- `tables/fold_comparison.csv`

## Questions To Answer

1. Are the worst family errors concentrated in high zero-sales families?
2. Are store errors concentrated in a specific city, state, store type, or cluster?
3. Does high promotion intensity have higher RMSLE than low promotion bins?
4. Does fold 3 have worse fold-level RMSLE than fold 1/2?
