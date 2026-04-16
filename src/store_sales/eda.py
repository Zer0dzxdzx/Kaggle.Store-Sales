from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-store-sales")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass(slots=True)
class EdaPaths:
    output_dir: Path
    figures_dir: Path
    tables_dir: Path
    report_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate EDA report for Kaggle Store Sales data.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/eda"))
    parser.add_argument("--validation-summary", type=Path, default=Path("artifacts/validation_summary.csv"))
    return parser


def prepare_paths(output_dir: Path) -> EdaPaths:
    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    return EdaPaths(
        output_dir=output_dir,
        figures_dir=figures_dir,
        tables_dir=tables_dir,
        report_path=output_dir / "eda_report.md",
    )


def read_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    train = pd.read_csv(
        data_dir / "train.csv",
        parse_dates=["date"],
        dtype={
            "id": "int64",
            "store_nbr": "int16",
            "family": "category",
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
            "family": "category",
            "onpromotion": "int16",
        },
    )
    stores = pd.read_csv(
        data_dir / "stores.csv",
        dtype={
            "store_nbr": "int16",
            "city": "category",
            "state": "category",
            "type": "category",
            "cluster": "int16",
        },
    )
    oil = pd.read_csv(data_dir / "oil.csv", parse_dates=["date"], dtype={"dcoilwtico": "float32"})
    holidays = pd.read_csv(
        data_dir / "holidays_events.csv",
        parse_dates=["date"],
        dtype={
            "type": "category",
            "locale": "category",
            "locale_name": "category",
            "description": "category",
            "transferred": "bool",
        },
    )
    transactions_path = data_dir / "transactions.csv"
    transactions = None
    if transactions_path.exists():
        transactions = pd.read_csv(
            transactions_path,
            parse_dates=["date"],
            dtype={"store_nbr": "int16", "transactions": "float32"},
        )

    return {
        "train": train,
        "test": test,
        "stores": stores,
        "oil": oil,
        "holidays": holidays,
        "transactions": transactions,
    }


