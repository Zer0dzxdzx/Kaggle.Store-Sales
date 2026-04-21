from __future__ import annotations

import csv
import subprocess
from datetime import date
from pathlib import Path

from store_sales.config import PipelineConfig
from store_sales.pipeline import PipelineOutputs

EXPERIMENT_LOG_COLUMNS = [
    "date",
    "version_name",
    "goal",
    "commit_hash",
    "data_snapshot",
    "seed",
    "validation_horizon",
    "changed_items",
    "features",
    "preprocessing",
    "model",
    "validation_scheme",
    "validation_rmsle",
    "kaggle_public_score",
    "submission_file",
    "conclusion",
    "next_action",
]


def get_git_commit_hash() -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown"

    if status:
        return f"{commit}+dirty"
    return commit


def build_feature_summary(config: PipelineConfig) -> str:
    calendar_features = [
        "day_of_week",
        "month",
        "week_of_year",
        "is_month_end",
        "is_payday",
    ]
    lag_features = [f"sales_lag_{lag}" for lag in config.sales_lags]
    rolling_features = [f"sales_roll_mean_{window}" for window in config.sales_windows]
    promo_features = [f"promo_lag_{lag}" for lag in config.promo_lags]
    promo_features += [f"promo_roll_sum_{window}" for window in config.promo_windows]
    exogenous_features = [
        "oil_price",
        "oil_change_7",
        "national_is_holiday",
        "regional_is_holiday",
        "local_is_holiday",
        "city",
        "state",
        "store_type",
        "cluster",
        "days_since_earthquake",
    ]
    demand_features = []
    if config.demand_features:
        demand_features = [
            "family_mean_sales_hist",
            "family_zero_rate_hist",
            "family_row_count_hist",
            "family_is_low_demand",
            "store_family_mean_sales_hist",
            "store_family_zero_rate_hist",
            "store_family_row_count_hist",
            "store_family_is_low_demand",
        ]
    school_supplies_features = []
    if config.school_supplies_features:
        school_supplies_features = [
            "is_school_supplies",
            "school_supplies_august",
            "school_supplies_onpromotion",
            "school_supplies_onpromotion_log1p",
            "school_supplies_promo_6_plus",
            "school_supplies_promo_11_50",
            "school_supplies_type_a",
            "school_supplies_quito_ambato",
            "school_supplies_type_a_high_promo",
            "school_supplies_quito_ambato_high_promo",
            "school_supplies_august_high_promo",
            "school_supplies_august_type_a",
        ]
    return "|".join(
        [f"profile={config.feature_profile}"]
        + calendar_features
        + lag_features
        + rolling_features
        + promo_features
        + exogenous_features
        + demand_features
        + school_supplies_features
    )


def build_validation_scheme(config: PipelineConfig) -> str:
    if config.validation_window_dates:
        windows = "|".join(f"{start}:{end}" for start, end in config.validation_window_dates)
        return f"time split + recursive forecast; explicit_windows={windows}"

    step_days = config.validation_step_days or config.validation_horizon
    return (
        f"time split + recursive forecast; windows={config.validation_windows}; "
        f"horizon={config.validation_horizon}; step_days={step_days}"
    )


def build_experiment_log_row(
    config: PipelineConfig,
    outputs: PipelineOutputs,
    version_name: str,
    data_snapshot: str,
    conclusion: str | None = None,
    next_action: str | None = None,
) -> dict[str, str]:
    mean_score = f"{outputs.validation_score:.6f}"
    if outputs.submission_path is None:
        default_conclusion = f"validation_rmsle_mean={mean_score}; validation-only run"
        submission_file = ""
        changed_items = "ran validation pipeline; generated validation metrics, fold summary, and validation predictions"
    else:
        default_conclusion = f"validation_rmsle_mean={mean_score}; generated submission at {outputs.submission_path}"
        submission_file = str(outputs.submission_path)
        changed_items = (
            "ran full pipeline; generated validation metrics, fold summary, validation predictions, and submission"
        )
    default_next_action = "compare against Kaggle public score and inspect multi-window stability"

    return {
        "date": date.today().isoformat(),
        "version_name": version_name,
        "goal": "run Store Sales pipeline and record validation/submission outputs",
        "commit_hash": get_git_commit_hash(),
        "data_snapshot": data_snapshot,
        "seed": str(config.random_state),
        "validation_horizon": str(config.validation_horizon),
        "changed_items": changed_items,
        "features": build_feature_summary(config),
        "preprocessing": (
            "sales log1p target; oil daily interpolation; holiday locale aggregation; "
            "historical transaction aggregation; ordinal categorical encoding"
        ),
        "model": config.model_type,
        "validation_scheme": build_validation_scheme(config),
        "validation_rmsle": mean_score,
        "kaggle_public_score": "",
        "submission_file": submission_file,
        "conclusion": conclusion or default_conclusion,
        "next_action": next_action or default_next_action,
    }


def append_experiment_log(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists() and path.stat().st_size > 0

    with path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=EXPERIMENT_LOG_COLUMNS, lineterminator="\n")
        if not file_exists:
            writer.writeheader()
        writer.writerow({column: row.get(column, "") for column in EXPERIMENT_LOG_COLUMNS})
