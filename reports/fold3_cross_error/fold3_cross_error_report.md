# Fold 3 Cross Error Analysis

This report compares fold 3 against the pooled prior folds, using validation predictions only.
It ranks segments by positive MSLE delta contribution, so it focuses on groups that became worse in fold 3.

## Inputs

- Data directory: `data/raw`
- Artifacts directory: `artifacts`
- Target fold: `3`
- Minimum target-fold rows per reported segment: `4`

## Key Findings

- Fold 3 RMSLE is `0.423002` versus prior folds RMSLE `0.391024`.
- Largest family worsening contributor: `SCHOOL AND OFFICE SUPPLIES`.
- Largest store worsening contributor: store `47`.
- Largest promotion-bin worsening contributor: `11-50`.
- Largest family-store worsening combination: `SCHOOL AND OFFICE SUPPLIES` at store `47`.
- Largest family-promotion worsening combination: `LADIESWEAR` with promotion bin `0`.
- Largest new fold-3 family-store-promotion segment: `SCHOOL AND OFFICE SUPPLIES` at store `47` with promotion bin `11-50`.

## Fold Trend

| fold_id | row_count | rmsle | rmsle_delta_vs_prior_folds | mean_actual_sales | mean_predicted_sales |
| --- | --- | --- | --- | --- | --- |
| 1 | 28512 | 0.381085 | -0.009939 | 484.802112 | 483.467551 |
| 2 | 28512 | 0.400716 | 0.009693 | 481.763042 | 466.880720 |
| 3 | 28512 | 0.423002 | 0.031979 | 467.142950 | 494.452252 |

## Family Worsening

| family | fold3_rmsle | prior_rmsle | rmsle_delta | positive_msle_delta_contribution | fold3_mean_actual_sales | fold3_mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- |
| SCHOOL AND OFFICE SUPPLIES | 0.866511 | 0.547742 | 0.318769 | 0.013661 | 59.947917 | 18.501496 |
| HOME AND KITCHEN I | 0.494428 | 0.429142 | 0.065287 | 0.001827 | 31.273148 | 26.104428 |
| GROCERY II | 0.651992 | 0.605776 | 0.046216 | 0.001761 | 28.971065 | 33.240971 |
| LADIESWEAR | 0.537645 | 0.484806 | 0.052839 | 0.001637 | 10.082176 | 11.295860 |
| MAGAZINES | 0.548257 | 0.514843 | 0.033414 | 0.001076 | 7.113426 | 5.627806 |
| LAWN AND GARDEN | 0.438937 | 0.399589 | 0.039348 | 0.001000 | 14.939815 | 15.432014 |
| HOME AND KITCHEN II | 0.466147 | 0.434465 | 0.031682 | 0.000865 | 31.005787 | 29.329196 |
| HOME CARE | 0.259335 | 0.197999 | 0.061336 | 0.000850 | 291.542824 | 337.912141 |
| SEAFOOD | 0.494269 | 0.466500 | 0.027769 | 0.000808 | 19.977916 | 18.718790 |
| BEVERAGES | 0.240204 | 0.197715 | 0.042489 | 0.000564 | 3478.480324 | 3718.480654 |

## Store Worsening

| store_nbr | city | state | store_type | cluster | fold3_rmsle | prior_rmsle | rmsle_delta | positive_msle_delta_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 47 | Quito | Pichincha | A | 14 | 0.580428 | 0.325134 | 0.255294 | 0.004281 |
| 44 | Quito | Pichincha | A | 5 | 0.567815 | 0.319395 | 0.248421 | 0.004082 |
| 50 | Ambato | Tungurahua | A | 14 | 0.544224 | 0.350715 | 0.193509 | 0.003207 |
| 48 | Quito | Pichincha | A | 14 | 0.539596 | 0.348483 | 0.191113 | 0.003143 |
| 19 | Guaranda | Bolivar | C | 15 | 0.559079 | 0.451457 | 0.107622 | 0.002014 |
| 38 | Loja | Loja | D | 4 | 0.439754 | 0.346787 | 0.092967 | 0.001354 |
| 9 | Quito | Pichincha | B | 6 | 0.448407 | 0.370071 | 0.078336 | 0.001187 |
| 14 | Riobamba | Chimborazo | C | 7 | 0.505277 | 0.438465 | 0.066812 | 0.001168 |
| 20 | Quito | Pichincha | B | 6 | 0.462153 | 0.394808 | 0.067345 | 0.001069 |
| 25 | Salinas | Santa Elena | D | 1 | 0.480621 | 0.419254 | 0.061367 | 0.001023 |

