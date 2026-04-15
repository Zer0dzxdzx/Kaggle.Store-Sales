from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from store_sales.config import PipelineConfig


class ModelingError(RuntimeError):
    """Raised when a requested model backend cannot be used."""


@dataclass(slots=True)
class OrdinalEncoder:
    mappings: dict[str, dict[str, int]] = field(default_factory=dict)

    def fit(self, frame: pd.DataFrame, columns: list[str]) -> "OrdinalEncoder":
        self.mappings = {}
        for column in columns:
            values = frame[column].fillna("__missing__").astype("string")
            categories = sorted(values.unique().tolist())
            self.mappings[column] = {value: index for index, value in enumerate(categories)}
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        transformed = frame.copy()
        for column, mapping in self.mappings.items():
            values = transformed[column].fillna("__missing__").astype("string")
            transformed[column] = values.map(mapping).fillna(-1).astype("int32")
        return transformed


@dataclass(slots=True)
class ModelBundle:
    model: object
    encoder: OrdinalEncoder
    feature_columns: list[str]
    model_type: str

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        transformed = self.encoder.transform(frame[self.feature_columns])
        predictions = self.model.predict(transformed)
        predictions = np.expm1(predictions)
        return np.clip(predictions, 0.0, None)


def select_feature_columns(frame: pd.DataFrame, config: PipelineConfig) -> list[str]:
    return [column for column in frame.columns if column not in config.drop_columns]


def build_sample_weights(dates: pd.Series) -> np.ndarray:
    date_values = pd.to_datetime(dates)
    min_date = date_values.min()
    max_date = date_values.max()
    if min_date == max_date:
        return np.ones(len(date_values), dtype=float)

    span = (max_date - min_date).days
    scaled = (date_values - min_date).dt.days / max(span, 1)
    return 1.0 + scaled.to_numpy(dtype=float)


def fit_model(train_frame: pd.DataFrame, config: PipelineConfig) -> ModelBundle:
    feature_columns = select_feature_columns(train_frame, config)
    encoder = OrdinalEncoder().fit(train_frame, list(config.categorical_columns))
    X_train = encoder.transform(train_frame[feature_columns])
    y_train = np.log1p(train_frame["sales"].to_numpy(dtype=float))
    sample_weight = build_sample_weights(train_frame["date"])

    if config.model_type == "hist_gbdt":
        params = {
            "learning_rate": 0.05,
            "max_depth": 12,
            "max_iter": 350,
            "min_samples_leaf": 40,
            "l2_regularization": 0.1,
            "early_stopping": False,
            "random_state": config.random_state,
        }
        params.update(config.model_params)
        model = HistGradientBoostingRegressor(**params)
        model.fit(X_train, y_train, sample_weight=sample_weight)
        return ModelBundle(
            model=model,
            encoder=encoder,
            feature_columns=feature_columns,
            model_type=config.model_type,
        )

    if config.model_type == "lightgbm":
        try:
            from lightgbm import LGBMRegressor
        except ImportError as exc:
            raise ModelingError(
                "LightGBM is not installed. Install with `pip install -e .[lightgbm]` "
                "or use `--model-type hist_gbdt`."
            ) from exc

        params = {
            "objective": "regression",
            "n_estimators": 1200,
            "learning_rate": 0.03,
            "num_leaves": 255,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": config.random_state,
        }
        params.update(config.model_params)
        model = LGBMRegressor(**params)
        model.fit(X_train, y_train, sample_weight=sample_weight)
        return ModelBundle(
            model=model,
            encoder=encoder,
            feature_columns=feature_columns,
            model_type=config.model_type,
        )

    raise ModelingError(f"Unsupported model type: {config.model_type}")
