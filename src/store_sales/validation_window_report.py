from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


WINDOW_COLUMNS = ["fold_id", "validation_start", "validation_end", "train_rows", "validation_rows"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare Store Sales validation-window runs.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="Validation run in name=artifacts_dir format. Can be repeated.",
    )
    parser.add_argument("--baseline-name", required=True)
    parser.add_argument("--title", default="Validation Window Comparison")
    return parser


def parse_run_specs(values: list[str]) -> list[tuple[str, Path]]:
    specs = []
    seen_names = set()
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --run `{value}`. Expected name=artifacts_dir.")
        name, raw_path = value.split("=", maxsplit=1)
        name = name.strip()
        if not name:
            raise ValueError(f"Invalid --run `{value}`. Run name cannot be empty.")
        if name in seen_names:
            raise ValueError(f"Duplicate run name: {name}.")
        seen_names.add(name)
        specs.append((name, Path(raw_path)))
    return specs


def load_validation_summary(name: str, artifacts_dir: Path) -> pd.DataFrame:
    summary_path = artifacts_dir / "validation_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing validation summary for `{name}`: {summary_path}")

    summary = pd.read_csv(summary_path)
    required_columns = set(WINDOW_COLUMNS + ["validation_rmsle", "train_rows"])
    missing = required_columns.difference(summary.columns)
    if missing:
        raise ValueError(f"`{summary_path}` is missing columns: {sorted(missing)}")

    summary = summary.copy()
    summary["run_name"] = name
    summary["artifacts_dir"] = str(artifacts_dir)
    return summary


def validate_same_windows(summaries: dict[str, pd.DataFrame]) -> None:
    reference_name, reference = next(iter(summaries.items()))
    reference_windows = reference[WINDOW_COLUMNS].sort_values("fold_id").reset_index(drop=True)

    for name, summary in summaries.items():
        current_windows = summary[WINDOW_COLUMNS].sort_values("fold_id").reset_index(drop=True)
        if reference_windows.equals(current_windows):
            continue

        comparison = reference_windows.merge(
            current_windows,
            on="fold_id",
            how="outer",
            suffixes=(f"_{reference_name}", f"_{name}"),
            indicator=True,
        )
        raise ValueError(
            f"Validation windows differ between `{reference_name}` and `{name}`:\n"
            f"{comparison.to_string(index=False)}"
        )


def build_fold_comparison(summaries: dict[str, pd.DataFrame], baseline_name: str) -> pd.DataFrame:
    if baseline_name not in summaries:
        raise ValueError(f"Baseline run `{baseline_name}` not found. Available: {sorted(summaries)}")

    baseline = summaries[baseline_name][
        ["fold_id", "validation_start", "validation_end", "validation_rmsle"]
    ].rename(columns={"validation_rmsle": "baseline_rmsle"})

    frames = []
    for name, summary in summaries.items():
        current = summary[["fold_id", "validation_rmsle"]].rename(
            columns={"validation_rmsle": f"{name}_rmsle"}
        )
        if name == baseline_name:
            frames.append(baseline)
            continue
        merged = baseline.merge(current, on="fold_id", how="inner")
        merged[f"{name}_delta_vs_{baseline_name}"] = merged[f"{name}_rmsle"] - merged["baseline_rmsle"]
        frames.append(merged[["fold_id", f"{name}_rmsle", f"{name}_delta_vs_{baseline_name}"]])

    comparison = frames[0]
    for frame in frames[1:]:
        comparison = comparison.merge(frame, on="fold_id", how="inner")
    return comparison


def build_run_summary(summaries: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, summary in summaries.items():
        scores = summary["validation_rmsle"]
        rows.append(
            {
                "run_name": name,
                "validation_rmsle_mean": float(scores.mean()),
                "validation_rmsle_std": float(scores.std(ddof=0)),
                "validation_rmsle_min": float(scores.min()),
                "validation_rmsle_max": float(scores.max()),
                "worst_fold_id": int(summary.loc[scores.idxmax(), "fold_id"]),
                "train_rows_min": int(summary["train_rows"].min()),
                "train_rows_max": int(summary["train_rows"].max()),
                "artifacts_dir": summary["artifacts_dir"].iloc[0],
            }
        )
    return pd.DataFrame(rows).sort_values("validation_rmsle_mean").reset_index(drop=True)


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


def write_report(
    output_dir: Path,
    title: str,
    baseline_name: str,
    run_summary: pd.DataFrame,
    fold_comparison: pd.DataFrame,
) -> Path:
    report_path = output_dir / "validation_window_report.md"
    best_run = run_summary.iloc[0]
    baseline_row = run_summary[run_summary["run_name"] == baseline_name].iloc[0]

    lines = [
        f"# {title}",
        "",
        "本报告比较多个 validation run 在同一组显式时间窗口上的表现。Lower RMSLE is better.",
        "",
        "## Decision Rule",
        "",
        "- 先看 mean RMSLE。",
        "- 再看 worst fold，避免只改善平均值但牺牲某个时间窗口。",
        "- 如果某个 profile 是根据某个 fold 设计的，还要检查它是否能在历史同季窗口稳定改善。",
        "",
        "## Run Summary",
        "",
        dataframe_to_markdown(run_summary),
        "",
        "## Fold Comparison",
        "",
        dataframe_to_markdown(fold_comparison),
        "",
        "## Interpretation",
        "",
        f"- 当前 mean RMSLE 最低的是 `{best_run['run_name']}`，mean=`{best_run['validation_rmsle_mean']:.6f}`。",
        f"- Baseline `{baseline_name}` 的 mean RMSLE 是 `{baseline_row['validation_rmsle_mean']:.6f}`。",
        "- 如果本地 historical windows 与 Kaggle public score 方向冲突，优先相信 public score，同时回头修正验证设计。",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def run_report(run_specs: list[tuple[str, Path]], output_dir: Path, baseline_name: str, title: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = {name: load_validation_summary(name, path) for name, path in run_specs}
    validate_same_windows(summaries)

    long_summary = pd.concat(summaries.values(), ignore_index=True)
    run_summary = build_run_summary(summaries)
    fold_comparison = build_fold_comparison(summaries, baseline_name)

    long_summary.to_csv(output_dir / "validation_summary_long.csv", index=False)
    run_summary.to_csv(output_dir / "run_summary.csv", index=False)
    fold_comparison.to_csv(output_dir / "fold_comparison.csv", index=False)
    return write_report(output_dir, title, baseline_name, run_summary, fold_comparison)


def main() -> None:
    args = build_parser().parse_args()
    report_path = run_report(
        run_specs=parse_run_specs(args.run),
        output_dir=args.output_dir,
        baseline_name=args.baseline_name,
        title=args.title,
    )
    print(f"Validation window report: {report_path}")


if __name__ == "__main__":
    main()