## Promotion Bin Worsening

| promotion_bin | fold3_rmsle | prior_rmsle | rmsle_delta | positive_msle_delta_contribution | fold3_row_share |
| --- | --- | --- | --- | --- | --- |
| 11-50 | 0.418344 | 0.232653 | 0.185691 | 0.014759 | 0.122089 |
| 0 | 0.461326 | 0.447315 | 0.014011 | 0.007158 | 0.562254 |
| 6-10 | 0.281783 | 0.235802 | 0.045982 | 0.002729 | 0.114653 |
| 2-5 | 0.386309 | 0.357312 | 0.028997 | 0.002015 | 0.093434 |
| 51+ | 0.159258 | 0.146328 | 0.012930 | 0.000094 | 0.023885 |
| 1 | 0.412670 | 0.421571 | -0.008901 | 0.000000 | 0.083684 |

## Family Store Worsening

| family | store_nbr | city | store_type | fold3_row_count | fold3_rmsle | prior_rmsle | rmsle_delta | positive_msle_delta_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SCHOOL AND OFFICE SUPPLIES | 47 | Quito | A | 16 | 2.735861 | 0.721499 | 2.014362 | 0.003908 |
| SCHOOL AND OFFICE SUPPLIES | 44 | Quito | A | 16 | 2.665396 | 0.591897 | 2.073498 | 0.003790 |
| SCHOOL AND OFFICE SUPPLIES | 48 | Quito | A | 16 | 2.388825 | 0.487357 | 1.901467 | 0.003069 |
| SCHOOL AND OFFICE SUPPLIES | 50 | Ambato | A | 16 | 2.185463 | 0.609607 | 1.575855 | 0.002472 |
| GROCERY II | 19 | Guaranda | C | 16 | 2.015033 | 1.122442 | 0.892591 | 0.001572 |
| SCHOOL AND OFFICE SUPPLIES | 9 | Quito | B | 16 | 1.502361 | 0.679495 | 0.822865 | 0.001008 |
| GROCERY II | 14 | Riobamba | C | 16 | 1.465741 | 0.775170 | 0.690570 | 0.000868 |
| SCHOOL AND OFFICE SUPPLIES | 38 | Loja | D | 16 | 1.244050 | 0.182788 | 1.061263 | 0.000850 |
| LADIESWEAR | 20 | Quito | B | 16 | 1.148416 | 0.640639 | 0.507777 | 0.000510 |
| SCHOOL AND OFFICE SUPPLIES | 20 | Quito | B | 16 | 1.046808 | 0.497943 | 0.548866 | 0.000476 |

## Family Promotion Worsening

| family | promotion_bin | fold3_row_count | fold3_rmsle | prior_rmsle | rmsle_delta | positive_msle_delta_contribution |
| --- | --- | --- | --- | --- | --- | --- |
| LADIESWEAR | 0 | 770 | 0.525324 | 0.484974 | 0.040350 | 0.001101 |
| LAWN AND GARDEN | 0 | 770 | 0.448469 | 0.401236 | 0.047232 | 0.001084 |
| MAGAZINES | 0 | 864 | 0.548257 | 0.515282 | 0.032975 | 0.001063 |
| HOME AND KITCHEN II | 2-5 | 223 | 0.524384 | 0.379656 | 0.144728 | 0.001023 |
| SEAFOOD | 0 | 762 | 0.506708 | 0.473181 | 0.033528 | 0.000878 |
| GROCERY II | 0 | 762 | 0.655224 | 0.632338 | 0.022886 | 0.000788 |
| LIQUOR,WINE,BEER | 0 | 65 | 0.876379 | 0.704003 | 0.172376 | 0.000621 |
| LINGERIE | 0 | 683 | 0.641933 | 0.622399 | 0.019534 | 0.000592 |
| FROZEN FOODS | 1 | 513 | 0.284390 | 0.221985 | 0.062405 | 0.000569 |
| LIQUOR,WINE,BEER | 2-5 | 539 | 0.459009 | 0.433728 | 0.025282 | 0.000427 |

