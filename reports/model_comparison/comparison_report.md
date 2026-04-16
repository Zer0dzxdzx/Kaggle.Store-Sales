# Model Comparison Report

Lower RMSLE is better. All rows use time-based recursive validation.

These results rank local validation experiments only. Kaggle public score can differ, so the best local row still needs submission verification.
If `validation_step_days` is smaller than `validation_horizon`, validation windows overlap and should be interpreted accordingly.

## Results

| experiment_name | model_type | feature_profile | validation_rmsle_mean | validation_rmsle_std | validation_rmsle_min | validation_rmsle_max |
| --- | --- | --- | --- | --- | --- | --- |
| histgbdt_baseline | hist_gbdt | baseline | 0.401601 | 0.017124 | 0.381085 | 0.423002 |
| seasonal_naive | seasonal_naive | baseline | 0.458129 | 0.053525 | 0.412476 | 0.533245 |
| ridge_baseline | ridge | baseline | 2.734132 | 0.016583 | 2.712561 | 2.752886 |

## Experiment Notes

- `histgbdt_baseline`: Main tree-model baseline with lag, rolling, promotion, holiday, oil, and store features. Output: `artifacts/experiments/histgbdt_baseline`.
- `seasonal_naive`: Median of recent weekly sales lags; acts as a time-series benchmark. Output: `artifacts/experiments/seasonal_naive`.
- `ridge_baseline`: Regularized linear model on the baseline feature set. Output: `artifacts/experiments/ridge_baseline`.

## Available Feature Profiles

- `compact`: short lags/windows for quick smoke tests.
- `baseline`: main lag, rolling, promotion, holiday, oil, transaction, and store feature set.
- `extended`: adds longer seasonal lags for feature-engineering iteration.