def save_plot(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def format_number(value: float | int) -> str:
    if pd.isna(value):
        return ""
    return f"{value:,.4f}" if isinstance(value, float) else f"{value:,}"


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in frame.iterrows():
        values = []
        for value in row:
            if isinstance(value, float):
                values.append(f"{value:,.4f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def create_overview_table(data: dict[str, pd.DataFrame], paths: EdaPaths) -> pd.DataFrame:
    train = data["train"]
    test = data["test"]
    transactions = data["transactions"]

    rows = [
        {"metric": "train_rows", "value": len(train)},
        {"metric": "test_rows", "value": len(test)},
        {"metric": "train_start", "value": train["date"].min().date().isoformat()},
        {"metric": "train_end", "value": train["date"].max().date().isoformat()},
        {"metric": "test_start", "value": test["date"].min().date().isoformat()},
        {"metric": "test_end", "value": test["date"].max().date().isoformat()},
        {"metric": "store_count", "value": train["store_nbr"].nunique()},
        {"metric": "family_count", "value": train["family"].nunique()},
        {"metric": "total_sales", "value": float(train["sales"].sum())},
        {"metric": "mean_sales_per_row", "value": float(train["sales"].mean())},
        {"metric": "zero_sales_rate", "value": float((train["sales"] == 0).mean())},
        {"metric": "mean_onpromotion", "value": float(train["onpromotion"].mean())},
    ]
    if transactions is not None:
        rows.append({"metric": "transactions_rows", "value": len(transactions)})

    overview = pd.DataFrame(rows)
    overview.to_csv(paths.tables_dir / "dataset_overview.csv", index=False)
    return overview


def create_summary_tables(data: dict[str, pd.DataFrame], paths: EdaPaths) -> dict[str, pd.DataFrame]:
    train = data["train"]
    stores = data["stores"]
    holidays = data["holidays"]

    family_summary = (
        train.groupby("family", observed=True)
        .agg(
            total_sales=("sales", "sum"),
            mean_sales=("sales", "mean"),
            zero_sales_rate=("sales", lambda series: float((series == 0).mean())),
            mean_onpromotion=("onpromotion", "mean"),
        )
        .sort_values("total_sales", ascending=False)
        .reset_index()
    )
    family_summary.to_csv(paths.tables_dir / "family_summary.csv", index=False)

    store_sales = train.groupby("store_nbr", observed=True)["sales"].sum().reset_index()
    store_summary = (
        store_sales.merge(stores, on="store_nbr", how="left")
        .groupby(["type", "cluster"], observed=True)
        .agg(store_count=("store_nbr", "nunique"), total_sales=("sales", "sum"), mean_store_sales=("sales", "mean"))
        .sort_values("total_sales", ascending=False)
        .reset_index()
    )
    store_summary.to_csv(paths.tables_dir / "store_cluster_summary.csv", index=False)

    effective_holidays = holidays[~holidays["transferred"]].copy()
    holiday_summary = (
        effective_holidays.groupby(["type", "locale"], observed=True)
        .agg(event_count=("description", "count"))
        .sort_values("event_count", ascending=False)
        .reset_index()
    )
    holiday_summary.to_csv(paths.tables_dir / "holiday_summary.csv", index=False)

    return {
        "family_summary": family_summary,
        "store_summary": store_summary,
        "holiday_summary": holiday_summary,
    }


def plot_daily_sales(train: pd.DataFrame, paths: EdaPaths) -> None:
    daily_sales = train.groupby("date", observed=True)["sales"].sum().sort_index()
    rolling_sales = daily_sales.rolling(30, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(daily_sales.index, daily_sales.values, color="#9aa6b2", linewidth=0.7, label="Daily sales")
    ax.plot(rolling_sales.index, rolling_sales.values, color="#0b7285", linewidth=2.0, label="30-day rolling mean")
    ax.axvline(pd.Timestamp("2016-04-16"), color="#d9480f", linestyle="--", linewidth=1.4, label="2016 Ecuador earthquake")
    ax.set_title("Daily Total Sales Trend")
    ax.set_ylabel("Sales")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend()
    fig.autofmt_xdate()
    save_plot(paths.figures_dir / "daily_sales_trend.png")


def plot_family_sales(family_summary: pd.DataFrame, paths: EdaPaths) -> None:
    top_families = family_summary.head(15).sort_values("total_sales", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top_families["family"].astype(str), top_families["total_sales"], color="#2f9e44")
    ax.set_title("Top 15 Families by Total Sales")
    ax.set_xlabel("Total sales")
    save_plot(paths.figures_dir / "top_family_sales.png")


def plot_zero_sales(family_summary: pd.DataFrame, paths: EdaPaths) -> None:
    zero_families = family_summary.sort_values("zero_sales_rate", ascending=False).head(15)
    zero_families = zero_families.sort_values("zero_sales_rate", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(zero_families["family"].astype(str), zero_families["zero_sales_rate"], color="#c92a2a")
    ax.set_title("Top 15 Families by Zero-Sales Rate")
    ax.set_xlabel("Zero-sales rate")
    ax.set_xlim(0, 1)
    save_plot(paths.figures_dir / "zero_sales_rate_by_family.png")


def plot_weekday_pattern(train: pd.DataFrame, paths: EdaPaths) -> None:
    weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    frame = train[["date", "sales"]].copy()
    frame["weekday"] = frame["date"].dt.dayofweek
    weekday_sales = frame.groupby("weekday", observed=True)["sales"].mean().reindex(range(7))

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(weekday_order, weekday_sales.values, color="#1971c2")
    ax.set_title("Average Row-Level Sales by Day of Week")
    ax.set_ylabel("Mean sales")
    save_plot(paths.figures_dir / "sales_by_day_of_week.png")


def plot_promotion_relationship(train: pd.DataFrame, paths: EdaPaths) -> None:
    daily = train.groupby("date", observed=True).agg(sales=("sales", "sum"), onpromotion=("onpromotion", "sum"))
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(daily["onpromotion"], daily["sales"], s=12, alpha=0.45, color="#5f3dc4")
    ax.set_title("Daily Promotion Count vs Total Sales")
    ax.set_xlabel("Daily onpromotion sum")
    ax.set_ylabel("Daily sales")
    save_plot(paths.figures_dir / "promotion_vs_sales.png")


def plot_oil_sales(train: pd.DataFrame, oil: pd.DataFrame, paths: EdaPaths) -> None:
    monthly_sales = train.groupby(pd.Grouper(key="date", freq="ME"), observed=True)["sales"].sum()
    monthly_oil = oil.set_index("date")["dcoilwtico"].resample("ME").mean().interpolate()

    fig, ax_sales = plt.subplots(figsize=(12, 6))
    ax_oil = ax_sales.twinx()
    ax_sales.plot(monthly_sales.index, monthly_sales.values, color="#0b7285", linewidth=2, label="Monthly sales")
    ax_oil.plot(
        monthly_oil.index,
        monthly_oil.values,
        color="#e67700",
        linewidth=2,
        marker="o",
        markersize=3,
        label="Monthly oil price (interpolated)",
    )
    ax_sales.set_title("Monthly Sales vs Oil Price (Monthly Mean, Oil Interpolated)")
    ax_sales.set_ylabel("Monthly sales")
    ax_oil.set_ylabel("Oil price")
    ax_sales.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax_sales.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    save_plot(paths.figures_dir / "monthly_sales_vs_oil.png")


def plot_holiday_effect(train: pd.DataFrame, stores: pd.DataFrame, holidays: pd.DataFrame, paths: EdaPaths) -> None:
    effective_holidays = holidays[~holidays["transferred"]].copy()
    national_dates = set(
        effective_holidays.loc[effective_holidays["locale"] == "National", "date"].dt.normalize()
    )
    regional_pairs = set(
        zip(
            effective_holidays.loc[effective_holidays["locale"] == "Regional", "date"].dt.normalize(),
            effective_holidays.loc[effective_holidays["locale"] == "Regional", "locale_name"].astype(str),
            strict=False,
        )
    )
    local_pairs = set(
        zip(
            effective_holidays.loc[effective_holidays["locale"] == "Local", "date"].dt.normalize(),
            effective_holidays.loc[effective_holidays["locale"] == "Local", "locale_name"].astype(str),
            strict=False,
        )
    )

    store_daily = train.groupby(["date", "store_nbr"], observed=True)["sales"].sum().reset_index()
    store_daily = store_daily.merge(stores[["store_nbr", "city", "state"]], on="store_nbr", how="left")
    date_key = store_daily["date"].dt.normalize()
    regional_key = list(zip(date_key, store_daily["state"].astype(str), strict=False))
    local_key = list(zip(date_key, store_daily["city"].astype(str), strict=False))
    store_daily["is_holiday_or_event"] = (
        date_key.isin(national_dates)
        | pd.Series(regional_key, index=store_daily.index).isin(regional_pairs)
        | pd.Series(local_key, index=store_daily.index).isin(local_pairs)
    )
    holiday_effect = (
        store_daily.groupby("is_holiday_or_event", observed=True)["sales"]
        .mean()
        .rename(index={False: "Non-holiday/event", True: "Holiday/event"})
    )

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(holiday_effect.index.astype(str), holiday_effect.values, color=["#495057", "#f08c00"])
    ax.set_title("Average Store-Day Sales on Locale-Matched Holiday/Event Dates")
    ax.set_ylabel("Mean store-day sales")
    save_plot(paths.figures_dir / "holiday_event_sales_effect.png")


def plot_store_cluster_sales(store_summary: pd.DataFrame, paths: EdaPaths) -> None:
    top_clusters = store_summary.head(12).copy()
    top_clusters["cluster_label"] = (
        "type " + top_clusters["type"].astype(str) + " / cluster " + top_clusters["cluster"].astype(str)
    )
    top_clusters = top_clusters.sort_values("total_sales", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top_clusters["cluster_label"], top_clusters["total_sales"], color="#1864ab")
    ax.set_title("Top Store Type/Cluster Groups by Total Sales")
    ax.set_xlabel("Total sales")
    save_plot(paths.figures_dir / "store_cluster_sales.png")


def plot_validation_summary(validation_summary_path: Path, paths: EdaPaths) -> bool:
    if not validation_summary_path.exists():
        return False

    validation = pd.read_csv(validation_summary_path)
    if validation.empty:
        return False

    fig, ax = plt.subplots(figsize=(8, 5))
    labels = [f"fold {int(fold_id)}" for fold_id in validation["fold_id"]]
    ax.plot(labels, validation["validation_rmsle"], marker="o", color="#862e9c", linewidth=2)
    ax.set_title("Validation RMSLE by Fold")
    ax.set_ylabel("RMSLE")
    ax.grid(axis="y", alpha=0.25)
    save_plot(paths.figures_dir / "validation_rmsle_by_fold.png")
    return True


def write_report(
    data: dict[str, pd.DataFrame],
    overview: pd.DataFrame,
    summaries: dict[str, pd.DataFrame],
    paths: EdaPaths,
    has_validation_plot: bool,
) -> None:
    train = data["train"]
    test = data["test"]
    family_summary = summaries["family_summary"]

    overview_values = dict(zip(overview["metric"], overview["value"], strict=False))
    top_families = family_summary.head(8)[["family", "total_sales", "zero_sales_rate"]].copy()
    top_families["family"] = top_families["family"].astype(str)

    lines = [
        "# Store Sales EDA Report",
        "",
        "## Dataset Snapshot",
        "",
        f"- Train rows: `{int(overview_values['train_rows']):,}`",
        f"- Test rows: `{int(overview_values['test_rows']):,}`",
        f"- Train date range: `{overview_values['train_start']}` to `{overview_values['train_end']}`",
        f"- Test date range: `{overview_values['test_start']}` to `{overview_values['test_end']}`",
        f"- Stores: `{int(overview_values['store_count']):,}`",
        f"- Families: `{int(overview_values['family_count']):,}`",
        f"- Total train sales: `{float(overview_values['total_sales']):,.2f}`",
        f"- Zero-sales row rate: `{float(overview_values['zero_sales_rate']):.2%}`",
        f"- Mean onpromotion per row: `{float(overview_values['mean_onpromotion']):.4f}`",
        "",
        "## Key Observations",
        "",
        "- Sales show strong calendar structure, so validation must remain time-based.",
        "- Zero-sales behavior is material and differs strongly by family, so low-demand families need explicit attention.",
        "- Promotions are a legal future-known signal in `test.csv`; richer promotion features are a high-priority modeling direction.",
        "- The oil and holiday/event views should be treated as explanatory context rather than standalone causal proof.",
        "- Holiday/event comparisons are matched to national, regional, and local store scope; oil monthly means are interpolated for continuity.",
        "- The fold chart is useful for checking whether a feature improves only one holdout or is stable across time.",
        "",
        "## Top Families by Sales",
        "",
        dataframe_to_markdown(top_families),
        "",
        "## Figures",
        "",
        "![Daily sales trend](figures/daily_sales_trend.png)",
        "",
        "![Top family sales](figures/top_family_sales.png)",
        "",
        "![Zero sales rate by family](figures/zero_sales_rate_by_family.png)",
        "",
        "![Sales by day of week](figures/sales_by_day_of_week.png)",
        "",
        "![Promotion vs sales](figures/promotion_vs_sales.png)",
        "",
        "![Monthly sales vs oil](figures/monthly_sales_vs_oil.png)",
        "",
        "![Holiday/event sales effect](figures/holiday_event_sales_effect.png)",
        "",
        "![Store cluster sales](figures/store_cluster_sales.png)",
        "",
    ]
    if has_validation_plot:
        lines.extend(
            [
                "![Validation RMSLE by fold](figures/validation_rmsle_by_fold.png)",
                "",
            ]
        )

    lines.extend(
        [
            "## Generated Tables",
            "",
            "- `tables/dataset_overview.csv`",
            "- `tables/family_summary.csv`",
            "- `tables/store_cluster_summary.csv`",
            "- `tables/holiday_summary.csv`",
            "",
            "## Suggested Next EDA Checks",
            "",
            "1. Compare the last 90 training days against the public-test period calendar and promotions.",
            "2. Break down validation errors by `family`, `store_nbr`, and zero-sales-heavy groups.",
            "3. Inspect promotion response by family before adding more model features.",
            "4. Check whether holiday/event windows explain the worsening late validation folds.",
        ]
    )

    paths.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_eda(data_dir: Path, output_dir: Path, validation_summary_path: Path) -> EdaPaths:
    paths = prepare_paths(output_dir)
    data = read_data(data_dir)
    overview = create_overview_table(data, paths)
    summaries = create_summary_tables(data, paths)

    plot_daily_sales(data["train"], paths)
    plot_family_sales(summaries["family_summary"], paths)
    plot_zero_sales(summaries["family_summary"], paths)
    plot_weekday_pattern(data["train"], paths)
    plot_promotion_relationship(data["train"], paths)
    plot_oil_sales(data["train"], data["oil"], paths)
    plot_holiday_effect(data["train"], data["stores"], data["holidays"], paths)
    plot_store_cluster_sales(summaries["store_summary"], paths)
    has_validation_plot = plot_validation_summary(validation_summary_path, paths)

    write_report(data, overview, summaries, paths, has_validation_plot)
    return paths


def main() -> None:
    args = build_parser().parse_args()
    paths = generate_eda(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        validation_summary_path=args.validation_summary,
    )
    print(f"EDA report: {paths.report_path}")
    print(f"Figures: {paths.figures_dir}")
    print(f"Tables: {paths.tables_dir}")


if __name__ == "__main__":
    main()
