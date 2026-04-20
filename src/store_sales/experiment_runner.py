from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from store_sales.config import PipelineConfig
from store_sales.experiment_log import append_experiment_log, build_experiment_log_row
from store_sales.feature_profiles import apply_feature_profile, available_feature_profiles
from store_sales.pipeline import run_pipeline


@dataclass(frozen=True, slots=True)
class ExperimentSpec:
    name: str
    model_type: str
    feature_profile: str
    train_start_date: str
    description: str


EXPERIMENT_SPECS: dict[str, ExperimentSpec] = {
    "seasonal_naive": ExperimentSpec(
        name="seasonal_naive",
        model_type="seasonal_naive",
        feature_profile="baseline",
        train_start_date="2015-01-01",
        description="Median of recent weekly sales lags; acts as a time-series benchmark.",
    ),
    "ridge_baseline": ExperimentSpec(
        name="ridge_baseline",
        model_type="ridge",
        feature_profile="baseline",
        train_start_date="2015-01-01",
        description="Regularized linear model on the baseline feature set.",
    ),
    "histgbdt_baseline": ExperimentSpec(
        name="histgbdt_baseline",
        model_type="hist_gbdt",
        feature_profile="baseline",
        train_start_date="2015-01-01",
        description="Main tree-model baseline with lag, rolling, promotion, holiday, oil, and store features.",
    ),
    "histgbdt_extended": ExperimentSpec(
        name="histgbdt_extended",
        model_type="hist_gbdt",
        feature_profile="extended",
        train_start_date="2015-01-01",
        description="Tree model with longer seasonal lags for feature-engineering iteration.",
    ),
    "histgbdt_low_demand": ExperimentSpec(
        name="histgbdt_low_demand",
        model_type="hist_gbdt",
        feature_profile="low_demand",
        train_start_date="2015-01-01",
        description="Tree model with leakage-safe family and store-family low-demand history features.",
    ),
    "histgbdt_school_supplies_aug_promo": ExperimentSpec(
        name="histgbdt_school_supplies_aug_promo",
        model_type="hist_gbdt",
        feature_profile="school_supplies_aug_promo",
        train_start_date="2015-01-01",
        description="Tree model with targeted August, promotion, and store interactions for SCHOOL AND OFFICE SUPPLIES.",
    ),
}


def available_experiments() -> tuple[str, ...]:
    return tuple(EXPERIMENT_SPECS)


def _validate_experiment_names(experiment_names: list[str]) -> None:
    unknown = [name for name in experiment_names if name not in EXPERIMENT_SPECS]
    if unknown:
        available = ", ".join(available_experiments())
        raise ValueError(f"Unknown experiments: {', '.join(unknown)}. Available experiments: {available}.")


def build_experiment_config(
    spec: ExperimentSpec,
    data_dir: Path,
    experiment_output_dir: Path,
    validation_horizon: int,
    validation_windows: int,
    validation_step_days: int | None,
    random_state: int,
    make_submission: bool,
) -> PipelineConfig:
    config = PipelineConfig(
        data_dir=data_dir,
        output_dir=experiment_output_dir,
        train_start_date=spec.train_start_date,
        validation_horizon=validation_horizon,
        validation_windows=validation_windows,
        validation_step_days=validation_step_days,
        model_type=spec.model_type,
        feature_profile=spec.feature_profile,
        random_state=random_state,
        make_submission=make_submission,
    )
    return apply_feature_profile(config, spec.feature_profile)


