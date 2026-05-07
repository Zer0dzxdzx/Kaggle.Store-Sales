from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import shutil

import pandas as pd

from store_sales.config import PipelineConfig
from store_sales.experiment_runner import dataframe_to_markdown
from store_sales.feature_profiles import apply_feature_profile
from store_sales.pipeline import run_pipeline


@dataclass(frozen=True, slots=True)
class FeatureAblationGroup:
    name: str
    description: str
    columns: tuple[str, ...]
    requires_demand_features: bool = False
    requires_school_supplies_features: bool = False
    requires_transactions: bool = False


@dataclass(frozen=True, slots=True)
class FeatureAblationRun:
    name: str
    group: str
    description: str
    ablated_columns: tuple[str, ...]
    output_dir: Path


def _sales_lag_columns(config: PipelineConfig) -> tuple[str, ...]:
    return tuple(f"sales_lag_{lag}" for lag in config.sales_lags)


def _sales_rolling_columns(config: PipelineConfig) -> tuple[str, ...]:
    columns: list[str] = []
    for window in config.sales_windows:
        columns.extend([f"sales_roll_mean_{window}", f"sales_roll_std_{window}"])
    return tuple(columns)


def _promotion_history_columns(config: PipelineConfig) -> tuple[str, ...]:
    columns = [f"promo_lag_{lag}" for lag in config.promo_lags]
    columns.extend(f"promo_roll_sum_{window}" for window in config.promo_windows)
    return tuple(columns)


def build_feature_ablation_groups(config: PipelineConfig) -> dict[str, FeatureAblationGroup]:
    return {
        "identity": FeatureAblationGroup(
            name="identity",
            description="Remove direct store/family identifiers while keeping history features keyed by them.",
            columns=("store_nbr", "family"),
        ),
        "store_metadata": FeatureAblationGroup(
            name="store_metadata",
            description="Remove store city, state, type, and cluster metadata.",
            columns=("city", "state", "store_type", "cluster"),
        ),
        "calendar": FeatureAblationGroup(
            name="calendar",
            description="Remove regular calendar, payday, and cyclic time features.",
            columns=(
                "day_of_week",
                "day_of_month",
                "day_of_year",
                "week_of_year",
                "month",
                "year",
                "quarter",
                "is_weekend",
                "is_month_start",
                "is_month_end",
                "is_quarter_start",
                "is_quarter_end",
                "is_payday",
                "dow_sin",
                "dow_cos",
                "month_sin",
                "month_cos",
                "doy_sin",
                "doy_cos",
            ),
        ),
        "earthquake": FeatureAblationGroup(
            name="earthquake",
            description="Remove earthquake recency/window features.",
            columns=("days_since_earthquake", "earthquake_window_30"),
        ),
        "sales_lags": FeatureAblationGroup(
            name="sales_lags",
            description="Remove raw sales lag features.",
            columns=_sales_lag_columns(config),
        ),
        "sales_rolling": FeatureAblationGroup(
            name="sales_rolling",
            description="Remove rolling sales mean/std features.",
            columns=_sales_rolling_columns(config),
        ),
        "promotion": FeatureAblationGroup(
            name="promotion",
            description="Remove current and historical promotion features.",
            columns=("onpromotion",) + _promotion_history_columns(config),
        ),
        "oil": FeatureAblationGroup(
            name="oil",
            description="Remove oil price level/change/rolling mean features.",
            columns=("oil_price", "oil_change_7", "oil_mean_7", "oil_mean_28"),
        ),
        "holidays": FeatureAblationGroup(
            name="holidays",
            description="Remove national, regional, and local holiday/event/work-day indicators.",
            columns=(
                "national_holiday_count",
                "national_is_holiday",
                "national_is_event",
                "national_is_work_day",
                "regional_holiday_count",
                "regional_is_holiday",
                "regional_is_event",
                "regional_is_work_day",
                "local_holiday_count",
                "local_is_holiday",
                "local_is_event",
                "local_is_work_day",
            ),
        ),
        "transactions": FeatureAblationGroup(
            name="transactions",
            description="Remove historical store transaction aggregates.",
            columns=("transactions_weekday_mean", "transactions_month_mean"),
            requires_transactions=True,
        ),
        "demand_history": FeatureAblationGroup(
            name="demand_history",
            description="Remove leakage-safe family and store-family demand history features.",
            columns=(
                "family_mean_sales_hist",
                "family_zero_rate_hist",
                "family_row_count_hist",
                "family_is_low_demand",
                "store_family_mean_sales_hist",
                "store_family_zero_rate_hist",
                "store_family_row_count_hist",
                "store_family_is_low_demand",
            ),
            requires_demand_features=True,
        ),
        "school_supplies_targeted": FeatureAblationGroup(
            name="school_supplies_targeted",
            description="Remove targeted SCHOOL AND OFFICE SUPPLIES August/promotion/store interaction features.",
            columns=(
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
            ),
            requires_school_supplies_features=True,
        ),
    }


