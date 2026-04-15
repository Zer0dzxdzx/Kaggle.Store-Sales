from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from store_sales.config import PipelineConfig
from store_sales.data import CompetitionData

KEY_COLUMNS = ["store_nbr", "family"]


@dataclass(slots=True)
class FeatureContext:
    stores: pd.DataFrame
    oil_features: pd.DataFrame
    national_holidays: pd.DataFrame
    regional_holidays: pd.DataFrame
    local_holidays: pd.DataFrame
    weekday_transactions: pd.DataFrame | None
    month_transactions: pd.DataFrame | None


def build_feature_context(train_history: pd.DataFrame, data: CompetitionData) -> FeatureContext:
    return FeatureContext(
        stores=data.stores.copy(),
        oil_features=prepare_oil_features(data.oil),
        national_holidays=prepare_holiday_features(data.holidays, locale="National"),
        regional_holidays=prepare_holiday_features(data.holidays, locale="Regional"),
        local_holidays=prepare_holiday_features(data.holidays, locale="Local"),
        weekday_transactions=prepare_transaction_features(train_history, data.transactions, by="weekday"),
        month_transactions=prepare_transaction_features(train_history, data.transactions, by="month"),
    )


def prepare_oil_features(oil: pd.DataFrame) -> pd.DataFrame:
    oil_frame = oil.copy()
    oil_frame = oil_frame.set_index("date").asfreq("D")
    oil_frame["dcoilwtico"] = oil_frame["dcoilwtico"].interpolate().bfill().ffill()
    oil_frame["oil_change_7"] = oil_frame["dcoilwtico"] - oil_frame["dcoilwtico"].shift(7)
    oil_frame["oil_mean_7"] = oil_frame["dcoilwtico"].rolling(window=7, min_periods=1).mean()
    oil_frame["oil_mean_28"] = oil_frame["dcoilwtico"].rolling(window=28, min_periods=1).mean()
    oil_frame = oil_frame.rename(columns={"dcoilwtico": "oil_price"})
    return oil_frame.reset_index()


def prepare_holiday_features(holidays: pd.DataFrame, locale: str) -> pd.DataFrame:
    holiday_frame = holidays.copy()
    holiday_frame = holiday_frame.rename(columns={"type": "holiday_type"})
    holiday_frame = holiday_frame[holiday_frame["locale"] == locale].copy()

    if "transferred" in holiday_frame.columns:
        holiday_frame = holiday_frame[~holiday_frame["transferred"].fillna(False)].copy()

    holiday_frame["is_holiday"] = holiday_frame["holiday_type"].isin(
        ["Holiday", "Additional", "Bridge", "Transfer"]
    ).astype("int8")
    holiday_frame["is_event"] = (holiday_frame["holiday_type"] == "Event").astype("int8")
    holiday_frame["is_work_day"] = (holiday_frame["holiday_type"] == "Work Day").astype("int8")

    group_keys = ["date"]
    prefix = locale.lower()
    if locale in {"Regional", "Local"}:
        group_keys.append("locale_name")

    aggregated = (
        holiday_frame.groupby(group_keys, dropna=False)
        .agg(
            holiday_count=("description", "count"),
            holiday_is_holiday=("is_holiday", "max"),
            holiday_is_event=("is_event", "max"),
            holiday_is_work_day=("is_work_day", "max"),
        )
        .reset_index()
    )
    rename_map = {
        "holiday_count": f"{prefix}_holiday_count",
        "holiday_is_holiday": f"{prefix}_is_holiday",
        "holiday_is_event": f"{prefix}_is_event",
        "holiday_is_work_day": f"{prefix}_is_work_day",
    }
    return aggregated.rename(columns=rename_map)


def prepare_transaction_features(
    train_history: pd.DataFrame,
    transactions: pd.DataFrame | None,
    by: str,
) -> pd.DataFrame | None:
    if transactions is None:
        return None

    tx = transactions.copy()
    if not train_history.empty:
        tx = tx[tx["date"] <= train_history["date"].max()].copy()

    if by == "weekday":
        tx["day_of_week"] = tx["date"].dt.dayofweek.astype("int8")
        return (
            tx.groupby(["store_nbr", "day_of_week"], as_index=False)["transactions"]
            .mean()
            .rename(columns={"transactions": "transactions_weekday_mean"})
        )

    if by == "month":
        tx["month"] = tx["date"].dt.month.astype("int8")
        return (
            tx.groupby(["store_nbr", "month"], as_index=False)["transactions"]
            .mean()
            .rename(columns={"transactions": "transactions_month_mean"})
        )

    raise ValueError(f"Unsupported transaction aggregation: {by}")


