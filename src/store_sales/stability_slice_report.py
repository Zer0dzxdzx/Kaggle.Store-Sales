from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from store_sales.error_analysis import (
    PROMOTION_BINS,
    PROMOTION_LABELS,
    dataframe_to_markdown,
    enrich_predictions,
    load_validation_predictions,
    load_validation_summary,
    validate_validation_summary,
)
from store_sales.feature_experiment_report import (
    compare_summaries,
    validate_metric_compatibility,
    validate_prediction_key_compatibility,
    validate_prediction_truth_compatibility,
    validate_summary_compatibility,
)


DEFAULT_TARGET_FAMILY = "SCHOOL AND OFFICE SUPPLIES"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate public-like stability slice checks.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--baseline-artifacts-dir", type=Path, required=True)
    parser.add_argument("--experiment-artifacts-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-name", default="histgbdt_baseline")
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--target-family", default=DEFAULT_TARGET_FAMILY)
    parser.add_argument("--min-rows", type=int, default=30)
    return parser


def load_checked_predictions(artifacts_dir: Path) -> pd.DataFrame:
    predictions = load_validation_predictions(artifacts_dir)
    summary = load_validation_summary(artifacts_dir)
    validate_validation_summary(predictions, summary)
    return predictions


def load_comparable_predictions(
    baseline_artifacts_dir: Path,
    experiment_artifacts_dir: Path,
    data_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validate_metric_compatibility(baseline_artifacts_dir, experiment_artifacts_dir)
    baseline_summary = load_validation_summary(baseline_artifacts_dir)
    experiment_summary = load_validation_summary(experiment_artifacts_dir)
    validate_summary_compatibility(baseline_summary, experiment_summary)

    baseline_predictions = load_checked_predictions(baseline_artifacts_dir)
    experiment_predictions = load_checked_predictions(experiment_artifacts_dir)
    validate_prediction_key_compatibility(baseline_predictions, experiment_predictions)
    validate_prediction_truth_compatibility(baseline_predictions, experiment_predictions)
    return (
        enrich_predictions(baseline_predictions, data_dir),
        enrich_predictions(experiment_predictions, data_dir),
        baseline_summary,
        experiment_summary,
    )


def add_target_flags(frame: pd.DataFrame, target_family: str) -> pd.DataFrame:
    output = frame.copy()
    output["target_group"] = np.where(output["family"] == target_family, "target_family", "non_target_family")
    return output


def build_slice_comparison(
    baseline: pd.DataFrame,
    experiment: pd.DataFrame,
    group_columns: list[str],
    min_rows: int,
    output_path: Path,
) -> pd.DataFrame:
    comparison = compare_summaries(baseline, experiment, group_columns, min_rows=min_rows)
    comparison = comparison.sort_values(["rmsle_delta", "baseline_row_count"], ascending=[False, False])
    comparison.to_csv(output_path, index=False)
    return comparison


def summarize_validation_windows(baseline_summary: pd.DataFrame, experiment_summary: pd.DataFrame) -> pd.DataFrame:
    comparison = baseline_summary[["fold_id", "validation_start", "validation_end", "validation_rmsle"]].merge(
        experiment_summary[["fold_id", "validation_rmsle"]],
        on="fold_id",
        suffixes=("_baseline", "_experiment"),
    )
    comparison["rmsle_delta"] = comparison["validation_rmsle_experiment"] - comparison["validation_rmsle_baseline"]
    return comparison


def load_test_context(data_dir: Path) -> pd.DataFrame:
    test = pd.read_csv(
        data_dir / "test.csv",
        usecols=["date", "store_nbr", "family", "onpromotion"],
        parse_dates=["date"],
        dtype={"store_nbr": "int16", "family": "string", "onpromotion": "int16"},
    )
    stores = pd.read_csv(
        data_dir / "stores.csv",
        dtype={
            "store_nbr": "int16",
            "city": "string",
            "state": "string",
            "type": "string",
            "cluster": "int16",
        },
    ).rename(columns={"type": "store_type"})
    test = test.merge(stores, on="store_nbr", how="left")
    test["promotion_bin"] = pd.cut(
        test["onpromotion"],
        bins=PROMOTION_BINS,
        labels=PROMOTION_LABELS,
    ).astype("string")
    return test


def build_distribution_drift(
    validation: pd.DataFrame,
    test: pd.DataFrame,
    group_columns: list[str],
    output_path: Path,
) -> pd.DataFrame:
    validation_counts = validation.groupby(group_columns, dropna=False).size().rename("validation_rows").reset_index()
    test_counts = test.groupby(group_columns, dropna=False).size().rename("test_rows").reset_index()
    drift = validation_counts.merge(test_counts, on=group_columns, how="outer").fillna(
        {"validation_rows": 0, "test_rows": 0}
    )
    drift["validation_share"] = drift["validation_rows"] / drift["validation_rows"].sum()
    drift["test_share"] = drift["test_rows"] / drift["test_rows"].sum()
    drift["test_minus_validation_share"] = drift["test_share"] - drift["validation_share"]
    drift["abs_share_delta"] = drift["test_minus_validation_share"].abs()
    drift = drift.sort_values("abs_share_delta", ascending=False).reset_index(drop=True)
    drift.to_csv(output_path, index=False)
    return drift


def filter_non_target_family(family_comparison: pd.DataFrame, target_family: str) -> pd.DataFrame:
    return family_comparison[family_comparison["family"] != target_family].copy()


def build_overweighted_regressions(
    family_promotion_comparison: pd.DataFrame,
    family_promotion_drift: pd.DataFrame,
    target_family: str,
    output_path: Path,
) -> pd.DataFrame:
    slice_deltas = family_promotion_comparison[
        ["family", "promotion_bin", "rmsle_delta", "baseline_rmsle", "experiment_rmsle"]
    ].copy()
    merged = family_promotion_drift.merge(slice_deltas, on=["family", "promotion_bin"], how="left")
    regressions = merged[
        (merged["family"] != target_family)
        & (merged["rmsle_delta"] > 0)
        & (merged["test_minus_validation_share"] > 0)
    ].copy()
    regressions = regressions.sort_values(
        ["test_minus_validation_share", "rmsle_delta"],
        ascending=[False, False],
    ).reset_index(drop=True)
    regressions.to_csv(output_path, index=False)
    return regressions


def write_report(
    output_dir: Path,
    baseline_name: str,
    experiment_name: str,
    target_family: str,
    validation_comparison: pd.DataFrame,
    target_group_comparison: pd.DataFrame,
    family_comparison: pd.DataFrame,
    promotion_comparison: pd.DataFrame,
    family_promotion_comparison: pd.DataFrame,
    family_promotion_drift: pd.DataFrame,
    store_family_promotion_drift: pd.DataFrame,
    overweighted_regressions: pd.DataFrame,
) -> Path:
    report_path = output_dir / "stability_slice_report.md"
    mean_delta = validation_comparison["rmsle_delta"].mean()
    non_target = filter_non_target_family(family_comparison, target_family)
    worsened_non_target = non_target[non_target["rmsle_delta"] > 0].copy()
    improved_non_target = non_target[non_target["rmsle_delta"] < 0].copy()
    worst_promotion = promotion_comparison.sort_values("rmsle_delta", ascending=False).head(5)

    lines = [
        f"# Stability Slice Report: `{experiment_name}` vs `{baseline_name}`",
        "",
        "本报告用于解释 public-like 稳定性风险：一个 profile 即使 mean validation 更好，也可能在某些非目标切片或 test-like 分布上更差。",
        "",
        "## Overall Windows",
        "",
        dataframe_to_markdown(validation_comparison, max_rows=len(validation_comparison)),
        "",
        f"- Mean RMSLE delta: `{mean_delta:.6f}`.",
        "",
        "## Target vs Non-Target",
        "",
        dataframe_to_markdown(
            target_group_comparison[
                [
                    "target_group",
                    "baseline_row_count",
                    "baseline_rmsle",
                    "experiment_rmsle",
                    "rmsle_delta",
                    "baseline_mean_actual_sales",
                    "baseline_mean_predicted_sales",
                    "experiment_mean_predicted_sales",
                    "mean_predicted_sales_delta",
                ]
            ],
            max_rows=10,
        ),
        "",
        "## Non-Target Family Side Effects",
        "",
        f"- Non-target families worsened: `{len(worsened_non_target)}`.",
        f"- Non-target families improved: `{len(improved_non_target)}`.",
        "",
        "Top worsened non-target families:",
        "",
        dataframe_to_markdown(
            worsened_non_target[
                [
                    "family",
                    "baseline_row_count",
                    "baseline_rmsle",
                    "experiment_rmsle",
                    "rmsle_delta",
                    "baseline_mean_actual_sales",
                    "baseline_mean_predicted_sales",
                    "experiment_mean_predicted_sales",
                ]
            ].head(10),
            max_rows=10,
        ),
        "",
        "## Promotion Bin Stability",
        "",
        dataframe_to_markdown(
            worst_promotion[
                [
                    "promotion_bin",
                    "baseline_row_count",
                    "baseline_rmsle",
                    "experiment_rmsle",
                    "rmsle_delta",
                    "baseline_mean_onpromotion",
                    "experiment_mean_onpromotion",
                ]
            ],
            max_rows=5,
        ),
        "",
        "## Validation/Test Distribution Drift",
        "",
        "Top family-promotion share drift:",
        "",
        dataframe_to_markdown(family_promotion_drift.head(10), max_rows=10),
        "",
        "Overweighted non-target family-promotion regressions:",
        "",
        dataframe_to_markdown(
            overweighted_regressions[
                [
                    "family",
                    "promotion_bin",
                    "validation_rows",
                    "test_rows",
                    "test_minus_validation_share",
                    "rmsle_delta",
                    "baseline_rmsle",
                    "experiment_rmsle",
                ]
            ].head(10),
            max_rows=10,
        ),
        "",
        "Top store-family-promotion share drift:",
        "",
        dataframe_to_markdown(store_family_promotion_drift.head(10), max_rows=10),
        "",
        "## Interpretation",
        "",
    ]

    if not worsened_non_target.empty:
        lines.append(
            f"- `{experiment_name}` has non-target family regressions. This is a plausible reason why public score can worsen even when mean validation improves."
        )
    else:
        lines.append(
            "- No non-target family regression is visible in these validation windows, so the public mismatch is more likely tied to test distribution drift or unobserved public/private split effects."
        )

    lines.extend(
        [
            "- Distribution drift tables do not use `sales`; they only compare validation/test row composition by known fields.",
            "- A candidate profile should not be promoted only because mean RMSLE improves. It must also pass non-target slice and test-like distribution checks.",
            "",
            "## Generated Tables",
            "",
            "- `tables/validation_comparison.csv`",
            "- `tables/target_group_comparison.csv`",
            "- `tables/family_comparison.csv`",
            "- `tables/family_promotion_comparison.csv`",
            "- `tables/promotion_bin_comparison.csv`",
            "- `tables/family_promotion_drift.csv`",
            "- `tables/store_family_promotion_drift.csv`",
            "- `tables/overweighted_non_target_regressions.csv`",
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
    target_family: str,
    min_rows: int,
) -> Path:
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    baseline, experiment, baseline_summary, experiment_summary = load_comparable_predictions(
        baseline_artifacts_dir,
        experiment_artifacts_dir,
        data_dir,
    )
    baseline = add_target_flags(baseline, target_family)
    experiment = add_target_flags(experiment, target_family)
    test = load_test_context(data_dir)

    validation_comparison = summarize_validation_windows(baseline_summary, experiment_summary)
    validation_comparison.to_csv(tables_dir / "validation_comparison.csv", index=False)
    target_group_comparison = build_slice_comparison(
        baseline,
        experiment,
        ["target_group"],
        min_rows,
        tables_dir / "target_group_comparison.csv",
    )
    family_comparison = build_slice_comparison(
        baseline,
        experiment,
        ["family"],
        min_rows,
        tables_dir / "family_comparison.csv",
    )
    promotion_comparison = build_slice_comparison(
        baseline,
        experiment,
        ["promotion_bin"],
        min_rows,
        tables_dir / "promotion_bin_comparison.csv",
    )
    family_promotion_comparison = build_slice_comparison(
        baseline,
        experiment,
        ["family", "promotion_bin"],
        min_rows,
        tables_dir / "family_promotion_comparison.csv",
    )
    family_promotion_drift = build_distribution_drift(
        validation=baseline,
        test=test,
        group_columns=["family", "promotion_bin"],
        output_path=tables_dir / "family_promotion_drift.csv",
    )
    overweighted_regressions = build_overweighted_regressions(
        family_promotion_comparison=family_promotion_comparison,
        family_promotion_drift=family_promotion_drift,
        target_family=target_family,
        output_path=tables_dir / "overweighted_non_target_regressions.csv",
    )
    store_family_promotion_drift = build_distribution_drift(
        validation=baseline,
        test=test,
        group_columns=["store_nbr", "city", "store_type", "family", "promotion_bin"],
        output_path=tables_dir / "store_family_promotion_drift.csv",
    )
    return write_report(
        output_dir=output_dir,
        baseline_name=baseline_name,
        experiment_name=experiment_name,
        target_family=target_family,
        validation_comparison=validation_comparison,
        target_group_comparison=target_group_comparison,
        family_comparison=family_comparison,
        promotion_comparison=promotion_comparison,
        family_promotion_comparison=family_promotion_comparison,
        family_promotion_drift=family_promotion_drift,
        store_family_promotion_drift=store_family_promotion_drift,
        overweighted_regressions=overweighted_regressions,
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
        target_family=args.target_family,
        min_rows=args.min_rows,
    )
    print(f"Stability slice report: {report_path}")


if __name__ == "__main__":
    main()