def available_ablation_groups(config: PipelineConfig) -> tuple[str, ...]:
    return tuple(build_feature_ablation_groups(config))


def default_ablation_groups(config: PipelineConfig) -> tuple[str, ...]:
    groups = [
        "identity",
        "store_metadata",
        "calendar",
        "earthquake",
        "sales_lags",
        "sales_rolling",
        "promotion",
        "oil",
        "holidays",
    ]
    if (config.data_dir / "transactions.csv").exists():
        groups.append("transactions")
    if config.demand_features:
        groups.append("demand_history")
    if config.school_supplies_features:
        groups.append("school_supplies_targeted")
    return tuple(groups)


def _validate_requested_groups(config: PipelineConfig, group_names: tuple[str, ...]) -> None:
    available_groups = build_feature_ablation_groups(config)
    unknown = [name for name in group_names if name not in available_groups]
    if unknown:
        available = ", ".join(available_groups)
        raise ValueError(f"Unknown ablation groups: {', '.join(unknown)}. Available groups: {available}.")


def resolve_group_columns(config: PipelineConfig, group_name: str) -> tuple[str, ...]:
    groups = build_feature_ablation_groups(config)
    group = groups[group_name]
    if group.requires_transactions and not (config.data_dir / "transactions.csv").exists():
        return ()
    if group.requires_demand_features and not config.demand_features:
        return ()
    if group.requires_school_supplies_features and not config.school_supplies_features:
        return ()
    return group.columns


def build_ablation_config(
    base_config: PipelineConfig,
    output_dir: Path,
    ablated_columns: tuple[str, ...],
) -> PipelineConfig:
    drop_columns = tuple(dict.fromkeys(base_config.drop_columns + ablated_columns))
    categorical_columns = tuple(
        column for column in base_config.categorical_columns if column not in drop_columns
    )
    return replace(
        base_config,
        output_dir=output_dir,
        drop_columns=drop_columns,
        categorical_columns=categorical_columns,
        make_submission=False,
    )


def build_ablation_runs(
    config: PipelineConfig,
    output_dir: Path,
    group_names: tuple[str, ...],
) -> list[FeatureAblationRun]:
    _validate_requested_groups(config, group_names)
    groups = build_feature_ablation_groups(config)
    runs = [
        FeatureAblationRun(
            name="baseline",
            group="baseline",
            description="Full feature set for the selected model/profile.",
            ablated_columns=(),
            output_dir=output_dir / "baseline",
        )
    ]
    for group_name in group_names:
        columns = resolve_group_columns(config, group_name)
        if not columns:
            continue
        group = groups[group_name]
        runs.append(
            FeatureAblationRun(
                name=f"without_{group_name}",
                group=group_name,
                description=group.description,
                ablated_columns=columns,
                output_dir=output_dir / f"without_{group_name}",
            )
        )
    return runs


def skipped_ablation_groups(config: PipelineConfig, group_names: tuple[str, ...]) -> tuple[str, ...]:
    _validate_requested_groups(config, group_names)
    return tuple(group_name for group_name in group_names if not resolve_group_columns(config, group_name))


def prepare_ablation_output_paths(
    runs: list[FeatureAblationRun],
    report_dir: Path,
    overwrite: bool,
) -> None:
    report_paths = [report_dir / "ablation_results.csv", report_dir / "ablation_report.md"]
    existing_paths = [path for path in report_paths if path.exists()]
    existing_paths.extend(
        run.output_dir
        for run in runs
        if run.output_dir.exists() and any(run.output_dir.iterdir())
    )

    if existing_paths and not overwrite:
        existing_text = "\n".join(f"- {path}" for path in existing_paths)
        raise FileExistsError(
            "Feature ablation outputs already exist. Choose a new --output-dir/--report-dir "
            f"or rerun with --overwrite.\n{existing_text}"
        )

    if not overwrite:
        return

    for run in runs:
        if run.output_dir.exists():
            shutil.rmtree(run.output_dir)
    for path in report_paths:
        if path.exists():
            path.unlink()


def classify_ablation_signal(mean_delta: float, worst_delta: float) -> str:
    if mean_delta > 0 and worst_delta > 0:
        return "useful"
    if mean_delta < 0 and worst_delta <= 0:
        return "removal_candidate"
    if mean_delta < 0 and worst_delta > 0:
        return "mixed_mean_better_worst_worse"
    if mean_delta > 0 and worst_delta < 0:
        return "mixed_mean_worse_worst_better"
    return "neutral"