def add_calendar_features(frame: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    enriched = frame.copy()
    enriched["day_of_week"] = enriched["date"].dt.dayofweek.astype("int8")
    enriched["day_of_month"] = enriched["date"].dt.day.astype("int8")
    enriched["day_of_year"] = enriched["date"].dt.dayofyear.astype("int16")
    enriched["week_of_year"] = enriched["date"].dt.isocalendar().week.astype("int16")
    enriched["month"] = enriched["date"].dt.month.astype("int8")
    enriched["year"] = enriched["date"].dt.year.astype("int16")
    enriched["quarter"] = enriched["date"].dt.quarter.astype("int8")
    enriched["is_weekend"] = (enriched["day_of_week"] >= 5).astype("int8")
    enriched["is_month_start"] = enriched["date"].dt.is_month_start.astype("int8")
    enriched["is_month_end"] = enriched["date"].dt.is_month_end.astype("int8")
    enriched["is_quarter_start"] = enriched["date"].dt.is_quarter_start.astype("int8")
    enriched["is_quarter_end"] = enriched["date"].dt.is_quarter_end.astype("int8")
    enriched["is_payday"] = (
        (enriched["day_of_month"] == 15) | enriched["date"].dt.is_month_end
    ).astype("int8")

    earthquake_date = pd.Timestamp(config.earthquake_date)
    days_since_earthquake = (enriched["date"] - earthquake_date).dt.days
    enriched["days_since_earthquake"] = days_since_earthquake.clip(lower=0, upper=365).astype("int16")
    enriched["earthquake_window_30"] = days_since_earthquake.between(0, 30).astype("int8")

    enriched["dow_sin"] = np.sin(2 * np.pi * enriched["day_of_week"] / 7.0)
    enriched["dow_cos"] = np.cos(2 * np.pi * enriched["day_of_week"] / 7.0)
    enriched["month_sin"] = np.sin(2 * np.pi * enriched["month"] / 12.0)
    enriched["month_cos"] = np.cos(2 * np.pi * enriched["month"] / 12.0)
    enriched["doy_sin"] = np.sin(2 * np.pi * enriched["day_of_year"] / 365.0)
    enriched["doy_cos"] = np.cos(2 * np.pi * enriched["day_of_year"] / 365.0)
    return enriched


def add_known_exogenous_features(frame: pd.DataFrame, context: FeatureContext) -> pd.DataFrame:
    enriched = frame.copy()
    enriched = enriched.merge(context.stores, on="store_nbr", how="left")
    enriched = enriched.merge(context.oil_features, on="date", how="left")
    enriched = enriched.merge(context.national_holidays, on="date", how="left")
    enriched = enriched.merge(
        context.regional_holidays,
        left_on=["date", "state"],
        right_on=["date", "locale_name"],
        how="left",
    ).drop(columns=["locale_name"], errors="ignore")
    enriched = enriched.merge(
        context.local_holidays,
        left_on=["date", "city"],
        right_on=["date", "locale_name"],
        how="left",
    ).drop(columns=["locale_name"], errors="ignore")

    if context.weekday_transactions is not None:
        enriched = enriched.merge(context.weekday_transactions, on=["store_nbr", "day_of_week"], how="left")
    if context.month_transactions is not None:
        enriched = enriched.merge(context.month_transactions, on=["store_nbr", "month"], how="left")

    holiday_columns = [
        column
        for column in enriched.columns
        if column.endswith("_holiday_count")
        or column.endswith("_is_holiday")
        or column.endswith("_is_event")
        or column.endswith("_is_work_day")
    ]
    for column in holiday_columns:
        enriched[column] = enriched[column].fillna(0)

    numeric_fill_columns = [
        "oil_price",
        "oil_change_7",
        "oil_mean_7",
        "oil_mean_28",
        "transactions_weekday_mean",
        "transactions_month_mean",
    ]
    for column in numeric_fill_columns:
        if column in enriched.columns:
            enriched[column] = enriched[column].fillna(0.0)

    return enriched


def add_training_lag_features(
    train_frame: pd.DataFrame,
    config: PipelineConfig,
) -> pd.DataFrame:
    enriched = train_frame.sort_values(["store_nbr", "family", "date"]).copy()
    sales_group = enriched.groupby(KEY_COLUMNS, sort=False)["sales"]
    promo_group = enriched.groupby(KEY_COLUMNS, sort=False)["onpromotion"]

    for lag in config.sales_lags:
        enriched[f"sales_lag_{lag}"] = sales_group.shift(lag)
    for window in config.sales_windows:
        enriched[f"sales_roll_mean_{window}"] = sales_group.transform(
            lambda series: series.shift(1).rolling(window=window, min_periods=1).mean()
        )
        enriched[f"sales_roll_std_{window}"] = sales_group.transform(
            lambda series: series.shift(1).rolling(window=window, min_periods=1).std()
        )

    for lag in config.promo_lags:
        enriched[f"promo_lag_{lag}"] = promo_group.shift(lag)
    for window in config.promo_windows:
        enriched[f"promo_roll_sum_{window}"] = promo_group.transform(
            lambda series: series.shift(1).rolling(window=window, min_periods=1).sum()
        )

    max_sales_lag = max(config.sales_lags)
    enriched = enriched[enriched[f"sales_lag_{max_sales_lag}"].notna()].copy()
    return enriched


def build_feature_frame(
    base_frame: pd.DataFrame,
    context: FeatureContext,
    config: PipelineConfig,
    include_sales_lags: bool,
) -> pd.DataFrame:
    features = add_calendar_features(base_frame, config)
    features = add_known_exogenous_features(features, context)
    if include_sales_lags:
        features = add_training_lag_features(features, config)

    for column in features.columns:
        if pd.api.types.is_numeric_dtype(features[column]):
            features[column] = features[column].fillna(0.0)
    return features


def build_history_matrix(history: pd.DataFrame, value_column: str) -> pd.DataFrame:
    matrix = history.pivot(index=KEY_COLUMNS, columns="date", values=value_column)
    matrix = matrix.sort_index().sort_index(axis=1)
    matrix.columns = pd.to_datetime(matrix.columns)
    return matrix.astype("float32")


def compute_recursive_lag_features(
    rows_for_day: pd.DataFrame,
    forecast_date: pd.Timestamp,
    sales_history: pd.DataFrame,
    promotion_history: pd.DataFrame,
    config: PipelineConfig,
) -> pd.DataFrame:
    features = rows_for_day[KEY_COLUMNS].drop_duplicates().set_index(KEY_COLUMNS).copy()
    group_index = features.index

    for lag in config.sales_lags:
        lag_date = forecast_date - pd.Timedelta(days=lag)
        if lag_date in sales_history.columns:
            lag_values = sales_history[lag_date].reindex(group_index).fillna(0.0)
        else:
            lag_values = pd.Series(0.0, index=group_index, dtype="float32")
        features[f"sales_lag_{lag}"] = lag_values.to_numpy()

    for window in config.sales_windows:
        window_dates = pd.date_range(end=forecast_date - pd.Timedelta(days=1), periods=window, freq="D")
        window_values = sales_history.reindex(columns=window_dates).reindex(group_index)
        features[f"sales_roll_mean_{window}"] = window_values.mean(axis=1).fillna(0.0).to_numpy()
        features[f"sales_roll_std_{window}"] = window_values.std(axis=1).fillna(0.0).to_numpy()

    for lag in config.promo_lags:
        lag_date = forecast_date - pd.Timedelta(days=lag)
        if lag_date in promotion_history.columns:
            lag_values = promotion_history[lag_date].reindex(group_index).fillna(0.0)
        else:
            lag_values = pd.Series(0.0, index=group_index, dtype="float32")
        features[f"promo_lag_{lag}"] = lag_values.to_numpy()

    for window in config.promo_windows:
        window_dates = pd.date_range(end=forecast_date - pd.Timedelta(days=1), periods=window, freq="D")
        window_values = promotion_history.reindex(columns=window_dates).reindex(group_index)
        features[f"promo_roll_sum_{window}"] = window_values.sum(axis=1).to_numpy()

    return features.reset_index()
