from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from store_sales.config import PipelineConfig
from store_sales.data import CompetitionData, load_competition_data
from store_sales.features import (
    KEY_COLUMNS,
    build_feature_context,
    build_feature_frame,
    build_history_matrix,
    compute_recursive_lag_features,
)
from store_sales.metrics import rmsle, write_metrics
from store_sales.modeling import ModelBundle, fit_model


@dataclass(slots=True)
class PipelineOutputs:
    validation_score: float
    validation_path: Path
    metrics_path: Path
    submission_path: Path | None
    validation_summary_path: Path
    validation_fold_scores: list[dict[str, object]]


@dataclass(slots=True)
class ValidationWindow:
    fold_id: int
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp


def filter_training_window(train: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    filtered = train.copy()
    if config.train_start_date is not None:
        filtered = filtered[filtered["date"] >= pd.Timestamp(config.train_start_date)].copy()
    if config.recent_history_start is not None:
        filtered = filtered[filtered["date"] >= pd.Timestamp(config.recent_history_start)].copy()
    return filtered.reset_index(drop=True)


def split_train_validation(train: pd.DataFrame, config: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    unique_dates = sorted(train["date"].unique())
    if len(unique_dates) <= config.validation_horizon:
        raise ValueError("Training data is shorter than the requested validation horizon.")

    validation_start = unique_dates[-config.validation_horizon]
    train_part = train[train["date"] < validation_start].copy()
    validation_part = train[train["date"] >= validation_start].copy()
    return train_part.reset_index(drop=True), validation_part.reset_index(drop=True)


def build_validation_windows(train: pd.DataFrame, config: PipelineConfig) -> list[ValidationWindow]:
    if config.validation_windows < 1:
        raise ValueError("validation_windows must be at least 1.")

    unique_dates = sorted(pd.Timestamp(date_value) for date_value in train["date"].unique())
    horizon = config.validation_horizon
    step_days = config.validation_step_days or horizon

    if horizon < 1:
        raise ValueError("validation_horizon must be at least 1.")
    if step_days < 1:
        raise ValueError("validation_step_days must be at least 1.")
    if len(unique_dates) <= horizon:
        raise ValueError("Training data is shorter than the requested validation horizon.")

    windows: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    end_exclusive = len(unique_dates)
    for _ in range(config.validation_windows):
        start_index = end_exclusive - horizon
        if start_index <= 0:
            raise ValueError(
                "Training data is too short for the requested number of validation windows. "
                "Reduce `validation_windows`, `validation_horizon`, or `validation_step_days`."
            )
        windows.append((unique_dates[start_index], unique_dates[end_exclusive - 1]))
        end_exclusive -= step_days

    windows.reverse()
    return [
        ValidationWindow(
            fold_id=index,
            validation_start=validation_start,
            validation_end=validation_end,
        )
        for index, (validation_start, validation_end) in enumerate(windows, start=1)
    ]


def split_train_validation_window(
    train: pd.DataFrame,
    window: ValidationWindow,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_part = train[train["date"] < window.validation_start].copy()
    validation_part = train[
        (train["date"] >= window.validation_start) & (train["date"] <= window.validation_end)
    ].copy()
    return train_part.reset_index(drop=True), validation_part.reset_index(drop=True)


def _prepare_promotion_history(history: pd.DataFrame, future: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat(
        [
            history[["date", "store_nbr", "family", "onpromotion"]],
            future[["date", "store_nbr", "family", "onpromotion"]],
        ],
        ignore_index=True,
    )
    return build_history_matrix(combined, "onpromotion")


def recursive_forecast(
    model_bundle: ModelBundle,
    history: pd.DataFrame,
    future: pd.DataFrame,
    data: CompetitionData,
    config: PipelineConfig,
) -> pd.DataFrame:
    context = build_feature_context(history, data, config)
    future_base = build_feature_frame(
        base_frame=future,
        context=context,
        config=config,
        include_sales_lags=False,
    )

    sales_history = build_history_matrix(history, "sales")
    promotion_history = _prepare_promotion_history(history, future)
    future_index = future[KEY_COLUMNS].drop_duplicates().set_index(KEY_COLUMNS).index
    full_index = sales_history.index.union(future_index)
    sales_history = sales_history.reindex(full_index)
    promotion_history = promotion_history.reindex(full_index).fillna(0.0)

    predictions = []
    for forecast_date in sorted(future_base["date"].unique()):
        rows_for_day = future_base[future_base["date"] == forecast_date].copy()
        lag_features = compute_recursive_lag_features(
            rows_for_day=rows_for_day,
            forecast_date=pd.Timestamp(forecast_date),
            sales_history=sales_history,
            promotion_history=promotion_history,
            config=config,
        )

        day_features = rows_for_day.merge(
            lag_features,
            on=["store_nbr", "family"],
            how="left",
        )
        for column in day_features.columns:
            if pd.api.types.is_numeric_dtype(day_features[column]):
                day_features[column] = day_features[column].fillna(0.0)
        day_predictions = model_bundle.predict(day_features)
        day_output = rows_for_day[["date", "store_nbr", "family"]].copy()
        if "id" in rows_for_day.columns:
            day_output["id"] = rows_for_day["id"].to_numpy()
        day_output["sales_pred"] = day_predictions
        predictions.append(day_output)

        day_series = day_output.set_index(["store_nbr", "family"])["sales_pred"].astype("float32")
        sales_history[pd.Timestamp(forecast_date)] = day_series.reindex(sales_history.index)

    return pd.concat(predictions, ignore_index=True)


def fit_training_pipeline(
    history: pd.DataFrame,
    data: CompetitionData,
    config: PipelineConfig,
) -> ModelBundle:
    context = build_feature_context(history, data, config)
    train_features = build_feature_frame(
        base_frame=history,
        context=context,
        config=config,
        include_sales_lags=True,
    )
    if train_features.empty:
        raise ValueError(
            "No training rows remain after feature generation. "
            "Use an earlier `--train-start-date` or reduce the lag settings."
        )
    return fit_model(train_features, config)


def run_pipeline(config: PipelineConfig) -> PipelineOutputs:
    config.output_dir.mkdir(parents=True, exist_ok=True)

    data = load_competition_data(config)
    train = filter_training_window(data.train, config)
    validation_path = config.output_dir / "validation_predictions.csv"
    validation_summary_path = config.output_dir / "validation_summary.csv"
    metrics_path = config.output_dir / "validation_metrics.json"
    validation_windows = build_validation_windows(train, config)
    fold_scores: list[dict[str, object]] = []

    for window in validation_windows:
        train_part, validation_part = split_train_validation_window(train, window)
        validation_model = fit_training_pipeline(train_part, data, config)
        validation_predictions = recursive_forecast(
            model_bundle=validation_model,
            history=train_part,
            future=validation_part,
            data=data,
            config=config,
        )

        validation_truth = validation_part[["date", "store_nbr", "family", "sales"]].copy()
        validation_scored = validation_truth.merge(
            validation_predictions,
            on=["date", "store_nbr", "family"],
            how="left",
        )
        fold_score = rmsle(
            validation_scored["sales"].to_numpy(),
            validation_scored["sales_pred"].fillna(0.0).to_numpy(),
        )
        fold_predictions_path = config.output_dir / f"validation_predictions_fold_{window.fold_id:02d}.csv"
        validation_scored.to_csv(fold_predictions_path, index=False)
        if window.fold_id == len(validation_windows):
            validation_scored.to_csv(validation_path, index=False)

        fold_scores.append(
            {
                "fold_id": window.fold_id,
                "validation_start": window.validation_start.date().isoformat(),
                "validation_end": window.validation_end.date().isoformat(),
                "validation_rmsle": fold_score,
                "train_rows": int(len(train_part)),
                "validation_rows": int(len(validation_part)),
                "predictions_path": str(fold_predictions_path),
            }
        )

    validation_summary = pd.DataFrame(fold_scores)
    validation_summary.to_csv(validation_summary_path, index=False)
    validation_score = float(validation_summary["validation_rmsle"].mean())
    validation_std = float(validation_summary["validation_rmsle"].std(ddof=0))
    latest_fold = fold_scores[-1]

    write_metrics(
        metrics_path,
        {
            "validation_rmsle": validation_score,
            "validation_rmsle_mean": validation_score,
            "validation_rmsle_std": validation_std,
            "validation_rmsle_min": float(validation_summary["validation_rmsle"].min()),
            "validation_rmsle_max": float(validation_summary["validation_rmsle"].max()),
            "validation_horizon_days": config.validation_horizon,
            "validation_windows": config.validation_windows,
            "validation_step_days": config.validation_step_days or config.validation_horizon,
            "model_type": config.model_type,
            "feature_profile": config.feature_profile,
            "train_rows": int(latest_fold["train_rows"]),
            "validation_rows": int(latest_fold["validation_rows"]),
            "folds": fold_scores,
        },
    )

    submission_path: Path | None = None
    if config.make_submission:
        final_model = fit_training_pipeline(train, data, config)
        submission_predictions = recursive_forecast(
            model_bundle=final_model,
            history=train,
            future=data.test,
            data=data,
            config=config,
        )

        submission_path = config.output_dir / "submission.csv"
        submission_predictions[["id", "sales_pred"]].rename(columns={"sales_pred": "sales"}).to_csv(
            submission_path,
            index=False,
        )

    return PipelineOutputs(
        validation_score=validation_score,
        validation_path=validation_path,
        metrics_path=metrics_path,
        submission_path=submission_path,
        validation_summary_path=validation_summary_path,
        validation_fold_scores=fold_scores,
    )