## Store Promotion Worsening

| store_nbr | city | store_type | promotion_bin | fold3_row_count | fold3_rmsle | prior_rmsle | rmsle_delta | positive_msle_delta_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 47 | Quito | A | 11-50 | 92 | 1.115809 | 0.131261 | 0.984548 | 0.003962 |
| 44 | Quito | A | 11-50 | 103 | 1.047183 | 0.141843 | 0.905341 | 0.003889 |
| 48 | Quito | A | 11-50 | 89 | 0.992808 | 0.149061 | 0.843746 | 0.003007 |
| 50 | Ambato | A | 11-50 | 87 | 0.956222 | 0.122213 | 0.834009 | 0.002744 |
| 19 | Guaranda | C | 0 | 311 | 0.665197 | 0.520107 | 0.145090 | 0.001876 |
| 9 | Quito | B | 6-10 | 80 | 0.664634 | 0.254446 | 0.410188 | 0.001058 |
| 38 | Loja | D | 0 | 302 | 0.477687 | 0.364356 | 0.113331 | 0.001011 |
| 14 | Riobamba | C | 0 | 313 | 0.568898 | 0.500052 | 0.068846 | 0.000808 |
| 25 | Salinas | D | 0 | 315 | 0.542698 | 0.476380 | 0.066318 | 0.000747 |
| 26 | Guayaquil | D | 0 | 337 | 0.538580 | 0.480378 | 0.058202 | 0.000701 |

## Family Store Promotion Worsening

| family | store_nbr | city | promotion_bin | fold3_row_count | fold3_rmsle | prior_rmsle | rmsle_delta | positive_msle_delta_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GROCERY II | 19 | Guaranda | 0 | 15 | 1.921667 | 1.194742 | 0.726925 | 0.001192 |
| SCHOOL AND OFFICE SUPPLIES | 38 | Loja | 0 | 16 | 1.244050 | 0.182788 | 1.061263 | 0.000850 |
| GROCERY II | 26 | Guayaquil | 0 | 13 | 1.359765 | 0.281907 | 1.077858 | 0.000807 |
| SCHOOL AND OFFICE SUPPLIES | 9 | Quito | 6-10 | 15 | 1.501075 | 0.893248 | 0.607827 | 0.000766 |
| GROCERY II | 14 | Riobamba | 0 | 14 | 1.442875 | 0.806870 | 0.636005 | 0.000703 |
| LIQUOR,WINE,BEER | 32 | Guayaquil | 0 | 6 | 1.945881 | 1.066519 | 0.879362 | 0.000557 |
| LADIESWEAR | 20 | Quito | 0 | 16 | 1.148416 | 0.640639 | 0.507777 | 0.000510 |
| HOME AND KITCHEN I | 36 | Libertad | 1 | 6 | 1.348927 | 0.456061 | 0.892865 | 0.000339 |
| HOME AND KITCHEN II | 38 | Loja | 2-5 | 12 | 0.994152 | 0.478112 | 0.516040 | 0.000320 |
| HOME AND KITCHEN II | 23 | Ambato | 2-5 | 7 | 1.157230 | 0.325696 | 0.831534 | 0.000303 |

## New Fold 3 Family Promotion Segments

These segments appear in fold 3 but not in prior folds for the same exact grouping, so they are ranked by fold 3 error share rather than prior delta.

