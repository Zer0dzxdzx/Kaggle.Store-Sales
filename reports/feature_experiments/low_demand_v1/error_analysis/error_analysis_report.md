# Store Sales Error Analysis

This report uses validation fold predictions only. It is for local diagnosis, not Kaggle leaderboard scoring.
Family, store, and promotion-bin errors are pooled across all validation folds unless stated otherwise.

## Key Findings

- Worst family by RMSLE: `SCHOOL AND OFFICE SUPPLIES` with RMSLE `0.712021`.
- Worst store by RMSLE: store `19` with RMSLE `0.486059`.
- Worst promotion bin by RMSLE: `0` with RMSLE `0.450734`.
- Fold comparison is fold-level only; it shows trend by validation window, not segment-level causes.

## Inputs

- Data directory: `data/raw`
- Artifacts directory: `artifacts/experiments/histgbdt_low_demand_v1`
- Prediction files: `artifacts/experiments/histgbdt_low_demand_v1/validation_predictions_fold_01.csv, artifacts/experiments/histgbdt_low_demand_v1/validation_predictions_fold_02.csv, artifacts/experiments/histgbdt_low_demand_v1/validation_predictions_fold_03.csv`

## Family Error

| family | row_count | rmsle | actual_zero_rate | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- |
| SCHOOL AND OFFICE SUPPLIES | 2592 | 0.712021 | 0.551312 | 22.792824 | 6.188797 |
| LINGERIE | 2592 | 0.621184 | 0.100694 | 6.959105 | 5.684375 |
| GROCERY II | 2592 | 0.615957 | 0.016204 | 32.392747 | 28.581518 |
| CELEBRATION | 2592 | 0.561999 | 0.021219 | 13.373843 | 11.710291 |
| HARDWARE | 2592 | 0.530040 | 0.384259 | 1.481481 | 1.101003 |
| MAGAZINES | 2592 | 0.522599 | 0.155478 | 6.474537 | 5.560732 |
| LADIESWEAR | 2592 | 0.511103 | 0.292824 | 11.266204 | 10.981277 |
| AUTOMOTIVE | 2592 | 0.503569 | 0.032407 | 7.285108 | 6.238848 |
| LIQUOR,WINE,BEER | 2592 | 0.491545 | 0.000772 | 97.365741 | 90.472135 |
| SEAFOOD | 2592 | 0.473227 | 0.084491 | 20.549882 | 19.082341 |

## Store Error

| store_nbr | city | state | store_type | cluster | row_count | rmsle | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19 | Guaranda | Bolivar | C | 15 | 1584 | 0.486059 | 284.544595 | 278.897281 |
| 26 | Guayaquil | Guayas | D | 10 | 1584 | 0.465150 | 152.435699 | 152.671595 |
| 14 | Riobamba | Chimborazo | C | 7 | 1584 | 0.460773 | 250.403280 | 244.609208 |
| 22 | Puyo | Pastaza | C | 7 | 1584 | 0.460464 | 219.654736 | 208.262417 |
| 32 | Guayaquil | Guayas | C | 3 | 1584 | 0.455087 | 153.747769 | 130.108673 |
| 50 | Ambato | Tungurahua | A | 14 | 1584 | 0.453040 | 655.958859 | 675.002219 |
| 47 | Quito | Pichincha | A | 14 | 1584 | 0.443754 | 1156.226764 | 1163.112745 |
| 30 | Guayaquil | Guayas | C | 3 | 1584 | 0.443452 | 202.236705 | 191.900692 |
| 10 | Quito | Pichincha | C | 15 | 1584 | 0.439312 | 200.736710 | 189.338063 |
| 36 | Libertad | Guayas | E | 10 | 1584 | 0.438352 | 366.358669 | 339.195798 |

## Promotion Bin Error

| promotion_bin | row_count | rmsle | mean_actual_sales | mean_predicted_sales | mean_onpromotion |
| --- | --- | --- | --- | --- | --- |
| 0 | 48752 | 0.450734 | 57.814675 | 56.400740 | 0.000000 |
| 1 | 6777 | 0.417861 | 92.143089 | 90.178630 | 1.000000 |
| 2-5 | 7801 | 0.367168 | 230.279561 | 234.665474 | 3.269965 |
| 6-10 | 7012 | 0.267050 | 719.066165 | 778.932113 | 7.794210 |
| 11-50 | 12382 | 0.314086 | 1573.738688 | 1592.182179 | 23.461073 |
| 51+ | 2812 | 0.150228 | 3951.036789 | 3880.074123 | 79.523471 |

## Fold Comparison

| fold_id | validation_start | validation_end | row_count | rmsle | rmsle_delta_vs_previous_fold | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2017-06-29 | 2017-07-14 | 28512 | 0.379982 |  | 484.802112 | 482.282287 |
| 2 | 2017-07-15 | 2017-07-30 | 28512 | 0.402185 | 0.022203 | 481.763042 | 466.911453 |
| 3 | 2017-07-31 | 2017-08-15 | 28512 | 0.426889 | 0.024704 | 467.142950 | 498.563518 |

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
