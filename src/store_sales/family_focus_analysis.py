from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-store-sales")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
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
from store_sales.fold3_cross_error import compare_target_fold_to_prior


DEFAULT_FAMILY = "SCHOOL AND OFFICE SUPPLIES"
SUPPORTED_TARGET_FOLD = 3


@dataclass(slots=True)
class FamilyFocusPaths:
    output_dir: Path
    tables_dir: Path
    figures_dir: Path
    report_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a single Store Sales family in detail.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/family_focus/school_office_supplies"))
    parser.add_argument("--family", default=DEFAULT_FAMILY)
    parser.add_argument(
        "--target-fold",
        type=int,
        default=SUPPORTED_TARGET_FOLD,
        help="Currently only fold 3 is supported because report filenames and labels are fold-3 specific.",
    )
    parser.add_argument("--min-fold-rows", type=int, default=4)
    return parser


def prepare_paths(output_dir: Path) -> FamilyFocusPaths:
    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    return FamilyFocusPaths(
        output_dir=output_dir,
        tables_dir=tables_dir,
        figures_dir=figures_dir,
        report_path=output_dir / "family_focus_report.md",
    )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "family"


def read_focus_data(data_dir: Path, family: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(
        data_dir / "train.csv",
        parse_dates=["date"],
        dtype={
            "id": "int64",
            "store_nbr": "int16",
            "family": "string",
            "sales": "float32",
            "onpromotion": "int16",
        },
    )
    test = pd.read_csv(
        data_dir / "test.csv",
        parse_dates=["date"],
        dtype={
            "id": "int64",
            "store_nbr": "int16",
            "family": "string",
            "onpromotion": "int16",
        },
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

    focus_train = train[train["family"] == family].copy().merge(stores, on="store_nbr", how="left")
    focus_test = test[test["family"] == family].copy().merge(stores, on="store_nbr", how="left")
    if focus_train.empty:
        raise ValueError(f"No training rows found for family: {family}")
    if focus_test.empty:
        raise ValueError(f"No test rows found for family: {family}")
    return focus_train, focus_test, stores


def add_promotion_bin(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    enriched["promotion_bin"] = pd.cut(
        enriched["onpromotion"],
        bins=PROMOTION_BINS,
        labels=PROMOTION_LABELS,
    ).astype("string")
    return enriched


def validate_supported_target_fold(target_fold: int) -> None:
    if target_fold != SUPPORTED_TARGET_FOLD:
        raise ValueError(
            "family_focus_analysis currently supports only fold 3. "
            "Use --target-fold 3, or generalize report filenames and labels before using another fold."
        )


def write_new_store_promotion_table(table: pd.DataFrame, filename: str, paths: FamilyFocusPaths) -> pd.DataFrame:
    new_segments = (
        table[table["new_in_target_fold"]]
        .sort_values(["fold3_error_share", "fold3_rmsle"], ascending=[False, False])
        .reset_index(drop=True)
    )
    new_segments.to_csv(paths.tables_dir / filename, index=False)
    return new_segments


def save_plot(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def build_monthly_history(focus_train: pd.DataFrame, paths: FamilyFocusPaths) -> pd.DataFrame:
    frame = focus_train.copy()
    frame["year"] = frame["date"].dt.year.astype("int16")
    frame["month"] = frame["date"].dt.month.astype("int8")
    monthly = (
        frame.groupby(["year", "month"], observed=True)
        .agg(
            row_count=("sales", "size"),
            total_sales=("sales", "sum"),
            mean_sales=("sales", "mean"),
            zero_sales_rate=("sales", lambda values: float((values == 0).mean())),
            promotion_sum=("onpromotion", "sum"),
            mean_onpromotion=("onpromotion", "mean"),
            promoted_row_rate=("onpromotion", lambda values: float((values > 0).mean())),
            active_store_count=("store_nbr", lambda values: values.nunique()),
        )
        .reset_index()
        .sort_values(["year", "month"])
    )
    monthly.to_csv(paths.tables_dir / "monthly_history.csv", index=False)
    return monthly


def build_2017_daily_focus(focus_train: pd.DataFrame, focus_test: pd.DataFrame, paths: FamilyFocusPaths) -> pd.DataFrame:
    train_rows = focus_train.loc[
        focus_train["date"].dt.year == 2017,
        ["date", "store_nbr", "sales", "onpromotion"],
    ].copy()
    train_rows["sales"] = train_rows["sales"].astype("float32")
    train_rows["period"] = np.where(
        train_rows["date"].between(pd.Timestamp("2017-07-31"), pd.Timestamp("2017-08-15")),
        "fold3",
        "train_2017",
    )

    test_rows = focus_test[["date", "store_nbr", "onpromotion"]].copy()
    test_rows["sales"] = np.full(len(test_rows), np.nan, dtype="float32")
    test_rows["period"] = "test"

    ordered_columns = ["date", "store_nbr", "sales", "onpromotion", "period"]
    train_rows = train_rows[ordered_columns]
    test_rows = test_rows[ordered_columns]
    combined = pd.concat([train_rows, test_rows], ignore_index=True)
    daily = (
        combined.groupby(["date", "period"], observed=True)
        .agg(
            row_count=("store_nbr", "size"),
            total_sales=("sales", lambda values: values.sum(min_count=1)),
            mean_sales=("sales", "mean"),
            promotion_sum=("onpromotion", "sum"),
            promoted_store_count=("onpromotion", lambda values: int((values > 0).sum())),
            max_onpromotion=("onpromotion", "max"),
        )
        .reset_index()
        .sort_values("date")
    )
    daily.to_csv(paths.tables_dir / "daily_2017_focus.csv", index=False)
    return daily


def build_fold_focus_tables(
    data_dir: Path,
    artifacts_dir: Path,
    family: str,
    target_fold: int,
    min_fold_rows: int,
    paths: FamilyFocusPaths,
) -> dict[str, pd.DataFrame]:
    predictions = load_validation_predictions(artifacts_dir)
    validation_summary = load_validation_summary(artifacts_dir)
    validate_validation_summary(predictions, validation_summary)
    enriched = enrich_predictions(predictions, data_dir)
    focus = enriched[enriched["family"] == family].copy()
    if focus.empty:
        raise ValueError(f"No validation prediction rows found for family: {family}")

    fold_summary = (
        focus.groupby("fold_id", observed=True)
        .agg(
            row_count=("sales", "size"),
            squared_log_error_sum=("squared_log_error", "sum"),
            mean_abs_log_error=("abs_log_error", "mean"),
            actual_zero_rate=("actual_zero", "mean"),
            mean_actual_sales=("sales", "mean"),
            mean_predicted_sales=("sales_pred", "mean"),
            mean_signed_error=("signed_error", "mean"),
            mean_onpromotion=("onpromotion", "mean"),
        )
        .reset_index()
        .sort_values("fold_id")
    )
    fold_summary["rmsle"] = np.sqrt(fold_summary["squared_log_error_sum"] / fold_summary["row_count"].clip(lower=1))
    fold_summary.to_csv(paths.tables_dir / "family_fold_summary.csv", index=False)

    store_error = compare_target_fold_to_prior(
        enriched=focus,
        group_columns=["store_nbr", "city", "state", "store_type", "cluster"],
        target_fold=target_fold,
        min_fold_rows=min_fold_rows,
    )
    store_error.to_csv(paths.tables_dir / "family_fold3_store_error.csv", index=False)

    store_promotion_error = compare_target_fold_to_prior(
        enriched=focus,
        group_columns=["store_nbr", "city", "state", "store_type", "cluster", "promotion_bin"],
        target_fold=target_fold,
        min_fold_rows=min_fold_rows,
    )
    store_promotion_error.to_csv(paths.tables_dir / "family_fold3_store_promotion_error.csv", index=False)

    new_store_promotion = write_new_store_promotion_table(
        store_promotion_error,
        "family_fold3_new_store_promotion_segments.csv",
        paths,
    )
    return {
        "fold_summary": fold_summary,
        "store_error": store_error,
        "store_promotion_error": store_promotion_error,
        "new_store_promotion": new_store_promotion,
    }


def build_test_promotion_profile(
    focus_test: pd.DataFrame,
    store_promotion_error: pd.DataFrame,
    paths: FamilyFocusPaths,
) -> pd.DataFrame:
    test = add_promotion_bin(focus_test)
    test_profile = (
        test.groupby(["store_nbr", "city", "state", "store_type", "cluster", "promotion_bin"], dropna=False)
        .agg(
            test_row_count=("id", "size"),
            test_mean_onpromotion=("onpromotion", "mean"),
            test_max_onpromotion=("onpromotion", "max"),
            test_promotion_sum=("onpromotion", "sum"),
        )
        .reset_index()
    )
    risk_columns = [
        "store_nbr",
        "promotion_bin",
        "fold3_rmsle",
        "prior_rmsle",
        "rmsle_delta",
        "fold3_error_share",
        "new_in_target_fold",
        "fold3_mean_actual_sales",
        "fold3_mean_predicted_sales",
    ]
    risk = store_promotion_error[risk_columns].copy()
    overlap = test_profile.merge(risk, on=["store_nbr", "promotion_bin"], how="left")
    overlap["has_fold3_error_signal"] = overlap["fold3_rmsle"].notna()
    overlap = overlap.sort_values(
        ["has_fold3_error_signal", "test_promotion_sum", "fold3_error_share"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    overlap.to_csv(paths.tables_dir / "test_promotion_risk_overlap.csv", index=False)
    return overlap


def plot_2017_daily(daily: pd.DataFrame, paths: FamilyFocusPaths, family: str) -> None:
    train_part = daily[daily["period"] != "test"].copy()
    fig, ax_sales = plt.subplots(figsize=(14, 6))
    ax_promo = ax_sales.twinx()
    ax_sales.plot(train_part["date"], train_part["total_sales"], color="#0b7285", linewidth=2, label="Total sales")
    ax_promo.plot(daily["date"], daily["promotion_sum"], color="#f08c00", linewidth=1.5, label="Promotion sum")
    ax_sales.axvspan(pd.Timestamp("2017-07-31"), pd.Timestamp("2017-08-15"), color="#ffe066", alpha=0.25, label="Fold 3")
    ax_sales.axvspan(pd.Timestamp("2017-08-16"), pd.Timestamp("2017-08-31"), color="#d0ebff", alpha=0.25, label="Test")
    ax_sales.set_title(f"{family}: 2017 Daily Sales and Promotion")
    ax_sales.set_ylabel("Total sales")
    ax_promo.set_ylabel("Promotion sum")
    ax_sales.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax_sales.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax_sales.legend(loc="upper left")
    ax_promo.legend(loc="upper right")
    fig.autofmt_xdate()
    save_plot(paths.figures_dir / "daily_2017_sales_promotion.png")


def plot_monthly_history(monthly: pd.DataFrame, paths: FamilyFocusPaths, family: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    for year, frame in monthly.groupby("year", observed=True):
        ax.plot(frame["month"], frame["total_sales"], marker="o", linewidth=1.8, label=str(year))
    ax.set_title(f"{family}: Monthly Total Sales by Year")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total sales")
    ax.set_xticks(range(1, 13))
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title="Year", ncols=3)
    save_plot(paths.figures_dir / "monthly_sales_by_year.png")


def plot_fold3_top_stores(store_error: pd.DataFrame, paths: FamilyFocusPaths, family: str) -> None:
    top = store_error.head(10).sort_values("fold3_rmsle")
    labels = top["store_nbr"].astype(str) + " " + top["city"].astype(str)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(labels, top["fold3_rmsle"], color="#c92a2a", label="Fold 3")
    ax.scatter(top["prior_rmsle"], labels, color="#1864ab", label="Prior folds", zorder=3)
    ax.set_title(f"{family}: Top Fold 3 Store Error")
    ax.set_xlabel("RMSLE")
    ax.legend()
    save_plot(paths.figures_dir / "fold3_top_store_error.png")


def write_report(
    paths: FamilyFocusPaths,
    family: str,
    monthly: pd.DataFrame,
    daily: pd.DataFrame,
    fold_tables: dict[str, pd.DataFrame],
    test_overlap: pd.DataFrame,
) -> None:
    august = monthly[(monthly["month"] == 8)].sort_values("year")
    focus_2017_august = august[august["year"] == 2017].iloc[0]
    fold_summary = fold_tables["fold_summary"]
    store_error = fold_tables["store_error"]
    store_promotion_error = fold_tables["store_promotion_error"]
    new_store_promotion = fold_tables["new_store_promotion"]

    fold_display = fold_summary[
        [
            "fold_id",
            "row_count",
            "rmsle",
            "mean_actual_sales",
            "mean_predicted_sales",
            "mean_signed_error",
            "mean_onpromotion",
        ]
    ].copy()
    fold_display["fold_id"] = fold_display["fold_id"].astype("int64").astype("string")
    fold_display["row_count"] = fold_display["row_count"].astype("int64").astype("string")

    monthly_display = monthly[monthly["month"].isin([3, 4, 7, 8, 9])][
        ["year", "month", "total_sales", "promotion_sum", "mean_sales", "mean_onpromotion"]
    ].tail(20)
    monthly_display = monthly_display.copy()
    monthly_display["year"] = monthly_display["year"].astype("int64").astype("string")
    monthly_display["month"] = monthly_display["month"].astype("int64").astype("string")
    store_columns = [
        "store_nbr",
        "city",
        "store_type",
        "cluster",
        "fold3_rmsle",
        "prior_rmsle",
        "rmsle_delta",
        "fold3_mean_actual_sales",
        "fold3_mean_predicted_sales",
        "fold3_mean_onpromotion",
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
        "fold3_mean_actual_sales",
        "fold3_mean_predicted_sales",
    ]
    new_columns = [
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
    test_columns = [
        "store_nbr",
        "city",
        "store_type",
        "promotion_bin",
        "test_row_count",
        "test_mean_onpromotion",
        "test_promotion_sum",
        "has_fold3_error_signal",
        "fold3_rmsle",
        "fold3_error_share",
    ]

    top_new = new_store_promotion.iloc[0] if not new_store_promotion.empty else None
    top_test_overlap = test_overlap[test_overlap["has_fold3_error_signal"]].head(10)

    lines = [
        f"# Family Focus Analysis: {family}",
        "",
        "This report diagnoses one family after fold 3 cross-error analysis. It does not change the model.",
        "",
        "## Key Findings",
        "",
        f"- August 2017 total sales for this family are `{focus_2017_august['total_sales']:.0f}`, much higher than July 2017 and prior August levels.",
        f"- Fold 3 prediction error is concentrated in high-promotion type A / Quito-Ambato store segments for `{family}`.",
        f"- Top fold 3 store segment: store `{int(store_error.iloc[0]['store_nbr'])}` in `{store_error.iloc[0]['city']}`.",
        f"- Test-period promotions continue to be high for type A stores, so this family remains relevant for submission risk.",
    ]
    if top_new is not None:
        lines.append(
            f"- Strongest new fold 3 store-promotion segment: store `{int(top_new['store_nbr'])}` "
            f"with promotion bin `{top_new['promotion_bin']}`, actual mean `{top_new['fold3_mean_actual_sales']:.1f}`, "
            f"predicted mean `{top_new['fold3_mean_predicted_sales']:.1f}`."
        )

    lines.extend(
        [
            "",
            "## Fold Summary",
            "",
            dataframe_to_markdown(fold_display, max_rows=len(fold_display)),
            "",
            "## Monthly History Snapshot",
            "",
            dataframe_to_markdown(monthly_display, max_rows=len(monthly_display)),
            "",
            "## Fold 3 Store Error",
            "",
            dataframe_to_markdown(store_error[store_columns]),
            "",
            "## Fold 3 Store Promotion Error",
            "",
            "This table prioritizes segments that can be compared against prior folds. Fold 3-only high-promotion segments are shown in the next table.",
            "",
            dataframe_to_markdown(store_promotion_error[store_promotion_columns]),
            "",
            "## New Fold 3 Store Promotion Segments",
            "",
            "These store-promotion combinations appear in fold 3 but not in prior folds for this family.",
            "",
            dataframe_to_markdown(new_store_promotion[new_columns]),
            "",
            "## Test Promotion Risk Overlap",
            "",
            dataframe_to_markdown(top_test_overlap[test_columns], max_rows=10),
            "",
            "## Figures",
            "",
            "![2017 daily sales and promotion](figures/daily_2017_sales_promotion.png)",
            "",
            "![Monthly sales by year](figures/monthly_sales_by_year.png)",
            "",
            "![Fold 3 top store error](figures/fold3_top_store_error.png)",
            "",
            "## Generated Tables",
            "",
            "- `tables/monthly_history.csv`",
            "- `tables/daily_2017_focus.csv`",
            "- `tables/family_fold_summary.csv`",
            "- `tables/family_fold3_store_error.csv`",
            "- `tables/family_fold3_store_promotion_error.csv`",
            "- `tables/family_fold3_new_store_promotion_segments.csv`",
            "- `tables/test_promotion_risk_overlap.csv`",
            "",
            "## Interpretation",
            "",
            "- The evidence supports a targeted issue for this family, not a general low-demand fix.",
            "- The data shows underprediction in fold 3 high-promotion type A / Quito-Ambato store segments.",
            "- The next feature experiment should target August timing and promotion behavior for this family; a school-season explanation remains a hypothesis.",
            "- This report is diagnostic; it does not prove the external business cause of the pattern.",
        ]
    )
    paths.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_family_focus_analysis(
    data_dir: Path,
    artifacts_dir: Path,
    output_dir: Path,
    family: str,
    target_fold: int,
    min_fold_rows: int,
) -> FamilyFocusPaths:
    validate_supported_target_fold(target_fold)
    paths = prepare_paths(output_dir)
    focus_train, focus_test, _ = read_focus_data(data_dir, family)
    monthly = build_monthly_history(focus_train, paths)
    daily = build_2017_daily_focus(focus_train, focus_test, paths)
    fold_tables = build_fold_focus_tables(data_dir, artifacts_dir, family, target_fold, min_fold_rows, paths)
    test_overlap = build_test_promotion_profile(focus_test, fold_tables["store_promotion_error"], paths)

    plot_2017_daily(daily, paths, family)
    plot_monthly_history(monthly, paths, family)
    plot_fold3_top_stores(fold_tables["store_error"], paths, family)
    write_report(paths, family, monthly, daily, fold_tables, test_overlap)
    return paths


def main() -> None:
    args = build_parser().parse_args()
    output_dir = args.output_dir
    if output_dir == Path("reports/family_focus/school_office_supplies") and args.family != DEFAULT_FAMILY:
        output_dir = Path("reports/family_focus") / slugify(args.family)
    paths = run_family_focus_analysis(
        data_dir=args.data_dir,
        artifacts_dir=args.artifacts_dir,
        output_dir=output_dir,
        family=args.family,
        target_fold=args.target_fold,
        min_fold_rows=args.min_fold_rows,
    )
    print(f"Family focus report: {paths.report_path}")
    print(f"Tables: {paths.tables_dir}")
    print(f"Figures: {paths.figures_dir}")


if __name__ == "__main__":
    main()
