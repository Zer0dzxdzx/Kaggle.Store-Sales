from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from store_sales.config import PipelineConfig
from store_sales.data import CompetitionData
from store_sales.pipeline import recursive_forecast


class LagPlusTenModel:
    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return frame["sales_lag_1"].to_numpy(dtype=float) + 10.0


def _data() -> CompetitionData:
    return CompetitionData(
        train=pd.DataFrame(),
        test=pd.DataFrame(),
        stores=pd.DataFrame(
            {
                "store_nbr": [1],
                "city": ["Quito"],
                "state": ["Pichincha"],
                "store_type": ["A"],
                "cluster": [1],
            }
        ),
        oil=pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=4, freq="D"),
                "dcoilwtico": [50.0, 51.0, 52.0, 53.0],
            }
        ),
        holidays=pd.DataFrame(
            {
                "date": pd.to_datetime([]),
                "type": pd.Series(dtype="string"),
                "locale": pd.Series(dtype="string"),
                "locale_name": pd.Series(dtype="string"),
                "description": pd.Series(dtype="string"),
                "transferred": pd.Series(dtype="boolean"),
            }
        ),
    )


def _config() -> PipelineConfig:
    return PipelineConfig(
        data_dir=Path("unused"),
        output_dir=Path("unused"),
        sales_lags=(1,),
        sales_windows=(1,),
        promo_lags=(1,),
        promo_windows=(1,),
    )


def test_recursive_forecast_writes_predictions_back_into_sales_history() -> None:
    history = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
            "store_nbr": [1, 1],
            "family": ["GROCERY I", "GROCERY I"],
            "sales": [90.0, 100.0],
            "onpromotion": [0, 0],
        }
    )
    future = pd.DataFrame(
        {
            "id": [1, 2],
            "date": pd.to_datetime(["2020-01-03", "2020-01-04"]),
            "store_nbr": [1, 1],
            "family": ["GROCERY I", "GROCERY I"],
            "onpromotion": [0, 0],
        }
    )

    predictions = recursive_forecast(
        model_bundle=LagPlusTenModel(),
        history=history,
        future=future,
        data=_data(),
        config=_config(),
    )

    assert predictions["id"].tolist() == [1, 2]
    assert predictions["sales_pred"].tolist() == [110.0, 120.0]
