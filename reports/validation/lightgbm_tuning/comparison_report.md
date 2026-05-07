# Model Comparison Report

Lower RMSLE is better. All rows use time-based recursive validation.

These results rank local validation experiments only. Kaggle public score can differ, so the best local row still needs submission verification.
If `validation_step_days` is smaller than `validation_horizon`, validation windows overlap and should be interpreted accordingly.

## Results

| experiment_name | model_type | feature_profile | validation_rmsle_mean | validation_rmsle_std | validation_rmsle_min | validation_rmsle_max | lightgbm_preset | early_stopping_rounds | early_stopping_validation_days | validation_window_dates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lightgbm_baseline | lightgbm | baseline | 0.486767 | 0.070236 | 0.400730 | 0.583115 | baseline |  | 0 | 2014-08-16:2014-08-31|2015-08-16:2015-08-31|2016-08-16:2016-08-31|2017-07-31:2017-08-15 |
| lightgbm_shrinkage_es | lightgbm | baseline | 0.499285 | 0.124943 | 0.403487 | 0.710339 | shrinkage | 100 | 16 | 2014-08-16:2014-08-31|2015-08-16:2015-08-31|2016-08-16:2016-08-31|2017-07-31:2017-08-15 |
| lightgbm_conservative_es | lightgbm | baseline | 0.507772 | 0.120996 | 0.414622 | 0.711345 | conservative | 100 | 16 | 2014-08-16:2014-08-31|2015-08-16:2015-08-31|2016-08-16:2016-08-31|2017-07-31:2017-08-15 |
| lightgbm_regularized_es | lightgbm | baseline | 0.519939 | 0.126331 | 0.406631 | 0.717537 | regularized | 100 | 16 | 2014-08-16:2014-08-31|2015-08-16:2015-08-31|2016-08-16:2016-08-31|2017-07-31:2017-08-15 |

## Experiment Notes

- `lightgbm_baseline`: Original LightGBM baseline on the fixed baseline feature profile. Output: `artifacts/validation/lightgbm_tuning/lightgbm_baseline`.
- `lightgbm_shrinkage_es`: LightGBM shrinkage preset with a lower learning rate and early stopping holdout. Output: `artifacts/validation/lightgbm_tuning/lightgbm_shrinkage_es`.
- `lightgbm_conservative_es`: LightGBM conservative preset with strong leaf-size and regularization constraints. Output: `artifacts/validation/lightgbm_tuning/lightgbm_conservative_es`.
- `lightgbm_regularized_es`: LightGBM regularized preset with smaller leaves, subsampling, L1/L2, and early stopping. Output: `artifacts/validation/lightgbm_tuning/lightgbm_regularized_es`.

## Available Feature Profiles

- `compact`: short lags/windows for quick smoke tests.
- `baseline`: main lag, rolling, promotion, holiday, oil, transaction, and store feature set.
- `extended`: adds longer seasonal lags for feature-engineering iteration.
- `low_demand`: baseline feature set plus family and store-family low-demand history features.
- `school_supplies_aug_promo`: baseline feature set plus targeted SCHOOL AND OFFICE SUPPLIES August, promotion, and store interactions.