def build_result_row(
    run: FeatureAblationRun,
    config: PipelineConfig,
    summary: pd.DataFrame,
    baseline_mean: float,
    baseline_worst: float,
) -> dict[str, object]:
    scores = summary["validation_rmsle"]
    mean_delta = float(scores.mean()) - baseline_mean
    worst_delta = float(scores.max()) - baseline_worst
    row: dict[str, object] = {
        "run_name": run.name,
        "ablation_group": run.group,
        "model_type": config.model_type,
        "lightgbm_preset": config.lightgbm_preset,
        "model_params": _format_model_params(config.model_params),
        "feature_profile": config.feature_profile,
        "early_stopping_rounds": "" if config.early_stopping_rounds is None else config.early_stopping_rounds,
        "early_stopping_validation_days": config.early_stopping_validation_days,
        "ablated_feature_count": len(run.ablated_columns),
        "ablated_columns": "|".join(run.ablated_columns),
        "validation_rmsle_mean": float(scores.mean()),
        "validation_rmsle_std": float(scores.std(ddof=0)),
        "validation_rmsle_min": float(scores.min()),
        "validation_rmsle_max": float(scores.max()),
        "mean_delta_vs_baseline": mean_delta,
        "worst_delta_vs_baseline": worst_delta,
        "ablation_signal": classify_ablation_signal(mean_delta, worst_delta),
        "output_dir": str(run.output_dir),
        "description": run.description,
    }
    for _, fold in summary.sort_values("fold_id").iterrows():
        fold_id = int(fold["fold_id"])
        row[f"fold_{fold_id}_rmsle"] = float(fold["validation_rmsle"])
    return row