def build_comparison_row(
    spec: ExperimentSpec,
    config: PipelineConfig,
    validation_summary: pd.DataFrame,
    output_dir: Path,
    submission_file: Path | None,
) -> dict[str, object]:
    scores = validation_summary["validation_rmsle"]
    return {
        "experiment_name": spec.name,
        "model_type": spec.model_type,
        "feature_profile": config.feature_profile,
        "train_start_date": config.train_start_date,
        "validation_horizon": config.validation_horizon,
        "validation_windows": config.validation_windows,
        "validation_step_days": config.validation_step_days or config.validation_horizon,
        "validation_rmsle_mean": float(scores.mean()),
        "validation_rmsle_std": float(scores.std(ddof=0)),
        "validation_rmsle_min": float(scores.min()),
        "validation_rmsle_max": float(scores.max()),
        "output_dir": str(output_dir),
        "submission_file": "" if submission_file is None else str(submission_file),
        "description": spec.description,
    }


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in frame.iterrows():
        values = []
        for value in row:
            if isinstance(value, float):
                values.append(f"{value:.6f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def write_comparison_report(results: pd.DataFrame, report_dir: Path) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "comparison_results.csv"
    md_path = report_dir / "comparison_report.md"

    sorted_results = results.sort_values("validation_rmsle_mean").reset_index(drop=True)
    sorted_results.to_csv(csv_path, index=False)

    display_columns = [
        "experiment_name",
        "model_type",
        "feature_profile",
        "validation_rmsle_mean",
        "validation_rmsle_std",
        "validation_rmsle_min",
        "validation_rmsle_max",
    ]
    lines = [
        "# Model Comparison Report",
        "",
        "Lower RMSLE is better. All rows use time-based recursive validation.",
        "",
        "These results rank local validation experiments only. Kaggle public score can differ, so the best local row still needs submission verification.",
        "If `validation_step_days` is smaller than `validation_horizon`, validation windows overlap and should be interpreted accordingly.",
        "",
        "## Results",
        "",
        dataframe_to_markdown(sorted_results[display_columns]),
        "",
        "## Experiment Notes",
        "",
    ]
    for _, row in sorted_results.iterrows():
        lines.append(
            f"- `{row['experiment_name']}`: {row['description']} Output: `{row['output_dir']}`."
        )
    lines.extend(
        [
            "",
            "## Available Feature Profiles",
            "",
            "- `compact`: short lags/windows for quick smoke tests.",
            "- `baseline`: main lag, rolling, promotion, holiday, oil, transaction, and store feature set.",
            "- `extended`: adds longer seasonal lags for feature-engineering iteration.",
            "- `low_demand`: baseline feature set plus family and store-family low-demand history features.",
            "- `school_supplies_aug_promo`: baseline feature set plus targeted SCHOOL AND OFFICE SUPPLIES August, promotion, and store interactions.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path


def run_experiment_suite(
    data_dir: Path,
    output_dir: Path,
    report_dir: Path,
    experiment_names: list[str],
    validation_horizon: int,
    validation_windows: int,
    validation_step_days: int | None,
    random_state: int,
    make_submission: bool,
    log_experiments: bool,
    experiment_log_path: Path,
) -> pd.DataFrame:
    _validate_experiment_names(experiment_names)
    if not available_feature_profiles():
        raise ValueError("No feature profiles are available.")

    rows: list[dict[str, object]] = []
    for experiment_name in experiment_names:
        spec = EXPERIMENT_SPECS[experiment_name]
        experiment_output_dir = output_dir / spec.name
        config = build_experiment_config(
            spec=spec,
            data_dir=data_dir,
            experiment_output_dir=experiment_output_dir,
            validation_horizon=validation_horizon,
            validation_windows=validation_windows,
            validation_step_days=validation_step_days,
            random_state=random_state,
            make_submission=make_submission,
        )
        outputs = run_pipeline(config)
        validation_summary = pd.read_csv(outputs.validation_summary_path)
        rows.append(
            build_comparison_row(
                spec=spec,
                config=config,
                validation_summary=validation_summary,
                output_dir=experiment_output_dir,
                submission_file=outputs.submission_path,
            )
        )

        if log_experiments:
            log_row = build_experiment_log_row(
                config=config,
                outputs=outputs,
                version_name=spec.name,
                data_snapshot=data_dir.name,
                conclusion=f"comparison run; validation_rmsle_mean={outputs.validation_score:.6f}",
                next_action="compare result stability and choose the next feature-engineering direction",
            )
            append_experiment_log(experiment_log_path, log_row)

    results = pd.DataFrame(rows)
    write_comparison_report(results, report_dir)
    return results
