from __future__ import annotations

from pathlib import Path

import pandas as pd

from store_sales.config import PipelineConfig
from store_sales.features import add_training_lag_features, build_history_matrix, compute_recursive_lag_features


def _config() -> PipelineConfig:
    return PipelineConfig(
        data_dir=Path("unused"),
        output_dir=Path("unused"),
        sales_lags=(1, 2),
        sales_windows=(2,),
        promo_lags=(1,),
        promo_windows=(2,),
    )


def test_training_lag_features_use_only_prior_sales() -> None:
    train = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=4, freq="D"),
            "store_nbr": [1, 1, 1, 1],
            "family": ["GROCERY I"] * 4,
            "sales": [10.0, 20.0, 30.0, 40.0],
            "onpromotion": [0, 1, 2, 3],
        }
    )

    features = add_training_lag_features(train, _config())
    row_for_jan_3 = features.loc[features["date"] == pd.Timestamp("2020-01-03")].iloc[0]

    assert row_for_jan_3["sales_lag_1"] == 20.0
    assert row_for_jan_3["sales_lag_2"] == 10.0
    assert row_for_jan_3["sales_roll_mean_2"] == 15.0
    assert row_for_jan_3["promo_lag_1"] == 1
    assert row_for_jan_3["promo_roll_sum_2"] == 1.0


def test_recursive_lag_features_do_not_use_forecast_date_sales() -> None:
    history_with_forecast_date = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
            "store_nbr": [1, 1, 1],
            "family": ["GROCERY I", "GROCERY I", "GROCERY I"],
            "sales": [10.0, 20.0, 999.0],
            "onpromotion": [1, 2, 9],
        }
    )
    rows_for_day = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-03")],
            "store_nbr": [1],
            "family": ["GROCERY I"],
        }
    )

    lag_features = compute_recursive_lag_features(
        rows_for_day=rows_for_day,
        forecast_date=pd.Timestamp("2020-01-03"),
        sales_history=build_history_matrix(history_with_forecast_date, "sales"),
        promotion_history=build_history_matrix(history_with_forecast_date, "onpromotion"),
        config=_config(),
    )
    row = lag_features.iloc[0]

    assert row["sales_lag_1"] == 20.0
    assert row["sales_lag_2"] == 10.0
    assert row["sales_roll_mean_2"] == 15.0
    assert row["promo_lag_1"] == 2
    assert row["promo_roll_sum_2"] == 3.0
    lag_columns = ["sales_lag_1", "sales_lag_2", "sales_roll_mean_2", "promo_lag_1", "promo_roll_sum_2"]
    assert 999.0 not in row[lag_columns].to_numpy()
