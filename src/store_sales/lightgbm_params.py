from __future__ import annotations

from copy import deepcopy
from typing import Any


LIGHTGBM_PARAMETER_PRESETS: dict[str, dict[str, Any]] = {
    "baseline": {
        "objective": "regression",
        "n_estimators": 1200,
        "learning_rate": 0.03,
        "num_leaves": 255,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },
    "shrinkage": {
        "objective": "regression",
        "n_estimators": 2400,
        "learning_rate": 0.015,
        "num_leaves": 127,
        "min_child_samples": 60,
        "subsample": 0.85,
        "subsample_freq": 1,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.0,
        "reg_lambda": 0.5,
    },
    "regularized": {
        "objective": "regression",
        "n_estimators": 1800,
        "learning_rate": 0.02,
        "num_leaves": 96,
        "min_child_samples": 100,
        "subsample": 0.75,
        "subsample_freq": 1,
        "colsample_bytree": 0.75,
        "reg_alpha": 0.05,
        "reg_lambda": 1.5,
    },
    "conservative": {
        "objective": "regression",
        "n_estimators": 1600,
        "learning_rate": 0.025,
        "num_leaves": 63,
        "min_child_samples": 120,
        "subsample": 0.85,
        "subsample_freq": 1,
        "colsample_bytree": 0.7,
        "reg_alpha": 0.1,
        "reg_lambda": 2.0,
    },
}


def available_lightgbm_presets() -> tuple[str, ...]:
    return tuple(LIGHTGBM_PARAMETER_PRESETS)


def build_lightgbm_params(
    preset_name: str,
    random_state: int,
    overrides: dict[str, object] | None = None,
) -> dict[str, Any]:
    if preset_name not in LIGHTGBM_PARAMETER_PRESETS:
        available = ", ".join(available_lightgbm_presets())
        raise ValueError(f"Unknown LightGBM preset `{preset_name}`. Available presets: {available}.")

    params = deepcopy(LIGHTGBM_PARAMETER_PRESETS[preset_name])
    params["random_state"] = random_state
    if overrides:
        params.update(overrides)
    return params
