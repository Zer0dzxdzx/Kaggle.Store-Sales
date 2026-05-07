from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from store_sales.config import PipelineConfig
from store_sales.lightgbm_params import build_lightgbm_params

MIN_LOG1P_PREDICTION = -20.0
MAX_LOG1P_PREDICTION = 20.0


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
    training_metadata: dict[str, object] = field(default_factory=dict)

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        # All model backends are trained to predict log1p(sales); convert back once here.
        transformed = self.encoder.transform(frame[self.feature_columns])
        predictions = self.model.predict(transformed)
        predictions = np.nan_to_num(
            predictions,
            nan=0.0,
            posinf=MAX_LOG1P_PREDICTION,
            neginf=MIN_LOG1P_PREDICTION,
        )
        predictions = np.clip(predictions, MIN_LOG1P_PREDICTION, MAX_LOG1P_PREDICTION)
        predictions = np.expm1(predictions)
        return np.clip(predictions, 0.0, None)


@dataclass(slots=True)
class SeasonalNaiveRegressor:
    lag_columns: tuple[str, ...] = ("sales_lag_7", "sales_lag_14", "sales_lag_28", "sales_lag_1")

    def fit(self, X: pd.DataFrame, y: np.ndarray, sample_weight: np.ndarray | None = None) -> "SeasonalNaiveRegressor":
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        available_lags = [column for column in self.lag_columns if column in X.columns]
        if not available_lags:
            return np.zeros(len(X), dtype=float)

        candidates = X[available_lags]
        raw_predictions = candidates.median(axis=1, skipna=True).fillna(0.0)
        raw_predictions = np.clip(raw_predictions.to_numpy(dtype=float), 0.0, None)
        return np.log1p(raw_predictions)


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


def _build_bundle(
    model: object,
    encoder: OrdinalEncoder,
    feature_columns: list[str],
    config: PipelineConfig,
    training_metadata: dict[str, object] | None = None,
) -> ModelBundle:
    return ModelBundle(
        model=model,
        encoder=encoder,
        feature_columns=feature_columns,
        model_type=config.model_type,
        training_metadata=training_metadata or {},
    )


def _prepare_eval_data(
    eval_frame: pd.DataFrame | None,
    feature_columns: list[str],
    encoder: OrdinalEncoder,
) -> tuple[pd.DataFrame, np.ndarray] | None:
    if eval_frame is None:
        return None

    X_eval = encoder.transform(eval_frame[feature_columns])
    y_eval = np.log1p(eval_frame["sales"].to_numpy(dtype=float))
    return X_eval, y_eval


def fit_model(
    train_frame: pd.DataFrame,
    config: PipelineConfig,
    eval_frame: pd.DataFrame | None = None,
) -> ModelBundle:
    feature_columns = select_feature_columns(train_frame, config)
    encoder = OrdinalEncoder().fit(train_frame, list(config.categorical_columns))
    X_train = encoder.transform(train_frame[feature_columns])
    y_train = np.log1p(train_frame["sales"].to_numpy(dtype=float))
    sample_weight = build_sample_weights(train_frame["date"])
    eval_data = _prepare_eval_data(eval_frame, feature_columns, encoder)

    if config.model_type == "seasonal_naive":
        model = SeasonalNaiveRegressor()
        model.fit(X_train, y_train, sample_weight=sample_weight)
        return _build_bundle(
            model,
            encoder,
            feature_columns,
            config,
            {"model_params": {}},
        )

    if config.model_type == "ridge":
        params = {"alpha": 1.0}
        params.update(config.model_params)
        model = make_pipeline(StandardScaler(), Ridge(**params))
        model.fit(X_train, y_train, ridge__sample_weight=sample_weight)
        return _build_bundle(
            model,
            encoder,
            feature_columns,
            config,
            {"model_params": params},
        )

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
        return _build_bundle(
            model,
            encoder,
            feature_columns,
            config,
            {"model_params": params},
        )

    if config.model_type == "lightgbm":
        try:
            from lightgbm import early_stopping
            from lightgbm import LGBMRegressor
        except ImportError as exc:
            raise ModelingError(
                "LightGBM is not installed. Install with `pip install -e .[lightgbm]` "
                "or use `--model-type hist_gbdt`."
            ) from exc

        params = build_lightgbm_params(
            preset_name=config.lightgbm_preset,
            random_state=config.random_state,
            overrides=config.model_params,
        )
        model = LGBMRegressor(**params)
        fit_kwargs: dict[str, object] = {"sample_weight": sample_weight}
        if eval_data is not None and config.early_stopping_rounds is not None:
            X_eval, y_eval = eval_data
            fit_kwargs.update(
                {
                    "eval_set": [(X_eval, y_eval)],
                    "eval_metric": "rmse",
                    "callbacks": [early_stopping(config.early_stopping_rounds, verbose=False)],
                }
            )
        model.fit(X_train, y_train, **fit_kwargs)
        best_iteration = getattr(model, "best_iteration_", None)
        if not config.early_stopping_rounds:
            best_iteration = None
        return _build_bundle(
            model,
            encoder,
            feature_columns,
            config,
            {
                "lightgbm_preset": config.lightgbm_preset,
                "model_params": params,
                "early_stopping_rounds": config.early_stopping_rounds,
                "early_stopping_validation_days": config.early_stopping_validation_days,
                "best_iteration": None if best_iteration is None else int(best_iteration),
            },
        )

    raise ModelingError(f"Unsupported model type: {config.model_type}")
