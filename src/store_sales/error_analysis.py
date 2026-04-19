from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


PROMOTION_BINS = [-1, 0, 1, 5, 10, 50, np.inf]
PROMOTION_LABELS = ["0", "1", "2-5", "6-10", "11-50", "51+"]


@dataclass(slots=True)
class ErrorAnalysisPaths:
    output_dir: Path
    tables_dir: Path
    report_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate grouped error analysis for Store Sales validation folds.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/error_analysis"))
    return parser


def prepare_paths(output_dir: Path) -> ErrorAnalysisPaths:
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    return ErrorAnalysisPaths(
        output_dir=output_dir,
        tables_dir=tables_dir,
        report_path=output_dir / "error_analysis_report.md",
    )


def extract_fold_id(path: Path) -> int:
    match = re.search(r"fold_(\d+)", path.stem)
    if not match:
        raise ValueError(f"Could not extract fold id from {path}.")
    return int(match.group(1))


def load_validation_predictions(artifacts_dir: Path) -> pd.DataFrame:
    fold_paths = sorted(artifacts_dir.glob("validation_predictions_fold_*.csv"))
    if not fold_paths:
        raise FileNotFoundError(
            f"No validation fold predictions found in {artifacts_dir}. "
            "Run the baseline with --validation-windows first."
        )

    frames = []
    for path in fold_paths:
        frame = pd.read_csv(path, parse_dates=["date"])
        frame["fold_id"] = extract_fold_id(path)
        frames.append(frame)
    predictions = pd.concat(frames, ignore_index=True)
    predictions.attrs["source_files"] = [str(path) for path in fold_paths]
    required_columns = {"date", "store_nbr", "family", "sales", "sales_pred", "fold_id"}
    missing = required_columns.difference(predictions.columns)
    if missing:
        raise ValueError(f"Validation predictions are missing columns: {sorted(missing)}")
    return predictions


def load_validation_summary(artifacts_dir: Path) -> pd.DataFrame:
    summary_path = artifacts_dir / "validation_summary.csv"
    if not summary_path.exists():
        return pd.DataFrame(columns=["fold_id", "validation_start", "validation_end", "validation_rmsle"])
    return pd.read_csv(summary_path)


def validate_validation_summary(predictions: pd.DataFrame, validation_summary: pd.DataFrame) -> None:
    if validation_summary.empty:
        return

    prediction_fold_ids = set(predictions["fold_id"].unique())
    summary_fold_ids = set(validation_summary["fold_id"].unique())
    if prediction_fold_ids != summary_fold_ids:
        raise ValueError(
            "Validation prediction folds do not match validation_summary.csv folds: "
            f"predictions={sorted(prediction_fold_ids)}, summary={sorted(summary_fold_ids)}"
        )

    if "validation_rows" not in validation_summary.columns:
        return

    prediction_counts = predictions.groupby("fold_id").size().rename("prediction_rows").reset_index()
    row_check = validation_summary[["fold_id", "validation_rows"]].merge(prediction_counts, on="fold_id", how="inner")
    mismatched = row_check[row_check["validation_rows"] != row_check["prediction_rows"]]
    if not mismatched.empty:
        raise ValueError(f"Validation row counts do not match prediction files:\n{mismatched.to_string(index=False)}")


