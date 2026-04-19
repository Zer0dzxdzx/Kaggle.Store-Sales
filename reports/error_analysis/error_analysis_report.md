# Store Sales Error Analysis

This report uses validation fold predictions only. It is for local diagnosis, not Kaggle leaderboard scoring.
Family, store, and promotion-bin errors are pooled across all validation folds unless stated otherwise.

## Key Findings

- Worst family by RMSLE: `SCHOOL AND OFFICE SUPPLIES` with RMSLE `0.671040`.
- Worst store by RMSLE: store `19` with RMSLE `0.489965`.
- Worst promotion bin by RMSLE: `0` with RMSLE `0.451970`.
- Fold comparison is fold-level only; it shows trend by validation window, not segment-level causes.

## Inputs

- Data directory: `data/raw`
- Artifacts directory: `artifacts`
- Prediction files: `artifacts/validation_predictions_fold_01.csv, artifacts/validation_predictions_fold_02.csv, artifacts/validation_predictions_fold_03.csv`

## Family Error

| family | row_count | rmsle | actual_zero_rate | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- |
| SCHOOL AND OFFICE SUPPLIES | 2592 | 0.671040 | 0.551312 | 22.792824 | 7.036063 |
| LINGERIE | 2592 | 0.624578 | 0.100694 | 6.959105 | 5.585274 |
| GROCERY II | 2592 | 0.621563 | 0.016204 | 32.392747 | 29.517127 |
| CELEBRATION | 2592 | 0.565454 | 0.021219 | 13.373843 | 11.473560 |
| HARDWARE | 2592 | 0.529902 | 0.384259 | 1.481481 | 1.125498 |
| MAGAZINES | 2592 | 0.526217 | 0.155478 | 6.474537 | 5.420559 |
| AUTOMOTIVE | 2592 | 0.505166 | 0.032407 | 7.285108 | 6.148242 |
| LADIESWEAR | 2592 | 0.503036 | 0.292824 | 11.266204 | 10.750995 |
| LIQUOR,WINE,BEER | 2592 | 0.494712 | 0.000772 | 97.365741 | 91.350860 |
| SEAFOOD | 2592 | 0.475937 | 0.084491 | 20.549882 | 18.772669 |

## Store Error

| store_nbr | city | state | store_type | cluster | row_count | rmsle | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19 | Guaranda | Bolivar | C | 15 | 1584 | 0.489965 | 284.544595 | 277.666059 |
| 26 | Guayaquil | Guayas | D | 10 | 1584 | 0.469451 | 152.435699 | 151.173631 |
| 22 | Puyo | Pastaza | C | 7 | 1584 | 0.461829 | 219.654736 | 205.203808 |
| 14 | Riobamba | Chimborazo | C | 7 | 1584 | 0.461811 | 250.403280 | 241.525305 |
| 32 | Guayaquil | Guayas | C | 3 | 1584 | 0.450065 | 153.747769 | 128.703314 |
| 30 | Guayaquil | Guayas | C | 3 | 1584 | 0.443649 | 202.236705 | 189.198936 |
| 25 | Salinas | Santa Elena | D | 1 | 1584 | 0.440660 | 257.164970 | 218.752409 |
| 10 | Quito | Pichincha | C | 15 | 1584 | 0.440461 | 200.736710 | 188.290441 |
| 36 | Libertad | Guayas | E | 10 | 1584 | 0.439910 | 366.358669 | 337.456987 |
| 35 | Playas | Guayas | C | 3 | 1584 | 0.434085 | 163.967742 | 154.950242 |

## Promotion Bin Error

| promotion_bin | row_count | rmsle | mean_actual_sales | mean_predicted_sales | mean_onpromotion |
| --- | --- | --- | --- | --- | --- |
| 0 | 48752 | 0.451970 | 57.814675 | 56.069185 | 0.000000 |
| 1 | 6777 | 0.418458 | 92.143089 | 89.583175 | 1.000000 |
| 2-5 | 7801 | 0.367472 | 230.279561 | 233.740426 | 3.269965 |
| 6-10 | 7012 | 0.258259 | 719.066165 | 779.113441 | 7.794210 |
| 11-50 | 12382 | 0.296837 | 1573.738688 | 1591.090277 | 23.461073 |
| 51+ | 2812 | 0.149562 | 3951.036789 | 3864.199891 | 79.523471 |

## Fold Comparison

| fold_id | validation_start | validation_end | row_count | rmsle | rmsle_delta_vs_previous_fold | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2017-06-29 | 2017-07-14 | 28512 | 0.381085 |  | 484.802112 | 483.467551 |
| 2 | 2017-07-15 | 2017-07-30 | 28512 | 0.400716 | 0.019631 | 481.763042 | 466.880720 |
| 3 | 2017-07-31 | 2017-08-15 | 28512 | 0.423002 | 0.022286 | 467.142950 | 494.452252 |

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
