from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PipelineConfig:
    data_dir: Path
    output_dir: Path
    train_start_date: str | None = "2015-01-01"
    validation_horizon: int = 16
    validation_windows: int = 1
    validation_step_days: int | None = None
    model_type: str = "hist_gbdt"
    feature_profile: str = "baseline"
    demand_features: bool = False
    school_supplies_features: bool = False
    random_state: int = 42
    sales_lags: tuple[int, ...] = (1, 7, 14, 28)
    sales_windows: tuple[int, ...] = (7, 14, 28, 56)
    promo_lags: tuple[int, ...] = (1, 7, 14)
    promo_windows: tuple[int, ...] = (7, 14)
    categorical_columns: tuple[str, ...] = (
        "family",
        "city",
        "state",
        "store_type",
    )
    drop_columns: tuple[str, ...] = ("date", "id", "sales")
    required_files: tuple[str, ...] = (
        "train.csv",
        "test.csv",
        "stores.csv",
        "oil.csv",
        "holidays_events.csv",
    )
    optional_files: tuple[str, ...] = (
        "transactions.csv",
        "items.csv",
    )
    earthquake_date: str = "2016-04-16"
    recent_history_start: str | None = None
    make_submission: bool = True
    model_params: dict[str, object] = field(default_factory=dict)
