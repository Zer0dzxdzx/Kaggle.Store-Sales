from __future__ import annotations

import argparse
from dataclasses import dataclass
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


@dataclass(slots=True)
class FoldCrossPaths:
    output_dir: Path
    tables_dir: Path
    report_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate fold 3 cross-error diagnostics.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/fold3_cross_error"))
    parser.add_argument("--target-fold", type=int, default=3)
    parser.add_argument(
        "--min-fold-rows",
        type=int,
        default=4,
        help="Minimum target-fold rows required for a segment to appear in cross tables.",
    )
    return parser


def prepare_paths(output_dir: Path) -> FoldCrossPaths:
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    return FoldCrossPaths(
        output_dir=output_dir,
        tables_dir=tables_dir,
        report_path=output_dir / "fold3_cross_error_report.md",
    )


def summarize_segment(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    grouped = (
        frame.groupby(group_columns, dropna=False)
        .agg(
            row_count=("sales", "size"),
            squared_log_error_sum=("squared_log_error", "sum"),
            mean_abs_log_error=("abs_log_error", "mean"),
            actual_zero_rate=("actual_zero", "mean"),
            predicted_zero_rate=("predicted_zero", "mean"),
            mean_actual_sales=("sales", "mean"),
            mean_predicted_sales=("sales_pred", "mean"),
            total_actual_sales=("sales", "sum"),
            total_predicted_sales=("sales_pred", "sum"),
            mean_signed_error=("signed_error", "mean"),
            mean_onpromotion=("onpromotion", "mean"),
        )
        .reset_index()
    )
    grouped["msle"] = grouped["squared_log_error_sum"] / grouped["row_count"].clip(lower=1)
    grouped["rmsle"] = np.sqrt(grouped["msle"])
    return grouped


def prefix_metric_columns(frame: pd.DataFrame, group_columns: list[str], prefix: str) -> pd.DataFrame:
    rename_map = {column: f"{prefix}_{column}" for column in frame.columns if column not in group_columns}
    return frame.rename(columns=rename_map)


def compare_target_fold_to_prior(
    enriched: pd.DataFrame,
    group_columns: list[str],
    target_fold: int,
    min_fold_rows: int,
) -> pd.DataFrame:
    target_frame = enriched[enriched["fold_id"] == target_fold].copy()
    prior_frame = enriched[enriched["fold_id"] < target_fold].copy()
    if target_frame.empty:
        raise ValueError(f"No rows found for target fold {target_fold}.")
    if prior_frame.empty:
        raise ValueError(f"No prior fold rows found before target fold {target_fold}.")

    target = prefix_metric_columns(summarize_segment(target_frame, group_columns), group_columns, "fold3")
    prior = prefix_metric_columns(summarize_segment(prior_frame, group_columns), group_columns, "prior")
    comparison = target.merge(prior, on=group_columns, how="left")

    comparison = comparison[comparison["fold3_row_count"] >= min_fold_rows].copy()
    comparison["new_in_target_fold"] = comparison["prior_row_count"].isna()
    comparison["prior_row_count"] = comparison["prior_row_count"].fillna(0).astype("int64")
    comparison["msle_delta"] = comparison["fold3_msle"] - comparison["prior_msle"]
    comparison["rmsle_delta"] = comparison["fold3_rmsle"] - comparison["prior_rmsle"]

    target_total_rows = max(len(target_frame), 1)
    target_total_sse = max(float(target_frame["squared_log_error"].sum()), np.finfo(float).eps)
    prior_total_rows = max(len(prior_frame), 1)

    comparison["fold3_row_share"] = comparison["fold3_row_count"] / target_total_rows
    comparison["prior_row_share"] = comparison["prior_row_count"] / prior_total_rows
    comparison["fold3_error_share"] = comparison["fold3_squared_log_error_sum"] / target_total_sse
    comparison["positive_msle_delta_contribution"] = np.where(
        comparison["new_in_target_fold"],
        0.0,
        comparison["msle_delta"].clip(lower=0.0) * comparison["fold3_row_count"] / target_total_rows,
    )

    ordered_columns = (
        group_columns
        + [
            "fold3_row_count",
            "prior_row_count",
            "fold3_rmsle",
            "prior_rmsle",
            "rmsle_delta",
            "msle_delta",
            "positive_msle_delta_contribution",
            "fold3_error_share",
            "fold3_row_share",
            "prior_row_share",
            "new_in_target_fold",
            "fold3_actual_zero_rate",
            "fold3_mean_actual_sales",
            "fold3_mean_predicted_sales",
            "fold3_mean_signed_error",
            "fold3_mean_onpromotion",
        ]
    )
    return (
        comparison[ordered_columns]
        .sort_values(
            ["positive_msle_delta_contribution", "rmsle_delta", "fold3_error_share"],
            ascending=[False, False, False],
        )
        .reset_index(drop=True)
    )


def build_fold_trend(enriched: pd.DataFrame, target_fold: int, paths: FoldCrossPaths) -> pd.DataFrame:
    fold_trend = summarize_segment(enriched, ["fold_id"]).sort_values("fold_id").reset_index(drop=True)
    prior = fold_trend[fold_trend["fold_id"] < target_fold]
    prior_msle = np.average(prior["msle"], weights=prior["row_count"]) if not prior.empty else np.nan
    prior_rmsle = float(np.sqrt(prior_msle)) if not prior.empty else np.nan
    fold_trend["rmsle_delta_vs_prior_folds"] = fold_trend["rmsle"] - prior_rmsle
    fold_trend.to_csv(paths.tables_dir / "fold_trend.csv", index=False)
    return fold_trend


def write_cross_table(
    enriched: pd.DataFrame,
    group_columns: list[str],
    filename: str,
    target_fold: int,
    min_fold_rows: int,
    paths: FoldCrossPaths,
) -> pd.DataFrame:
    table = compare_target_fold_to_prior(
        enriched=enriched,
        group_columns=group_columns,
        target_fold=target_fold,
        min_fold_rows=min_fold_rows,
    )
    table.to_csv(paths.tables_dir / filename, index=False)
    return table


def write_new_segment_table(table: pd.DataFrame, filename: str, paths: FoldCrossPaths) -> pd.DataFrame:
    new_segments = (
        table[table["new_in_target_fold"]]
        .sort_values(["fold3_error_share", "fold3_rmsle"], ascending=[False, False])
        .reset_index(drop=True)
    )
    new_segments.to_csv(paths.tables_dir / filename, index=False)
    return new_segments


def top_value(table: pd.DataFrame, column: str) -> object:
    if table.empty:
        return ""
    return table.iloc[0][column]


def write_report(
    paths: FoldCrossPaths,
    target_fold: int,
    min_fold_rows: int,
    data_dir: Path,
    artifacts_dir: Path,
    fold_trend: pd.DataFrame,
    family: pd.DataFrame,
    store: pd.DataFrame,
    promotion: pd.DataFrame,
    family_store: pd.DataFrame,
    family_promotion: pd.DataFrame,
    store_promotion: pd.DataFrame,
    family_store_promotion: pd.DataFrame,
    new_family_promotion: pd.DataFrame,
    new_store_promotion: pd.DataFrame,
    new_family_store_promotion: pd.DataFrame,
) -> None:
    target_row = fold_trend[fold_trend["fold_id"] == target_fold].iloc[0]
    prior_rows = fold_trend[fold_trend["fold_id"] < target_fold]
    prior_msle = np.average(prior_rows["msle"], weights=prior_rows["row_count"])
    prior_rmsle = float(np.sqrt(prior_msle))

    family_columns = [
        "family",
        "fold3_rmsle",
        "prior_rmsle",
        "rmsle_delta",
        "positive_msle_delta_contribution",
        "fold3_mean_actual_sales",
        "fold3_mean_predicted_sales",
    ]
    store_columns = [
        "store_nbr",
        "city",
        "state",
        "store_type",
        "cluster",
        "fold3_rmsle",
        "prior_rmsle",
        "rmsle_delta",
        "positive_msle_delta_contribution",
    ]
    promotion_columns = [
        "promotion_bin",
        "fold3_rmsle",
        "prior_rmsle",
        "rmsle_delta",
        "positive_msle_delta_contribution",
        "fold3_row_share",
    ]
    family_store_columns = [
        "family",
        "store_nbr",
        "city",
        "store_type",
        "fold3_row_count",
        "fold3_rmsle",
        "prior_rmsle",
        "rmsle_delta",
        "positive_msle_delta_contribution",
    ]
    family_promotion_columns = [
        "family",
        "promotion_bin",
        "fold3_row_count",
        "fold3_rmsle",
        "prior_rmsle",
        "rmsle_delta",
        "positive_msle_delta_contribution",
    ]
    store_promotion_columns = [
        "store_nbr",
        "city",
        "store_type",
        "promotion_bin",
        "fold3_row_count",
        "fold3_rmsle",
        "prior_rmsle",
        "rmsle_delta",
        "positive_msle_delta_contribution",
    ]
    family_store_promotion_columns = [
        "family",
        "store_nbr",
        "city",
        "promotion_bin",
        "fold3_row_count",
        "fold3_rmsle",
        "prior_rmsle",
        "rmsle_delta",
        "positive_msle_delta_contribution",
    ]
    new_family_promotion_columns = [
        "family",
        "promotion_bin",
        "fold3_row_count",
        "fold3_rmsle",
        "fold3_error_share",
        "fold3_mean_actual_sales",
        "fold3_mean_predicted_sales",
    ]
    new_store_promotion_columns = [
        "store_nbr",
        "city",
        "store_type",
        "promotion_bin",
        "fold3_row_count",
        "fold3_rmsle",
        "fold3_error_share",
        "fold3_mean_actual_sales",
        "fold3_mean_predicted_sales",
    ]
    new_family_store_promotion_columns = [
        "family",
        "store_nbr",
        "city",
        "promotion_bin",
        "fold3_row_count",
        "fold3_rmsle",
        "fold3_error_share",
        "fold3_mean_actual_sales",
        "fold3_mean_predicted_sales",
    ]
    fold_trend_display = fold_trend[
        ["fold_id", "row_count", "rmsle", "rmsle_delta_vs_prior_folds", "mean_actual_sales", "mean_predicted_sales"]
    ].copy()
    fold_trend_display["fold_id"] = fold_trend_display["fold_id"].astype("int64").astype("string")
    fold_trend_display["row_count"] = fold_trend_display["row_count"].astype("int64").astype("string")

    lines = [
        "# Fold 3 Cross Error Analysis",
        "",
        "This report compares fold 3 against the pooled prior folds, using validation predictions only.",
        "It ranks segments by positive MSLE delta contribution, so it focuses on groups that became worse in fold 3.",
        "",
        "## Inputs",
        "",
        f"- Data directory: `{data_dir}`",
        f"- Artifacts directory: `{artifacts_dir}`",
        f"- Target fold: `{target_fold}`",
        f"- Minimum target-fold rows per reported segment: `{min_fold_rows}`",
        "",
        "## Key Findings",
        "",
        f"- Fold {target_fold} RMSLE is `{target_row['rmsle']:.6f}` versus prior folds RMSLE `{prior_rmsle:.6f}`.",
        f"- Largest family worsening contributor: `{top_value(family, 'family')}`.",
        f"- Largest store worsening contributor: store `{top_value(store, 'store_nbr')}`.",
        f"- Largest promotion-bin worsening contributor: `{top_value(promotion, 'promotion_bin')}`.",
        f"- Largest family-store worsening combination: `{top_value(family_store, 'family')}` at store `{top_value(family_store, 'store_nbr')}`.",
        f"- Largest family-promotion worsening combination: `{top_value(family_promotion, 'family')}` with promotion bin `{top_value(family_promotion, 'promotion_bin')}`.",
        f"- Largest new fold-{target_fold} family-store-promotion segment: `{top_value(new_family_store_promotion, 'family')}` at store `{top_value(new_family_store_promotion, 'store_nbr')}` with promotion bin `{top_value(new_family_store_promotion, 'promotion_bin')}`.",
        "",
        "## Fold Trend",
        "",
        dataframe_to_markdown(fold_trend_display, max_rows=len(fold_trend_display)),
        "",
        "## Family Worsening",
        "",
        dataframe_to_markdown(family[family_columns]),
        "",
        "## Store Worsening",
        "",
        dataframe_to_markdown(store[store_columns]),
        "",
        "## Promotion Bin Worsening",
        "",
        dataframe_to_markdown(promotion[promotion_columns], max_rows=len(promotion)),
        "",
        "## Family Store Worsening",
        "",
        dataframe_to_markdown(family_store[family_store_columns]),
        "",
        "## Family Promotion Worsening",
        "",
        dataframe_to_markdown(family_promotion[family_promotion_columns]),
        "",
        "## Store Promotion Worsening",
        "",
        dataframe_to_markdown(store_promotion[store_promotion_columns]),
        "",
        "## Family Store Promotion Worsening",
        "",
        dataframe_to_markdown(family_store_promotion[family_store_promotion_columns]),
        "",
        "## New Fold 3 Family Promotion Segments",
        "",
        "These segments appear in fold 3 but not in prior folds for the same exact grouping, so they are ranked by fold 3 error share rather than prior delta.",
        "",
        dataframe_to_markdown(new_family_promotion[new_family_promotion_columns]),
        "",
        "## New Fold 3 Store Promotion Segments",
        "",
        "These segments appear in fold 3 but not in prior folds for the same exact grouping.",
        "",
        dataframe_to_markdown(new_store_promotion[new_store_promotion_columns]),
        "",
        "## New Fold 3 Family Store Promotion Segments",
        "",
        "These fine-grained segments are noisy but useful for spotting fold 3 distribution changes.",
        "",
        dataframe_to_markdown(new_family_store_promotion[new_family_store_promotion_columns]),
        "",
        "## Generated Tables",
        "",
        "- `tables/fold_trend.csv`",
        "- `tables/fold3_family_worsening.csv`",
        "- `tables/fold3_store_worsening.csv`",
        "- `tables/fold3_promotion_bin_worsening.csv`",
        "- `tables/fold3_family_store_worsening.csv`",
        "- `tables/fold3_family_promotion_worsening.csv`",
        "- `tables/fold3_store_promotion_worsening.csv`",
        "- `tables/fold3_family_store_promotion_worsening.csv`",
        "- `tables/fold3_new_family_promotion_segments.csv`",
        "- `tables/fold3_new_store_promotion_segments.csv`",
        "- `tables/fold3_new_family_store_promotion_segments.csv`",
        "",
        "## Interpretation Limits",
        "",
        "- This is diagnostic, not causal proof.",
        "- Small combinations can be noisy even after the minimum row filter.",
        "- RMSLE is not additive, so contribution ranking uses MSLE delta as an approximate decomposition.",
        "- New fold 3 segments have no exact prior comparison and should be treated as distribution-shift clues.",
    ]
    paths.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_fold3_cross_error(
    data_dir: Path,
    artifacts_dir: Path,
    output_dir: Path,
    target_fold: int,
    min_fold_rows: int,
) -> FoldCrossPaths:
    paths = prepare_paths(output_dir)
    predictions = load_validation_predictions(artifacts_dir)
    validation_summary = load_validation_summary(artifacts_dir)
    validate_validation_summary(predictions, validation_summary)
    enriched = enrich_predictions(predictions, data_dir)

    fold_trend = build_fold_trend(enriched, target_fold, paths)
    family = write_cross_table(enriched, ["family"], "fold3_family_worsening.csv", target_fold, min_fold_rows, paths)
    store = write_cross_table(
        enriched,
        ["store_nbr", "city", "state", "store_type", "cluster"],
        "fold3_store_worsening.csv",
        target_fold,
        min_fold_rows,
        paths,
    )
    promotion = write_cross_table(
        enriched,
        ["promotion_bin"],
        "fold3_promotion_bin_worsening.csv",
        target_fold,
        min_fold_rows,
        paths,
    )
    family_store = write_cross_table(
        enriched,
        ["family", "store_nbr", "city", "state", "store_type", "cluster"],
        "fold3_family_store_worsening.csv",
        target_fold,
        min_fold_rows,
        paths,
    )
    family_promotion = write_cross_table(
        enriched,
        ["family", "promotion_bin"],
        "fold3_family_promotion_worsening.csv",
        target_fold,
        min_fold_rows,
        paths,
    )
    store_promotion = write_cross_table(
        enriched,
        ["store_nbr", "city", "state", "store_type", "cluster", "promotion_bin"],
        "fold3_store_promotion_worsening.csv",
        target_fold,
        min_fold_rows,
        paths,
    )
    family_store_promotion = write_cross_table(
        enriched,
        ["family", "store_nbr", "city", "state", "store_type", "cluster", "promotion_bin"],
        "fold3_family_store_promotion_worsening.csv",
        target_fold,
        min_fold_rows,
        paths,
    )
    new_family_promotion = write_new_segment_table(
        family_promotion,
        "fold3_new_family_promotion_segments.csv",
        paths,
    )
    new_store_promotion = write_new_segment_table(
        store_promotion,
        "fold3_new_store_promotion_segments.csv",
        paths,
    )
    new_family_store_promotion = write_new_segment_table(
        family_store_promotion,
        "fold3_new_family_store_promotion_segments.csv",
        paths,
    )

    write_report(
        paths=paths,
        target_fold=target_fold,
        min_fold_rows=min_fold_rows,
        data_dir=data_dir,
        artifacts_dir=artifacts_dir,
        fold_trend=fold_trend,
        family=family,
        store=store,
        promotion=promotion,
        family_store=family_store,
        family_promotion=family_promotion,
        store_promotion=store_promotion,
        family_store_promotion=family_store_promotion,
        new_family_promotion=new_family_promotion,
        new_store_promotion=new_store_promotion,
        new_family_store_promotion=new_family_store_promotion,
    )
    return paths


def main() -> None:
    args = build_parser().parse_args()
    paths = run_fold3_cross_error(
        data_dir=args.data_dir,
        artifacts_dir=args.artifacts_dir,
        output_dir=args.output_dir,
        target_fold=args.target_fold,
        min_fold_rows=args.min_fold_rows,
    )
    print(f"Fold cross-error report: {paths.report_path}")
    print(f"Tables: {paths.tables_dir}")


if __name__ == "__main__":
    main()