| family | promotion_bin | fold3_row_count | fold3_rmsle | fold3_error_share | fold3_mean_actual_sales | fold3_mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- |
| LADIESWEAR | 2-5 | 49 | 0.721255 | 0.004996 | 15.469388 | 28.944425 |
| LADIESWEAR | 6-10 | 35 | 0.411082 | 0.001159 | 32.742857 | 44.379080 |
| CLEANING | 2-5 | 14 | 0.409516 | 0.000460 | 280.500000 | 378.376341 |
| BEVERAGES | 2-5 | 20 | 0.295888 | 0.000343 | 1479.100000 | 1872.194294 |
| DAIRY | 1 | 5 | 0.128482 | 0.000016 | 683.800000 | 647.866956 |
| LADIESWEAR | 11-50 | 5 | 0.101981 | 0.000010 | 43.800000 | 44.971070 |

## New Fold 3 Store Promotion Segments

These segments appear in fold 3 but not in prior folds for the same exact grouping.

| store_nbr | city | store_type | promotion_bin | fold3_row_count | fold3_rmsle | fold3_error_share | fold3_mean_actual_sales | fold3_mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## New Fold 3 Family Store Promotion Segments

These fine-grained segments are noisy but useful for spotting fold 3 distribution changes.

| family | store_nbr | city | promotion_bin | fold3_row_count | fold3_rmsle | fold3_error_share | fold3_mean_actual_sales | fold3_mean_predicted_sales |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SCHOOL AND OFFICE SUPPLIES | 47 | Quito | 11-50 | 15 | 2.733045 | 0.021962 | 538.400000 | 33.601619 |
| SCHOOL AND OFFICE SUPPLIES | 44 | Quito | 11-50 | 15 | 2.697563 | 0.021395 | 414.200000 | 26.982084 |
| SCHOOL AND OFFICE SUPPLIES | 48 | Quito | 11-50 | 13 | 2.561915 | 0.016725 | 464.846154 | 35.381392 |
| SCHOOL AND OFFICE SUPPLIES | 50 | Ambato | 11-50 | 15 | 2.254764 | 0.014948 | 416.000000 | 48.574898 |
| SCHOOL AND OFFICE SUPPLIES | 20 | Quito | 6-10 | 9 | 1.243681 | 0.002729 | 84.333333 | 23.288004 |
| LINGERIE | 44 | Quito | 6-10 | 9 | 1.139109 | 0.002289 | 64.555556 | 20.359246 |
| GROCERY II | 50 | Ambato | 0 | 13 | 0.828408 | 0.001749 | 70.846154 | 157.278106 |
| LADIESWEAR | 50 | Ambato | 2-5 | 8 | 0.851138 | 0.001136 | 12.500000 | 27.647809 |
| LADIESWEAR | 45 | Quito | 2-5 | 5 | 1.021468 | 0.001023 | 14.400000 | 33.468637 |
| HOME AND KITCHEN I | 46 | Quito | 0 | 13 | 0.616857 | 0.000970 | 55.076923 | 33.356494 |

## Generated Tables

- `tables/fold_trend.csv`
- `tables/fold3_family_worsening.csv`
- `tables/fold3_store_worsening.csv`
- `tables/fold3_promotion_bin_worsening.csv`
- `tables/fold3_family_store_worsening.csv`
- `tables/fold3_family_promotion_worsening.csv`
- `tables/fold3_store_promotion_worsening.csv`
- `tables/fold3_family_store_promotion_worsening.csv`
- `tables/fold3_new_family_promotion_segments.csv`
- `tables/fold3_new_store_promotion_segments.csv`
- `tables/fold3_new_family_store_promotion_segments.csv`

## Interpretation Limits

- This is diagnostic, not causal proof.
- Small combinations can be noisy even after the minimum row filter.
- RMSLE is not additive, so contribution ranking uses MSLE delta as an approximate decomposition.
- New fold 3 segments have no exact prior comparison and should be treated as distribution-shift clues.
