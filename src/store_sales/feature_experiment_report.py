from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from store_sales.error_analysis import (
    dataframe_to_markdown,
    enrich_predictions,
    load_validation_predictions,
    load_validation_summary,
    validate_validation_summary,
)


DEFAULT_FAMILY = "SCHOOL AND OFFICE SUPPLIES"
SUMMARY_SETUP_COLUMNS = ["fold_id", "validation_start", "validation_end", "train_rows", "validation_rows"]
METRIC_COMPATIBILITY_FIELDS = [
    "validation_horizon_days",
    "validation_windows",
    "validation_step_days",
    "model_type",
]
PREDICTION_KEY_COLUMNS = ["fold_id", "date", "store_nbr", "family"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the School Supplies August/Promotion feature experiment report."
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--baseline-artifacts-dir", type=Path, default=Path("artifacts/experiments/histgbdt_baseline"))
    parser.add_argument("--experiment-artifacts-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-name", default="histgbdt_baseline")
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--feature-profile", default="school_supplies_aug_promo")
    parser.add_argument("--baseline-public-score", default="0.58410")
    parser.add_argument("--family", default=DEFAULT_FAMILY)
    parser.add_argument("--target-fold", type=int, default=3)
    parser.add_argument("--min-rows", type=int, default=4)
    return parser


def summarize_error(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    grouped = (
        frame.groupby(group_columns, dropna=False)
        .agg(
            row_count=("sales", "size"),
            squared_log_error_sum=("squared_log_error", "sum"),
            mean_actual_sales=("sales", "mean"),
            mean_predicted_sales=("sales_pred", "mean"),
            mean_signed_error=("signed_error", "mean"),
            mean_onpromotion=("onpromotion", "mean"),
        )
        .reset_index()
    )
    grouped["rmsle"] = np.sqrt(grouped["squared_log_error_sum"] / grouped["row_count"].clip(lower=1))
    total_sse = max(float(frame["squared_log_error"].sum()), np.finfo(float).eps)
    grouped["error_share"] = grouped["squared_log_error_sum"] / total_sse
    return grouped


def prefix_columns(frame: pd.DataFrame, group_columns: list[str], prefix: str) -> pd.DataFrame:
    return frame.rename(columns={column: f"{prefix}_{column}" for column in frame.columns if column not in group_columns})


def compare_summaries(
    baseline: pd.DataFrame,
    experiment: pd.DataFrame,
    group_columns: list[str],
    min_rows: int = 1,
) -> pd.DataFrame:
    baseline_summary = prefix_columns(summarize_error(baseline, group_columns), group_columns, "baseline")
    experiment_summary = prefix_columns(summarize_error(experiment, group_columns), group_columns, "experiment")
    comparison = baseline_summary.merge(experiment_summary, on=group_columns, how="inner")
    comparison = comparison[
        (comparison["baseline_row_count"] >= min_rows) & (comparison["experiment_row_count"] >= min_rows)
    ].copy()
    comparison["rmsle_delta"] = comparison["experiment_rmsle"] - comparison["baseline_rmsle"]
    comparison["mean_predicted_sales_delta"] = (
        comparison["experiment_mean_predicted_sales"] - comparison["baseline_mean_predicted_sales"]
    )
    comparison["mean_signed_error_delta"] = (
        comparison["experiment_mean_signed_error"] - comparison["baseline_mean_signed_error"]
    )
    return comparison


def load_validation_metrics(artifacts_dir: Path) -> dict[str, object]:
    metrics_path = artifacts_dir / "validation_metrics.json"
    if not metrics_path.exists():
        return {}
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def validate_metric_compatibility(baseline_dir: Path, experiment_dir: Path) -> None:
    baseline_metrics = load_validation_metrics(baseline_dir)
    experiment_metrics = load_validation_metrics(experiment_dir)
    if not baseline_metrics or not experiment_metrics:
        return

    mismatches = []
    for field in METRIC_COMPATIBILITY_FIELDS:
        if baseline_metrics.get(field) != experiment_metrics.get(field):
            mismatches.append(
                {
                    "field": field,
                    "baseline": baseline_metrics.get(field),
                    "experiment": experiment_metrics.get(field),
                }
            )
    if mismatches:
        mismatch_text = pd.DataFrame(mismatches).to_string(index=False)
        raise ValueError(f"Baseline and experiment validation settings differ:\n{mismatch_text}")


def validate_summary_compatibility(baseline: pd.DataFrame, experiment: pd.DataFrame) -> None:
    missing_by_label = {
        "baseline": set(SUMMARY_SETUP_COLUMNS + ["validation_rmsle"]).difference(baseline.columns),
        "experiment": set(SUMMARY_SETUP_COLUMNS + ["validation_rmsle"]).difference(experiment.columns),
    }
    missing_messages = [f"{label}: {sorted(missing)}" for label, missing in missing_by_label.items() if missing]
    if missing_messages:
        raise ValueError("Validation summary is missing required columns: " + "; ".join(missing_messages))

    baseline_setup = baseline[SUMMARY_SETUP_COLUMNS].sort_values("fold_id").reset_index(drop=True)
    experiment_setup = experiment[SUMMARY_SETUP_COLUMNS].sort_values("fold_id").reset_index(drop=True)
    if baseline_setup.equals(experiment_setup):
        return

    comparison = baseline_setup.merge(
        experiment_setup,
        on="fold_id",
        how="outer",
        suffixes=("_baseline", "_experiment"),
        indicator=True,
    )
    mismatch_rows = comparison[comparison["_merge"] != "both"].copy()
    for column in SUMMARY_SETUP_COLUMNS:
        if column == "fold_id":
            continue
        baseline_column = f"{column}_baseline"
        experiment_column = f"{column}_experiment"
        if baseline_column in comparison.columns and experiment_column in comparison.columns:
            mismatch_rows = pd.concat(
                [
                    mismatch_rows,
                    comparison[
                        (comparison["_merge"] == "both")
                        & (comparison[baseline_column] != comparison[experiment_column])
                    ],
                ],
                ignore_index=True,
            )
    mismatch_rows = mismatch_rows.drop_duplicates()
    raise ValueError(
        "Baseline and experiment validation windows/row counts differ. "
        "Do not compare artifacts from different validation setups.\n"
        f"{mismatch_rows.to_string(index=False)}"
    )


def validate_prediction_key_compatibility(baseline: pd.DataFrame, experiment: pd.DataFrame) -> None:
    for label, frame in [("baseline", baseline), ("experiment", experiment)]:
        missing = set(PREDICTION_KEY_COLUMNS + ["sales"]).difference(frame.columns)
        if missing:
            raise ValueError(f"{label} predictions are missing required columns: {sorted(missing)}")
        duplicates = frame[frame.duplicated(PREDICTION_KEY_COLUMNS, keep=False)]
        if not duplicates.empty:
            sample = duplicates[PREDICTION_KEY_COLUMNS].head(10).to_string(index=False)
            raise ValueError(f"{label} predictions contain duplicate validation keys:\n{sample}")

    baseline_index = pd.MultiIndex.from_frame(baseline[PREDICTION_KEY_COLUMNS])
    experiment_index = pd.MultiIndex.from_frame(experiment[PREDICTION_KEY_COLUMNS])
    missing_in_experiment = baseline_index.difference(experiment_index)
    missing_in_baseline = experiment_index.difference(baseline_index)
    if missing_in_experiment.empty and missing_in_baseline.empty:
        return

    messages = []
    if not missing_in_experiment.empty:
        messages.append(f"keys missing in experiment: {list(missing_in_experiment[:5])}")
    if not missing_in_baseline.empty:
        messages.append(f"keys missing in baseline: {list(missing_in_baseline[:5])}")
    raise ValueError(
        "Baseline and experiment predictions do not cover the same validation rows; "
        + "; ".join(messages)
    )


def validate_prediction_truth_compatibility(baseline: pd.DataFrame, experiment: pd.DataFrame) -> None:
    sort_columns = PREDICTION_KEY_COLUMNS
    selected_columns = PREDICTION_KEY_COLUMNS + ["sales"]
    baseline_aligned = baseline[selected_columns].sort_values(sort_columns).reset_index(drop=True)
    experiment_aligned = experiment[selected_columns].sort_values(sort_columns).reset_index(drop=True)

    if not baseline_aligned[PREDICTION_KEY_COLUMNS].equals(experiment_aligned[PREDICTION_KEY_COLUMNS]):
        raise ValueError("Prediction keys are not aligned after sorting. Run key compatibility checks first.")

    baseline_sales = baseline_aligned["sales"].to_numpy(dtype=float)
    experiment_sales = experiment_aligned["sales"].to_numpy(dtype=float)
    sales_match = np.isclose(baseline_sales, experiment_sales, rtol=0.0, atol=1e-9, equal_nan=True)
    if sales_match.all():
        return

    sample = baseline_aligned.loc[~sales_match, selected_columns].merge(
        experiment_aligned.loc[~sales_match, selected_columns],
        on=PREDICTION_KEY_COLUMNS,
        suffixes=("_baseline", "_experiment"),
    )
    raise ValueError(
        "Baseline and experiment predictions have different validation truth values for the same keys:\n"
        f"{sample.head(10).to_string(index=False)}"
    )


def build_validation_comparison_from_summaries(
    baseline: pd.DataFrame,
    experiment: pd.DataFrame,
    paths_dir: Path,
) -> pd.DataFrame:
    comparison = baseline[["fold_id", "validation_rmsle"]].merge(
        experiment[["fold_id", "validation_rmsle"]],
        on="fold_id",
        suffixes=("_baseline", "_experiment"),
    )
    comparison["rmsle_delta"] = comparison["validation_rmsle_experiment"] - comparison["validation_rmsle_baseline"]
    mean_row = pd.DataFrame(
        [
            {
                "fold_id": "mean",
                "validation_rmsle_baseline": comparison["validation_rmsle_baseline"].mean(),
                "validation_rmsle_experiment": comparison["validation_rmsle_experiment"].mean(),
                "rmsle_delta": comparison["rmsle_delta"].mean(),
            }
        ]
    )
    comparison = pd.concat([comparison, mean_row], ignore_index=True)
    comparison.to_csv(paths_dir / "validation_comparison.csv", index=False)
    return comparison


def build_validation_comparison(
    baseline_dir: Path,
    experiment_dir: Path,
    paths_dir: Path,
) -> pd.DataFrame:
    validate_metric_compatibility(baseline_dir, experiment_dir)
    baseline = load_validation_summary(baseline_dir)
    experiment = load_validation_summary(experiment_dir)
    validate_summary_compatibility(baseline, experiment)
    return build_validation_comparison_from_summaries(baseline, experiment, paths_dir)


def load_checked_predictions(artifacts_dir: Path) -> pd.DataFrame:
    predictions = load_validation_predictions(artifacts_dir)
    validation_summary = load_validation_summary(artifacts_dir)
    validate_validation_summary(predictions, validation_summary)
    return predictions


def load_enriched_predictions(artifacts_dir: Path, data_dir: Path) -> pd.DataFrame:
    return enrich_predictions(load_checked_predictions(artifacts_dir), data_dir)


def build_target_family_comparison(
    baseline: pd.DataFrame,
    experiment: pd.DataFrame,
    family: str,
    paths_dir: Path,
) -> pd.DataFrame:
    baseline_family = baseline[baseline["family"] == family].copy()
    experiment_family = experiment[experiment["family"] == family].copy()
    if baseline_family.empty or experiment_family.empty:
        raise ValueError(
            f"No validation rows found for family `{family}`: "
            f"baseline_rows={len(baseline_family)}, experiment_rows={len(experiment_family)}"
        )
    comparison = compare_summaries(baseline_family, experiment_family, ["fold_id"])
    if comparison.empty:
        raise ValueError(f"No comparable validation folds found for family `{family}`.")
    comparison = comparison.sort_values("fold_id").reset_index(drop=True)
    comparison.to_csv(paths_dir / "target_family_fold_comparison.csv", index=False)
    return comparison


def build_target_store_promotion_comparison(
    baseline: pd.DataFrame,
    experiment: pd.DataFrame,
    family: str,
    target_fold: int,
    min_rows: int,
    paths_dir: Path,
) -> pd.DataFrame:
    group_columns = ["store_nbr", "city", "store_type", "promotion_bin"]
    baseline_target = baseline[(baseline["family"] == family) & (baseline["fold_id"] == target_fold)].copy()
    experiment_target = experiment[(experiment["family"] == family) & (experiment["fold_id"] == target_fold)].copy()
    if baseline_target.empty or experiment_target.empty:
        raise ValueError(
            f"No target rows found for family `{family}` and fold `{target_fold}`: "
            f"baseline_rows={len(baseline_target)}, experiment_rows={len(experiment_target)}"
        )
    comparison = compare_summaries(baseline_target, experiment_target, group_columns, min_rows=min_rows)
    if comparison.empty:
        raise ValueError(
            f"No comparable store-promotion segments found for family `{family}`, "
            f"fold `{target_fold}`, min_rows={min_rows}."
        )
    comparison = comparison.sort_values(
        ["baseline_error_share", "baseline_rmsle"],
        ascending=[False, False],
    ).reset_index(drop=True)
    comparison.to_csv(paths_dir / "target_fold_store_promotion_comparison.csv", index=False)
    return comparison


def format_float(value: float) -> str:
    return f"{value:.6f}"


def write_report(
    output_dir: Path,
    baseline_name: str,
    experiment_name: str,
    feature_profile: str,
    baseline_public_score: str,
    family: str,
    target_fold: int,
    validation_comparison: pd.DataFrame,
    family_comparison: pd.DataFrame,
    store_promotion_comparison: pd.DataFrame,
) -> Path:
    report_path = output_dir / "experiment_report.md"
    mean_rows = validation_comparison[validation_comparison["fold_id"].astype("string") == "mean"]
    if mean_rows.empty:
        raise ValueError("Validation comparison is missing the mean row.")
    target_family_rows = family_comparison[family_comparison["fold_id"] == target_fold]
    if target_family_rows.empty:
        available_folds = sorted(family_comparison["fold_id"].unique().tolist())
        raise ValueError(f"Target fold `{target_fold}` not found in family comparison. Available folds: {available_folds}")

    mean_row = mean_rows.iloc[0]
    family_target = target_family_rows.iloc[0]
    top_segment = store_promotion_comparison.iloc[0]

    validation_display = validation_comparison.copy()
    family_display = family_comparison[
        [
            "fold_id",
            "baseline_rmsle",
            "experiment_rmsle",
            "rmsle_delta",
            "baseline_mean_actual_sales",
            "baseline_mean_predicted_sales",
            "experiment_mean_predicted_sales",
            "mean_predicted_sales_delta",
        ]
    ].copy()
    family_display["fold_id"] = family_display["fold_id"].astype(int).astype(str)
    segment_columns = [
        "store_nbr",
        "city",
        "store_type",
        "promotion_bin",
        "baseline_row_count",
        "baseline_rmsle",
        "experiment_rmsle",
        "rmsle_delta",
        "baseline_mean_actual_sales",
        "baseline_mean_predicted_sales",
        "experiment_mean_predicted_sales",
        "mean_predicted_sales_delta",
    ]
    segment_display = store_promotion_comparison[segment_columns].head(10).copy()

    decision = "candidate"
    if mean_row["rmsle_delta"] >= 0 or family_target["rmsle_delta"] >= 0:
        decision = "reject_or_rework"

    lines = [
        f"# Feature Experiment Report: `{experiment_name}`",
        "",
        "## Experiment Goal / 实验目标",
        "",
        f"验证针对 `{family}` 的窄特征，是否能缓解 fold {target_fold} underprediction，同时不明显伤害整体 validation。",
        "",
        "This experiment follows the fold 3 cross-error and family focus analysis. It is intentionally narrow: only features are changed; the model stays the same.",
        "",
        "注意：这些特征是在 fold 3 error analysis 之后设计的，所以 fold 3 改善只能说明这是一个 candidate，不等于已经证明能泛化到 Kaggle test period。",
        "",
        "## Setup",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| Experiment name | `{experiment_name}` |",
        f"| Baseline comparison | `{baseline_name}` |",
        "| Model | `hist_gbdt` |",
        f"| Feature profile | `{feature_profile}` |",
        "| Validation scheme | 3 non-overlapping time windows, 16 days each |",
        "| Submission generated | No |",
        "",
        "New feature groups / 新增特征组：",
        "",
        "- `is_school_supplies`",
        "- `school_supplies_august`",
        "- `school_supplies_onpromotion` and `school_supplies_onpromotion_log1p`",
        "- `school_supplies_promo_6_plus` and `school_supplies_promo_11_50`",
        "- `school_supplies_type_a` and `school_supplies_quito_ambato`",
        "- interaction flags for August, high promotion, type A, and Quito/Ambato",
        "",
        "Leakage boundary / 防泄漏边界：这些特征只使用 `date`、`family`、`onpromotion`、`store_type`、`city`，这些字段在 validation/test 预测时已知；不使用 validation/test 真实 `sales`。",
        "",
        "## Validation Result / 验证结果",
        "",
        dataframe_to_markdown(validation_display, max_rows=len(validation_display)),
        "",
        "Lower RMSLE is better / RMSLE 越低越好。",
        "",
        f"- Mean RMSLE delta: `{format_float(mean_row['rmsle_delta'])}`.",
        f"- Fold {target_fold} target family RMSLE delta: `{format_float(family_target['rmsle_delta'])}`.",
    ]
    if top_segment is not None:
        lines.append(
            f"- Top fold {target_fold} target segment: store `{int(top_segment['store_nbr'])}` + promotion bin `{top_segment['promotion_bin']}`, "
            f"baseline predicted mean `{top_segment['baseline_mean_predicted_sales']:.1f}`, "
            f"experiment predicted mean `{top_segment['experiment_mean_predicted_sales']:.1f}`, "
            f"actual mean `{top_segment['baseline_mean_actual_sales']:.1f}`."
        )

    lines.extend(
        [
            "",
            "## Target Family Fold Check / 目标 family 检查",
            "",
            dataframe_to_markdown(family_display, max_rows=len(family_display)),
            "",
            f"## Fold {target_fold} Store-Promotion Check / 目标片段检查",
            "",
            dataframe_to_markdown(segment_display, max_rows=10),
            "",
            "## Decision",
            "",
        ]
    )

    if decision == "candidate":
        lines.extend(
            [
                "Keep this feature profile as a candidate, but do not replace the default baseline yet.",
                "",
                "保留为 candidate profile，但暂时不替换默认 baseline。",
                "",
                "Reason:",
                "",
                "- Mean RMSLE improves versus baseline.",
                f"- Fold {target_fold} improves versus baseline.",
                f"- `{family}` fold {target_fold} improves versus baseline.",
                "- The original underprediction in high-promotion store segments is reduced.",
                "- 风险：该实验是根据 fold 3 问题反推设计的，存在 validation selection bias，需要 public score 或更多未参与设计的窗口验证。",
                "",
                "Next action: generate a submission with this profile and compare Kaggle public score "
                f"against the current baseline public score `{baseline_public_score}`.",
            ]
        )
    else:
        lines.extend(
            [
                "Do not keep this feature profile as a candidate in its current form.",
                "",
                "当前版本不应作为 candidate 保留。",
                "",
                "Reason:",
                "",
                "- Either mean RMSLE or the target family fold check did not improve.",
                "- The feature hypothesis needs to be narrowed or reworked before submission.",
            ]
        )

    lines.extend(
        [
            "",
            "## Generated Tables",
            "",
            "- `tables/validation_comparison.csv`",
            "- `tables/target_family_fold_comparison.csv`",
            "- `tables/target_fold_store_promotion_comparison.csv`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def run_report(
    data_dir: Path,
    baseline_artifacts_dir: Path,
    experiment_artifacts_dir: Path,
    output_dir: Path,
    baseline_name: str,
    experiment_name: str,
    feature_profile: str,
    baseline_public_score: str,
    family: str,
    target_fold: int,
    min_rows: int,
) -> Path:
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    validate_metric_compatibility(baseline_artifacts_dir, experiment_artifacts_dir)
    baseline_summary = load_validation_summary(baseline_artifacts_dir)
    experiment_summary = load_validation_summary(experiment_artifacts_dir)
    validate_summary_compatibility(baseline_summary, experiment_summary)

    baseline_predictions = load_checked_predictions(baseline_artifacts_dir)
    experiment_predictions = load_checked_predictions(experiment_artifacts_dir)
    validate_prediction_key_compatibility(baseline_predictions, experiment_predictions)
    validate_prediction_truth_compatibility(baseline_predictions, experiment_predictions)

    validation_comparison = build_validation_comparison_from_summaries(
        baseline_summary,
        experiment_summary,
        tables_dir,
    )
    baseline = enrich_predictions(baseline_predictions, data_dir)
    experiment = enrich_predictions(experiment_predictions, data_dir)
    target_family = build_target_family_comparison(baseline, experiment, family, tables_dir)
    target_segments = build_target_store_promotion_comparison(
        baseline,
        experiment,
        family,
        target_fold,
        min_rows,
        tables_dir,
    )
    return write_report(
        output_dir=output_dir,
        baseline_name=baseline_name,
        experiment_name=experiment_name,
        feature_profile=feature_profile,
        baseline_public_score=baseline_public_score,
        family=family,
        target_fold=target_fold,
        validation_comparison=validation_comparison,
        family_comparison=target_family,
        store_promotion_comparison=target_segments,
    )


def main() -> None:
    args = build_parser().parse_args()
    report_path = run_report(
        data_dir=args.data_dir,
        baseline_artifacts_dir=args.baseline_artifacts_dir,
        experiment_artifacts_dir=args.experiment_artifacts_dir,
        output_dir=args.output_dir,
        baseline_name=args.baseline_name,
        experiment_name=args.experiment_name,
        feature_profile=args.feature_profile,
        baseline_public_score=args.baseline_public_score,
        family=args.family,
        target_fold=args.target_fold,
        min_rows=args.min_rows,
    )
    print(f"Feature experiment report: {report_path}")


if __name__ == "__main__":
    main()
