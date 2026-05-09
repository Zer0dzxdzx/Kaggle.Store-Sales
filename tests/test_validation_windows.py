from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from store_sales.config import PipelineConfig
from store_sales.pipeline import build_validation_windows


def _config(**overrides: object) -> PipelineConfig:
    values = {
        "data_dir": Path("unused"),
        "output_dir": Path("unused"),
        "validation_horizon": 2,
        "validation_windows": 3,
        "validation_step_days": 2,
    }
    values.update(overrides)
    return PipelineConfig(**values)


def _train_dates(start: str, periods: int) -> pd.DataFrame:
    return pd.DataFrame({"date": pd.date_range(start, periods=periods, freq="D")})


def test_rolling_validation_windows_follow_time_order() -> None:
    train = _train_dates("2020-01-01", periods=10)

    windows = build_validation_windows(train, _config())

    assert [(window.validation_start.date().isoformat(), window.validation_end.date().isoformat()) for window in windows] == [
        ("2020-01-05", "2020-01-06"),
        ("2020-01-07", "2020-01-08"),
        ("2020-01-09", "2020-01-10"),
    ]
    assert [window.fold_id for window in windows] == [1, 2, 3]


def test_explicit_validation_windows_are_sorted_and_numbered() -> None:
    train = _train_dates("2020-01-01", periods=10)
    config = _config(
        validation_window_dates=(
            ("2020-01-07", "2020-01-08"),
            ("2020-01-03", "2020-01-04"),
        ),
    )

    windows = build_validation_windows(train, config)

    assert [(window.validation_start.date().isoformat(), window.validation_end.date().isoformat()) for window in windows] == [
        ("2020-01-03", "2020-01-04"),
        ("2020-01-07", "2020-01-08"),
    ]
    assert [window.fold_id for window in windows] == [1, 2]


def test_explicit_validation_windows_reject_overlaps() -> None:
    train = _train_dates("2020-01-01", periods=10)
    config = _config(
        validation_window_dates=(
            ("2020-01-03", "2020-01-04"),
            ("2020-01-04", "2020-01-05"),
        ),
    )

    with pytest.raises(ValueError, match="overlaps"):
        build_validation_windows(train, config)


def test_explicit_validation_windows_reject_wrong_horizon() -> None:
    train = _train_dates("2020-01-01", periods=10)
    config = _config(validation_window_dates=(("2020-01-03", "2020-01-05"),))

    with pytest.raises(ValueError, match="validation_horizon"):
        build_validation_windows(train, config)
