from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from store_sales.config import PipelineConfig


@dataclass(slots=True)
class CompetitionData:
    train: pd.DataFrame
    test: pd.DataFrame
    stores: pd.DataFrame
    oil: pd.DataFrame
    holidays: pd.DataFrame
    transactions: pd.DataFrame | None = None
    items: pd.DataFrame | None = None


def _read_csv(path: Path, **kwargs: object) -> pd.DataFrame:
    frame = pd.read_csv(path, **kwargs)
    if "date" in frame.columns:
        frame["date"] = pd.to_datetime(frame["date"])
    return frame


def _load_optional_csv(path: Path, **kwargs: object) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return _read_csv(path, **kwargs)


def validate_data_dir(config: PipelineConfig) -> None:
    missing = [name for name in config.required_files if not (config.data_dir / name).exists()]
    if missing:
        expected = ", ".join(config.required_files)
        missing_text = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing required files in {config.data_dir}: {missing_text}. "
            f"Expected at least: {expected}."
        )


def load_competition_data(config: PipelineConfig) -> CompetitionData:
    validate_data_dir(config)

    train = _read_csv(
        config.data_dir / "train.csv",
        dtype={
            "id": "int64",
            "store_nbr": "int16",
            "family": "string",
            "sales": "float32",
            "onpromotion": "int16",
        },
    )
    test = _read_csv(
        config.data_dir / "test.csv",
        dtype={
            "id": "int64",
            "store_nbr": "int16",
            "family": "string",
            "onpromotion": "int16",
        },
    )
    stores = _read_csv(
        config.data_dir / "stores.csv",
        dtype={
            "store_nbr": "int16",
            "city": "string",
            "state": "string",
            "type": "string",
            "cluster": "int16",
        },
    ).rename(columns={"type": "store_type"})
    oil = _read_csv(
        config.data_dir / "oil.csv",
        dtype={"dcoilwtico": "float32"},
    )
    holidays = _read_csv(
        config.data_dir / "holidays_events.csv",
        dtype={
            "type": "string",
            "locale": "string",
            "locale_name": "string",
            "description": "string",
            "transferred": "boolean",
        },
    )
    transactions = _load_optional_csv(
        config.data_dir / "transactions.csv",
        dtype={
            "store_nbr": "int16",
            "transactions": "float32",
        },
    )
    items = _load_optional_csv(
        config.data_dir / "items.csv",
        dtype={
            "item_nbr": "int32",
            "family": "string",
            "class": "int32",
            "perishable": "int8",
        },
    )

    train = train.sort_values(["date", "store_nbr", "family"]).reset_index(drop=True)
    test = test.sort_values(["date", "store_nbr", "family"]).reset_index(drop=True)
    stores = stores.sort_values("store_nbr").reset_index(drop=True)
    oil = oil.sort_values("date").reset_index(drop=True)
    holidays = holidays.sort_values("date").reset_index(drop=True)

    train["sales"] = train["sales"].clip(lower=0.0)
    train["onpromotion"] = train["onpromotion"].fillna(0).astype("int16")
    test["onpromotion"] = test["onpromotion"].fillna(0).astype("int16")

    if transactions is not None:
        transactions = transactions.sort_values(["date", "store_nbr"]).reset_index(drop=True)

    return CompetitionData(
        train=train,
        test=test,
        stores=stores,
        oil=oil,
        holidays=holidays,
        transactions=transactions,
        items=items,
    )
