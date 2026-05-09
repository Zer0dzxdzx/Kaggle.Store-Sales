# Store Sales Project Summary

## Project Positioning

Kaggle Store Sales is a store-family level time series forecasting project. The project goal is not a one-off notebook result, but a reproducible machine learning workflow covering raw data validation, feature engineering, time-based validation, model comparison, submission generation, and experiment logging.

For the current single source of truth on scores, champion model, failed experiments, and residual risks, see [final_result_summary.md](final_result_summary.md).

## Current Deliverables

| Deliverable | Status | Evidence |
| --- | --- | --- |
| Runnable project repository | Done | Modular package under `src/store_sales/` with CLI entry points. |
| Kaggle submission | Done | HistGBDT baseline public score `0.58410`; LightGBM submission improved public score to `0.50834`. |
| Iterative feature-engineering pipeline | Done | `compact`, `baseline`, and `extended` feature profiles are available. |
| At least two model comparison results | Done | HistGBDT, LightGBM, ridge, seasonal naive, and simple blending have been compared with time-based validation. |
| Resume/interview project summary | Done | This document summarizes scope, methods, results, and next improvement direction. |

## Methods

- Data integration: `train`, `test`, `stores`, `oil`, `holidays_events`, and optional `transactions`.
- Validation: rolling time-based validation with recursive multi-day forecasting.
- Features: date/calendar signals, payday/month-end flags, oil price interpolation, locale-aware holiday features, store metadata, transaction aggregates, promotion lags, sales lags, and rolling sales statistics.
- Models: seasonal lag benchmark, ridge regression baseline, scikit-learn HistGradientBoosting tree model, and optional LightGBM backend.
- Tracking: validation fold summaries, experiment log CSV, model comparison report, and EDA report.

## Current Results

| Experiment | Model | Feature Profile | Validation Scheme | Validation RMSLE Mean | Validation RMSLE Std |
| --- | --- | --- | --- | ---: | ---: |
| `histgbdt_baseline` | HistGradientBoostingRegressor | `baseline` | Early 3-window validation | `0.401601` | `0.017124` |
| `seasonal_naive` | Weekly lag median benchmark | `baseline` | Early 3-window validation | `0.458129` | `0.053525` |
| `ridge_baseline` | Ridge regression | `baseline` | Early 3-window validation | `2.734132` | `0.016583` |
| `lightgbm_baseline` | LightGBM | `baseline` | August / pre-test validation | `0.486767` | `0.070236` |

The early 3-window results and August / pre-test results use different validation schemes, so they should not be directly compared as the same metric. The initial tree-model baseline improved early multi-window mean RMSLE by about 12.3% over the seasonal lag benchmark. Ridge is much worse under the current ordinal-encoded feature setup, so it is useful as a negative control rather than a competitive candidate. The current best Kaggle public score is `0.50834` from the LightGBM baseline, improving over the original HistGBDT baseline score `0.58410`. The next optimization should focus on reducing validation-public mismatch and improving fold/slice stability rather than only chasing a single public score.

## Resume Version

Kaggle: Store Sales Time Series Forecasting | Machine Learning / Time Series Analysis

- Built a reproducible forecasting pipeline for store-family retail sales, covering multi-table data integration, feature engineering, time-based validation, and Kaggle submission generation.
- Engineered calendar, holiday, promotion, oil-price, store metadata, lag, and rolling-window features; used EDA to analyze sales patterns, zero-sales behavior, and validation instability.
- Compared seasonal lag, ridge, HistGBDT, LightGBM, and blending candidates with time-based validation; improved Kaggle public score from `0.58410` to `0.50834` while using fold and slice stability checks to monitor and diagnose overfitting risk.

## Next Evidence to Add

- Add an interview talk-track document that separates 30-second, 60-second, and deep-dive answers.
- Add CI so lightweight pytest sanity checks run automatically on future changes.
- Continue improving residual fold/family/promotion stability before claiming a more mature forecasting system.