def write_ablation_report(
    results: pd.DataFrame,
    report_dir: Path,
    config: PipelineConfig,
    skipped_groups: tuple[str, ...] = (),
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "ablation_results.csv"
    md_path = report_dir / "ablation_report.md"

    sorted_results = results.sort_values("mean_delta_vs_baseline", ascending=False).reset_index(drop=True)
    sorted_results.to_csv(csv_path, index=False)

    display_columns = [
        "run_name",
        "ablation_group",
        "ablated_feature_count",
        "validation_rmsle_mean",
        "validation_rmsle_max",
        "mean_delta_vs_baseline",
        "worst_delta_vs_baseline",
        "ablation_signal",
    ]
    ablated_display = sorted_results[sorted_results["ablation_group"] != "baseline"]
    baseline = results[results["ablation_group"] == "baseline"].iloc[0]
    useful = ablated_display[ablated_display["ablation_signal"] == "useful"].copy()
    removal_candidates = ablated_display[ablated_display["ablation_signal"] == "removal_candidate"].copy()
    mixed = ablated_display[ablated_display["ablation_signal"].str.startswith("mixed_")].copy()

    lines = [
        "# Feature Ablation Report",
        "",
        "Lower RMSLE is better. Positive delta means removing the feature group made validation worse, so the group appears useful under this validation setup.",
        "Negative delta means removing the group improved validation, so the group is a removal or redesign candidate.",
        "Compare this report only with runs that use the same model type, feature profile, validation windows, and model parameter overrides.",
        "",
        "## Setup",
        "",
        f"- Model type: `{config.model_type}`",
        f"- LightGBM preset: `{config.lightgbm_preset}`",
        f"- Model params: `{_format_model_params(config.model_params)}`",
        f"- Feature profile: `{config.feature_profile}`",
        f"- Early stopping rounds: `{config.early_stopping_rounds or ''}`",
        f"- Early stopping validation days: `{config.early_stopping_validation_days}`",
        f"- Train start date: `{config.train_start_date}`",
        f"- Validation horizon: `{config.validation_horizon}`",
        f"- Validation windows: `{config.validation_windows}`",
        f"- Validation step days: `{config.validation_step_days or config.validation_horizon}`",
        f"- Explicit windows: `{_format_validation_windows(config.validation_window_dates)}`",
        f"- Skipped groups: `{_format_group_names(skipped_groups)}`",
        "",
        "## Baseline",
        "",
        f"- Mean RMSLE: `{baseline['validation_rmsle_mean']:.6f}`",
        f"- Worst fold RMSLE: `{baseline['validation_rmsle_max']:.6f}`",
        "",
        "## Results",
        "",
        dataframe_to_markdown(sorted_results[display_columns]),
        "",
        "## Interpretation",
        "",
    ]
    if useful.empty:
        lines.append("- No feature group removal worsened both mean and worst-fold RMSLE versus baseline.")
    else:
        top_helpful = useful.sort_values("mean_delta_vs_baseline", ascending=False).iloc[0]
        lines.append(
            f"- Strongest useful original feature group: `{top_helpful['ablation_group']}` "
            f"(mean delta `{top_helpful['mean_delta_vs_baseline']:.6f}`)."
        )
    if removal_candidates.empty:
        lines.append("- No feature group removal improved both mean and worst-fold RMSLE versus baseline.")
    else:
        top_harmful = removal_candidates.sort_values("mean_delta_vs_baseline").iloc[0]
        lines.append(
            f"- Strongest robust removal candidate: `{top_harmful['ablation_group']}` "
            f"(mean delta `{top_harmful['mean_delta_vs_baseline']:.6f}`)."
        )
    if not mixed.empty:
        top_mixed = mixed.reindex(mixed["mean_delta_vs_baseline"].abs().sort_values(ascending=False).index).iloc[0]
        lines.append(
            f"- Largest mixed result: `{top_mixed['ablation_group']}` "
            f"(`{top_mixed['ablation_signal']}`; mean delta `{top_mixed['mean_delta_vs_baseline']:.6f}`, "
            f"worst delta `{top_mixed['worst_delta_vs_baseline']:.6f}`). Treat this as follow-up evidence, not a direct keep/drop decision."
        )
    lines.extend(
        [
            "",
            "## Ablated Columns",
            "",
        ]
    )
    for _, row in sorted_results.iterrows():
        if row["ablation_group"] == "baseline":
            continue
        lines.append(f"### `{row['ablation_group']}`")
        lines.append("")
        lines.append(str(row["description"]))
        lines.append("")
        lines.append(f"`{row['ablated_columns']}`")
        lines.append("")

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return csv_path, md_path


def _format_validation_windows(windows: tuple[tuple[str, str], ...]) -> str:
    if not windows:
        return ""
    return "|".join(f"{start}:{end}" for start, end in windows)


def _format_model_params(model_params: dict[str, object]) -> str:
    if not model_params:
        return ""
    return "|".join(f"{key}={model_params[key]}" for key in sorted(model_params))


def _format_group_names(group_names: tuple[str, ...]) -> str:
    if not group_names:
        return ""
    return "|".join(group_names)


def run_feature_ablation(
    data_dir: Path,
    output_dir: Path,
    report_dir: Path,
    model_type: str,
    lightgbm_preset: str,
    model_params: dict[str, object],
    early_stopping_rounds: int | None,
    early_stopping_validation_days: int,
    feature_profile: str,
    train_start_date: str | None,
    validation_horizon: int,
    validation_windows: int,
    validation_step_days: int | None,
    validation_window_dates: tuple[tuple[str, str], ...],
    random_state: int,
    group_names: tuple[str, ...] = (),
    overwrite: bool = False,
) -> pd.DataFrame:
    base_config = PipelineConfig(
        data_dir=data_dir,
        output_dir=output_dir / "baseline",
        train_start_date=train_start_date,
        validation_horizon=validation_horizon,
        validation_windows=validation_windows,
        validation_step_days=validation_step_days,
        validation_window_dates=validation_window_dates,
        model_type=model_type,
        lightgbm_preset=lightgbm_preset,
        model_params=model_params,
        early_stopping_rounds=early_stopping_rounds,
        early_stopping_validation_days=early_stopping_validation_days,
        feature_profile=feature_profile,
        random_state=random_state,
        make_submission=False,
    )
    base_config = apply_feature_profile(base_config, feature_profile)
    selected_groups = group_names or default_ablation_groups(base_config)
    runs = build_ablation_runs(base_config, output_dir, selected_groups)
    skipped_groups = skipped_ablation_groups(base_config, selected_groups)
    prepare_ablation_output_paths(runs, report_dir, overwrite=overwrite)

    rows: list[dict[str, object]] = []
    baseline_mean: float | None = None
    baseline_worst: float | None = None
    for run in runs:
        run_config = build_ablation_config(base_config, run.output_dir, run.ablated_columns)
        outputs = run_pipeline(run_config)
        summary = pd.read_csv(outputs.validation_summary_path)
        if run.group == "baseline":
            baseline_mean = float(summary["validation_rmsle"].mean())
            baseline_worst = float(summary["validation_rmsle"].max())
        if baseline_mean is None or baseline_worst is None:
            raise RuntimeError("Baseline ablation run must complete before ablated runs.")
        rows.append(
            build_result_row(
                run=run,
                config=run_config,
                summary=summary,
                baseline_mean=baseline_mean,
                baseline_worst=baseline_worst,
            )
        )

    results = pd.DataFrame(rows)
    write_ablation_report(results, report_dir, base_config, skipped_groups=skipped_groups)
    return results