def load_context(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(
        data_dir / "train.csv",
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
    return train, stores


def enrich_predictions(predictions: pd.DataFrame, data_dir: Path) -> pd.DataFrame:
    train, stores = load_context(data_dir)
    enriched = predictions.merge(train, on=["date", "store_nbr", "family"], how="left")
    enriched = enriched.merge(stores, on="store_nbr", how="left")
    enriched["onpromotion"] = enriched["onpromotion"].fillna(0).astype("int16")
    enriched["promotion_bin"] = pd.cut(
        enriched["onpromotion"],
        bins=PROMOTION_BINS,
        labels=PROMOTION_LABELS,
    ).astype("string")

    actual = np.clip(enriched["sales"].to_numpy(dtype=float), 0.0, None)
    predicted = np.clip(enriched["sales_pred"].to_numpy(dtype=float), 0.0, None)
    log_error = np.log1p(predicted) - np.log1p(actual)

    enriched["actual_zero"] = actual == 0.0
    enriched["predicted_zero"] = predicted == 0.0
    enriched["signed_error"] = predicted - actual
    enriched["abs_log_error"] = np.abs(log_error)
    enriched["squared_log_error"] = np.square(log_error)
    return enriched


def summarize_errors(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    grouped = (
        frame.groupby(group_columns, dropna=False)
        .agg(
            row_count=("sales", "size"),
            rmsle_numerator=("squared_log_error", "mean"),
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
    grouped["rmsle"] = np.sqrt(grouped["rmsle_numerator"])
    grouped = grouped.drop(columns=["rmsle_numerator"])

    ordered_columns = (
        group_columns
        + [
            "row_count",
            "rmsle",
            "mean_abs_log_error",
            "actual_zero_rate",
            "predicted_zero_rate",
            "mean_actual_sales",
            "mean_predicted_sales",
            "total_actual_sales",
            "total_predicted_sales",
            "mean_signed_error",
            "mean_onpromotion",
        ]
    )
    return grouped[ordered_columns].sort_values("rmsle", ascending=False).reset_index(drop=True)


def build_family_error(enriched: pd.DataFrame, paths: ErrorAnalysisPaths) -> pd.DataFrame:
    family_error = summarize_errors(enriched, ["family"])
    family_error.to_csv(paths.tables_dir / "family_error.csv", index=False)
    return family_error


def build_store_error(enriched: pd.DataFrame, paths: ErrorAnalysisPaths) -> pd.DataFrame:
    store_error = summarize_errors(enriched, ["store_nbr", "city", "state", "store_type", "cluster"])
    store_error.to_csv(paths.tables_dir / "store_error.csv", index=False)
    return store_error


def build_promotion_error(enriched: pd.DataFrame, paths: ErrorAnalysisPaths) -> pd.DataFrame:
    promotion_error = summarize_errors(enriched, ["promotion_bin"])
    promotion_error["promotion_bin"] = pd.Categorical(
        promotion_error["promotion_bin"],
        categories=PROMOTION_LABELS,
        ordered=True,
    )
    promotion_error = promotion_error.sort_values("promotion_bin").reset_index(drop=True)
    promotion_error["promotion_bin"] = promotion_error["promotion_bin"].astype("string")
    promotion_error.to_csv(paths.tables_dir / "promotion_bin_error.csv", index=False)
    return promotion_error


def build_fold_comparison(
    enriched: pd.DataFrame,
    validation_summary: pd.DataFrame,
    paths: ErrorAnalysisPaths,
) -> pd.DataFrame:
    fold_comparison = summarize_errors(enriched, ["fold_id"]).sort_values("fold_id").reset_index(drop=True)
    if not validation_summary.empty:
        fold_comparison = fold_comparison.merge(
            validation_summary[["fold_id", "validation_start", "validation_end", "validation_rmsle"]],
            on="fold_id",
            how="left",
        )
    fold_comparison["rmsle_delta_vs_previous_fold"] = fold_comparison["rmsle"].diff()
    fold_comparison.to_csv(paths.tables_dir / "fold_comparison.csv", index=False)
    return fold_comparison


def dataframe_to_markdown(frame: pd.DataFrame, max_rows: int = 10) -> str:
    display = frame.head(max_rows).copy()
    headers = [str(column) for column in display.columns]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in display.iterrows():
        values = []
        for value in row:
            if pd.isna(value):
                values.append("")
            elif isinstance(value, float):
                values.append(f"{value:.6f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def write_report(
    paths: ErrorAnalysisPaths,
    family_error: pd.DataFrame,
    store_error: pd.DataFrame,
    promotion_error: pd.DataFrame,
    fold_comparison: pd.DataFrame,
    data_dir: Path,
    artifacts_dir: Path,
    prediction_files: list[str],
) -> None:
    family_columns = ["family", "row_count", "rmsle", "actual_zero_rate", "mean_actual_sales", "mean_predicted_sales"]
    store_columns = [
        "store_nbr",
        "city",
        "state",
        "store_type",
        "cluster",
        "row_count",
        "rmsle",
        "mean_actual_sales",
        "mean_predicted_sales",
    ]
    promotion_columns = [
        "promotion_bin",
        "row_count",
        "rmsle",
        "mean_actual_sales",
        "mean_predicted_sales",
        "mean_onpromotion",
    ]
    fold_columns = [
        "fold_id",
        "validation_start",
        "validation_end",
        "row_count",
        "rmsle",
        "rmsle_delta_vs_previous_fold",
        "mean_actual_sales",
        "mean_predicted_sales",
    ]
    fold_columns = [column for column in fold_columns if column in fold_comparison.columns]

    top_family = family_error.iloc[0]
    top_store = store_error.iloc[0]
    worst_promo = promotion_error.sort_values("rmsle", ascending=False).iloc[0]

    lines = [
        "# Store Sales Error Analysis",
        "",
        "This report uses validation fold predictions only. It is for local diagnosis, not Kaggle leaderboard scoring.",
        "Family, store, and promotion-bin errors are pooled across all validation folds unless stated otherwise.",
        "",
        "## Key Findings",
        "",
        f"- Worst family by RMSLE: `{top_family['family']}` with RMSLE `{top_family['rmsle']:.6f}`.",
        f"- Worst store by RMSLE: store `{int(top_store['store_nbr'])}` with RMSLE `{top_store['rmsle']:.6f}`.",
        f"- Worst promotion bin by RMSLE: `{worst_promo['promotion_bin']}` with RMSLE `{worst_promo['rmsle']:.6f}`.",
        "- Fold comparison is fold-level only; it shows trend by validation window, not segment-level causes.",
        "",
        "## Inputs",
        "",
        f"- Data directory: `{data_dir}`",
        f"- Artifacts directory: `{artifacts_dir}`",
        f"- Prediction files: `{', '.join(prediction_files)}`",
        "",
        "## Family Error",
        "",
        dataframe_to_markdown(family_error[family_columns]),
        "",
        "## Store Error",
        "",
        dataframe_to_markdown(store_error[store_columns]),
        "",
        "## Promotion Bin Error",
        "",
        dataframe_to_markdown(promotion_error[promotion_columns], max_rows=len(promotion_error)),
        "",
        "## Fold Comparison",
        "",
        dataframe_to_markdown(fold_comparison[fold_columns], max_rows=len(fold_comparison)),
        "",
        "## Generated Tables",
        "",
        "- `tables/family_error.csv`",
        "- `tables/store_error.csv`",
        "- `tables/promotion_bin_error.csv`",
        "- `tables/fold_comparison.csv`",
        "",
        "## Questions To Answer",
        "",
        "1. Are the worst family errors concentrated in high zero-sales families?",
        "2. Are store errors concentrated in a specific city, state, store type, or cluster?",
        "3. Does high promotion intensity have higher RMSLE than low promotion bins?",
        "4. Does fold 3 have worse fold-level RMSLE than fold 1/2?",
    ]
    paths.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_error_analysis(data_dir: Path, artifacts_dir: Path, output_dir: Path) -> ErrorAnalysisPaths:
    paths = prepare_paths(output_dir)
    predictions = load_validation_predictions(artifacts_dir)
    validation_summary = load_validation_summary(artifacts_dir)
    validate_validation_summary(predictions, validation_summary)
    enriched = enrich_predictions(predictions, data_dir)

    family_error = build_family_error(enriched, paths)
    store_error = build_store_error(enriched, paths)
    promotion_error = build_promotion_error(enriched, paths)
    fold_comparison = build_fold_comparison(enriched, validation_summary, paths)
    prediction_files = predictions.attrs.get("source_files", [])
    write_report(
        paths,
        family_error,
        store_error,
        promotion_error,
        fold_comparison,
        data_dir,
        artifacts_dir,
        prediction_files,
    )
    return paths


def main() -> None:
    args = build_parser().parse_args()
    paths = run_error_analysis(
        data_dir=args.data_dir,
        artifacts_dir=args.artifacts_dir,
        output_dir=args.output_dir,
    )
    print(f"Error analysis report: {paths.report_path}")
    print(f"Tables: {paths.tables_dir}")


if __name__ == "__main__":
    main()
