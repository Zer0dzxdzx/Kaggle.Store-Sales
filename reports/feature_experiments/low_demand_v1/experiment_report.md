# Low Demand Feature Experiment v1

## Experiment Goal

Test whether leakage-safe family and store-family low-demand history features improve the baseline model.

The hypothesis came from stage 4 error analysis: several high-error families were low-sales or high-zero-sales categories, so explicit historical demand profile features might help the model separate low-demand groups from normal groups.

## Setup

| Item | Value |
| --- | --- |
| Experiment name | `histgbdt_low_demand_v1` |
| Model | `hist_gbdt` |
| Feature profile | `low_demand` |
| Baseline comparison | `histgbdt_baseline` |
| Validation scheme | 3 non-overlapping time windows, 16 days each |
| Submission generated | No |

New feature groups:

- `family_mean_sales_hist`
- `family_zero_rate_hist`
- `family_row_count_hist`
- `family_is_low_demand`
- `store_family_mean_sales_hist`
- `store_family_zero_rate_hist`
- `store_family_row_count_hist`
- `store_family_is_low_demand`

Training rows use only dates before the current row's date for these statistics. Validation and test rows use only the corresponding training window history.

## Validation Result

| Metric | Baseline | Low demand v1 | Delta |
| --- | ---: | ---: | ---: |
| Mean RMSLE | 0.401601 | 0.403019 | +0.001417 |
| Fold 1 RMSLE | 0.381085 | 0.379982 | -0.001103 |
| Fold 2 RMSLE | 0.400716 | 0.402185 | +0.001469 |
| Fold 3 RMSLE | 0.423002 | 0.426889 | +0.003886 |

Lower RMSLE is better. This experiment improves fold 1 slightly, but hurts fold 2 and fold 3. Because fold 3 is closest to the Kaggle test period, the result is not acceptable as a default feature set.

## Family Error Check

| Family | Baseline RMSLE | Low demand RMSLE | Delta | Interpretation |
| --- | ---: | ---: | ---: | --- |
| SCHOOL AND OFFICE SUPPLIES | 0.671040 | 0.712021 | +0.040981 | Major regression; prediction mean dropped from 7.04 to 6.19 while actual mean is 22.79 |
| LINGERIE | 0.624578 | 0.621184 | -0.003393 | Small improvement |
| GROCERY II | 0.621563 | 0.615957 | -0.005606 | Small improvement |
| CELEBRATION | 0.565454 | 0.561999 | -0.003455 | Small improvement |
| HARDWARE | 0.529902 | 0.530040 | +0.000137 | Essentially unchanged |

The feature helps some low-sales families slightly, but it badly worsens the worst baseline family. That means the low-demand signal is too coarse or is pushing some seasonal/irregular demand categories too low.

## Decision

Do not promote `low_demand` as the default feature profile.

Reason:

- Mean RMSLE is worse than baseline.
- Fold 3 is worse than baseline.
- The worst family error becomes worse, not better.
- The original hypothesis was only partially supported.

## Next Action

Keep the implementation available for reference, but do not use it as the main submission feature set.

The next experiment should be narrower. Instead of broad family/store-family low-demand features, focus on one of these:

1. A specific fix for `SCHOOL AND OFFICE SUPPLIES`.
2. A fold 3 cross-error analysis before adding more features.
3. Promotion/family interaction only after confirming which family-promotion groups fail.

