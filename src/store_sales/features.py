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
    family_demand: pd.DataFrame | None
    store_family_demand: pd.DataFrame | None


def build_feature_context(
    train_history: pd.DataFrame,
    data: CompetitionData,
    config: PipelineConfig,
) -> FeatureContext:
    use_demand_features = config.demand_features
    return FeatureContext(
        stores=data.stores.copy(),
        oil_features=prepare_oil_features(data.oil),
        national_holidays=prepare_holiday_features(data.holidays, locale="National"),
        regional_holidays=prepare_holiday_features(data.holidays, locale="Regional"),
        local_holidays=prepare_holiday_features(data.holidays, locale="Local"),
        weekday_transactions=prepare_transaction_features(train_history, data.transactions, by="weekday"),
        month_transactions=prepare_transaction_features(train_history, data.transactions, by="month"),
        family_demand=(
            prepare_static_demand_features(train_history, ["family"], prefix="family")
            if use_demand_features
            else None
        ),
        store_family_demand=(
            prepare_static_demand_features(
                train_history,
                ["store_nbr", "family"],
                prefix="store_family",
            )
            if use_demand_features
            else None
        ),
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


def _add_low_demand_flag(frame: pd.DataFrame, mean_column: str, zero_rate_column: str, flag_column: str) -> pd.DataFrame:
    enriched = frame.copy()
    if enriched.empty:
        enriched[flag_column] = pd.Series(dtype="int8")
        return enriched

    low_sales_cutoff = enriched[mean_column].quantile(0.25)
    high_zero_cutoff = max(0.5, float(enriched[zero_rate_column].quantile(0.75)))
    enriched[flag_column] = (
        (enriched[mean_column] <= low_sales_cutoff) | (enriched[zero_rate_column] >= high_zero_cutoff)
    ).astype("int8")
    return enriched


def prepare_static_demand_features(
    history: pd.DataFrame,
    group_columns: list[str],
    prefix: str,
) -> pd.DataFrame | None:
    if history.empty:
        return None

    stats = (
        history.groupby(group_columns, dropna=False)
        .agg(
            demand_sales_sum=("sales", "sum"),
            demand_row_count=("sales", "size"),
            demand_zero_count=("sales", lambda values: (values == 0).sum()),
        )
        .reset_index()
    )
    stats[f"{prefix}_mean_sales_hist"] = stats["demand_sales_sum"] / stats["demand_row_count"].clip(lower=1)
    stats[f"{prefix}_zero_rate_hist"] = stats["demand_zero_count"] / stats["demand_row_count"].clip(lower=1)
    stats = stats.rename(columns={"demand_row_count": f"{prefix}_row_count_hist"})
    stats = _add_low_demand_flag(
        stats,
        mean_column=f"{prefix}_mean_sales_hist",
        zero_rate_column=f"{prefix}_zero_rate_hist",
        flag_column=f"{prefix}_is_low_demand",
    )
    return stats[
        group_columns
        + [
            f"{prefix}_mean_sales_hist",
            f"{prefix}_zero_rate_hist",
            f"{prefix}_row_count_hist",
            f"{prefix}_is_low_demand",
        ]
    ]


def prepare_training_demand_features(
    history: pd.DataFrame,
    group_columns: list[str],
    prefix: str,
) -> pd.DataFrame:
    daily = (
        history.groupby(group_columns + ["date"], dropna=False)
        .agg(
            demand_sales_sum=("sales", "sum"),
            demand_row_count=("sales", "size"),
            demand_zero_count=("sales", lambda values: (values == 0).sum()),
        )
        .sort_values(group_columns + ["date"])
        .reset_index()
    )

    grouped = daily.groupby(group_columns, sort=False)
    daily["sales_sum_before"] = grouped["demand_sales_sum"].cumsum() - daily["demand_sales_sum"]
    daily["row_count_before"] = grouped["demand_row_count"].cumsum() - daily["demand_row_count"]
    daily["zero_count_before"] = grouped["demand_zero_count"].cumsum() - daily["demand_zero_count"]

    denominator = daily["row_count_before"].clip(lower=1)
    daily[f"{prefix}_mean_sales_hist"] = daily["sales_sum_before"] / denominator
    daily[f"{prefix}_zero_rate_hist"] = daily["zero_count_before"] / denominator
    daily[f"{prefix}_row_count_hist"] = daily["row_count_before"]

    daily = _add_low_demand_flag(
        daily,
        mean_column=f"{prefix}_mean_sales_hist",
        zero_rate_column=f"{prefix}_zero_rate_hist",
        flag_column=f"{prefix}_is_low_demand",
    )
    return daily[
        group_columns
        + [
            "date",
            f"{prefix}_mean_sales_hist",
            f"{prefix}_zero_rate_hist",
            f"{prefix}_row_count_hist",
            f"{prefix}_is_low_demand",
        ]
    ]


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
    if context.family_demand is not None:
        enriched = enriched.merge(context.family_demand, on=["family"], how="left")
    if context.store_family_demand is not None:
        enriched = enriched.merge(context.store_family_demand, on=["store_nbr", "family"], how="left")

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
        "family_mean_sales_hist",
        "family_zero_rate_hist",
        "family_row_count_hist",
        "family_is_low_demand",
        "store_family_mean_sales_hist",
        "store_family_zero_rate_hist",
        "store_family_row_count_hist",
        "store_family_is_low_demand",
    ]
    for column in numeric_fill_columns:
        if column in enriched.columns:
            enriched[column] = enriched[column].fillna(0.0)

    return enriched


def add_training_demand_features(train_frame: pd.DataFrame) -> pd.DataFrame:
    enriched = train_frame.copy()
    family_demand = prepare_training_demand_features(enriched, ["family"], prefix="family")
    enriched = enriched.merge(family_demand, on=["family", "date"], how="left")

    store_family_demand = prepare_training_demand_features(
        enriched,
        ["store_nbr", "family"],
        prefix="store_family",
    )
    enriched = enriched.merge(store_family_demand, on=["store_nbr", "family", "date"], how="left")
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
    if config.demand_features and include_sales_lags:
        features = features.drop(
            columns=[
                "family_mean_sales_hist",
                "family_zero_rate_hist",
                "family_row_count_hist",
                "family_is_low_demand",
                "store_family_mean_sales_hist",
                "store_family_zero_rate_hist",
                "store_family_row_count_hist",
                "store_family_is_low_demand",
            ],
            errors="ignore",
        )
        features = add_training_demand_features(features)
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
