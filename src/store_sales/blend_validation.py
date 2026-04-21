from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from store_sales.metrics import rmsle, write_metrics
from store_sales.validation_window_report import (
    build_fold_comparison,
    build_run_summary,
    dataframe_to_markdown,
    load_validation_summary,
    validate_same_windows,
)


KEY_COLUMNS = ["date", "store_nbr", "family"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Blend two Store Sales validation runs.")
    parser.add_argument(
        "--base-run",
        required=True,
        help="Base validation run in name=artifacts_dir format.",
    )
    parser.add_argument(
        "--other-run",
        required=True,
        help="Secondary validation run in name=artifacts_dir format.",
    )
    parser.add_argument(
        "--base-weight",
        action="append",
        type=float,
        required=True,
        help="Weight assigned to the base run prediction. Can be repeated.",
    )
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--title", default="Validation Blending Report")
    return parser


def parse_run_spec(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"Invalid run spec `{value}`. Expected name=artifacts_dir.")
    name, raw_path = value.split("=", maxsplit=1)
    name = name.strip()
    if not name:
        raise ValueError(f"Invalid run spec `{value}`. Run name cannot be empty.")
    return name, Path(raw_path)


def format_weight_suffix(weight: float) -> str:
    return f"{int(round(weight * 1000)):03d}"


def validate_weights(weights: list[float]) -> list[float]:
    unique_weights = sorted(set(weights), reverse=True)
    invalid = [weight for weight in unique_weights if weight < 0.0 or weight > 1.0]
    if invalid:
        raise ValueError(f"Blend weights must be between 0 and 1. Invalid values: {invalid}")
    return unique_weights


def load_fold_predictions(artifacts_dir: Path, fold_id: int) -> pd.DataFrame:
    path = artifacts_dir / f"validation_predictions_fold_{fold_id:02d}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing fold predictions: {path}")

    frame = pd.read_csv(path)
    required_columns = set(KEY_COLUMNS + ["sales", "sales_pred"])
    missing = required_columns.difference(frame.columns)
    if missing:
        raise ValueError(f"`{path}` is missing columns: {sorted(missing)}")
    if frame[KEY_COLUMNS].duplicated().any():
        duplicate_keys = frame.loc[frame[KEY_COLUMNS].duplicated(), KEY_COLUMNS].head(10)
        raise ValueError(f"`{path}` contains duplicate prediction keys:\n{duplicate_keys.to_string(index=False)}")
    return frame[KEY_COLUMNS + ["sales", "sales_pred"]].copy()


def blend_fold_predictions(
    base_predictions: pd.DataFrame,
    other_predictions: pd.DataFrame,
    base_weight: float,
) -> pd.DataFrame:
    merged = base_predictions.merge(
        other_predictions.rename(columns={"sales": "sales_other", "sales_pred": "sales_pred_other"}),
        on=KEY_COLUMNS,
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != len(base_predictions) or len(merged) != len(other_predictions):
        raise ValueError("Prediction rows do not align between blended runs.")

    sales_delta = (merged["sales"] - merged["sales_other"]).abs().max()
    if sales_delta > 1e-9:
        raise ValueError(f"Validation targets differ between blended runs. Max delta={sales_delta}.")

    blended = merged[KEY_COLUMNS + ["sales"]].copy()
    blended["sales_pred"] = (
        base_weight * merged["sales_pred"] + (1.0 - base_weight) * merged["sales_pred_other"]
    ).clip(lower=0.0)
    return blended


def write_blend_artifacts(
    run_name: str,
    output_dir: Path,
    base_summary: pd.DataFrame,
    base_dir: Path,
    other_dir: Path,
    base_weight: float,
) -> Path:
    run_dir = output_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for _, fold in base_summary.sort_values("fold_id").iterrows():
        fold_id = int(fold["fold_id"])
        base_predictions = load_fold_predictions(base_dir, fold_id)
        other_predictions = load_fold_predictions(other_dir, fold_id)
        blended = blend_fold_predictions(base_predictions, other_predictions, base_weight)
        score = rmsle(blended["sales"].to_numpy(), blended["sales_pred"].to_numpy())

        predictions_path = run_dir / f"validation_predictions_fold_{fold_id:02d}.csv"
        blended.to_csv(predictions_path, index=False)
        if fold_id == int(base_summary["fold_id"].max()):
            blended.to_csv(run_dir / "validation_predictions.csv", index=False)

        rows.append(
            {
                "fold_id": fold_id,
                "validation_start": fold["validation_start"],
                "validation_end": fold["validation_end"],
                "validation_rmsle": score,
                "train_rows": int(fold["train_rows"]),
                "validation_rows": int(fold["validation_rows"]),
                "predictions_path": str(predictions_path),
            }
        )

    summary = pd.DataFrame(rows)
    summary.to_csv(run_dir / "validation_summary.csv", index=False)
    base_metrics_path = base_dir / "validation_metrics.json"
    base_metrics = json.loads(base_metrics_path.read_text(encoding="utf-8")) if base_metrics_path.exists() else {}
    write_metrics(
        run_dir / "validation_metrics.json",
        {
            "validation_rmsle": float(summary["validation_rmsle"].mean()),
            "validation_rmsle_mean": float(summary["validation_rmsle"].mean()),
            "validation_rmsle_std": float(summary["validation_rmsle"].std(ddof=0)),
            "validation_rmsle_min": float(summary["validation_rmsle"].min()),
            "validation_rmsle_max": float(summary["validation_rmsle"].max()),
            "validation_horizon_days": base_metrics.get("validation_horizon_days"),
            "validation_windows": base_metrics.get("validation_windows"),
            "validation_step_days": base_metrics.get("validation_step_days"),
            "validation_window_dates": base_metrics.get("validation_window_dates"),
            "model_type": "blend",
            "base_weight": base_weight,
        },
    )
    return run_dir


def write_blend_report(
    report_dir: Path,
    title: str,
    baseline_name: str,
    base_name: str,
    other_name: str,
    run_summary: pd.DataFrame,
    fold_comparison: pd.DataFrame,
) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "blend_report.md"
    best_run = run_summary.iloc[0]
    baseline_row = run_summary[run_summary["run_name"] == baseline_name].iloc[0]

    lines = [
        f"# {title}",
        "",
        f"本报告测试 `{base_name}` 与 `{other_name}` 的简单 prediction blending。Lower RMSLE is better.",
        "",
        "## Decision Rule",
        "",
        "- 先看 mean RMSLE 是否低于 baseline。",
        "- 再看 worst fold，避免平均分小幅改善但最差窗口恶化。",
        "- 这里只做 validation blending；除非验证稳定优于 baseline，否则不生成 Kaggle submission。",
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
    ]

    if best_run["run_name"] == baseline_name:
        lines.append("- 本轮 simple blending 没有超过 baseline，不应生成新的提交。")
    else:
        best_delta_column = f"{best_run['run_name']}_delta_vs_{baseline_name}"
        delta = float(best_run["validation_rmsle_mean"] - baseline_row["validation_rmsle_mean"])
        lines.append(f"- 最优 blending 相比 baseline 的 mean RMSLE delta 为 `{delta:.6f}`。")
        if best_delta_column in fold_comparison.columns:
            regressed_folds = fold_comparison[fold_comparison[best_delta_column] > 0].copy()
            if regressed_folds.empty:
                lines.append("- 最优 blending 没有任何 fold 差于 baseline，可以进入 stability slice checks。")
            else:
                worst_regression = regressed_folds.sort_values(best_delta_column, ascending=False).iloc[0]
                lines.append(
                    f"- 最优 blending 有 `{len(regressed_folds)}` 个 fold 差于 baseline；"
                    f"最大回退出现在 fold `{int(worst_regression['fold_id'])}`，"
                    f"delta=`{float(worst_regression[best_delta_column]):.6f}`。"
                )
        lines.append("- 只有通过 stability slice checks 后，才应考虑生成 Kaggle submission。")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def run_blending(
    base_run: tuple[str, Path],
    other_run: tuple[str, Path],
    base_weights: list[float],
    artifacts_dir: Path,
    report_dir: Path,
    title: str,
) -> Path:
    base_name, base_dir = base_run
    other_name, other_dir = other_run
    weights = validate_weights(base_weights)

    source_summaries = {
        base_name: load_validation_summary(base_name, base_dir),
        other_name: load_validation_summary(other_name, other_dir),
    }
    validate_same_windows(source_summaries)
    base_summary = source_summaries[base_name]

    run_specs = [base_run, other_run]
    for weight in weights:
        run_name = f"blend_{base_name}_{other_name}_base_w{format_weight_suffix(weight)}"
        run_dir = write_blend_artifacts(
            run_name=run_name,
            output_dir=artifacts_dir,
            base_summary=base_summary,
            base_dir=base_dir,
            other_dir=other_dir,
            base_weight=weight,
        )
        run_specs.append((run_name, run_dir))

    summaries = {name: load_validation_summary(name, path) for name, path in run_specs}
    validate_same_windows(summaries)
    long_summary = pd.concat(summaries.values(), ignore_index=True)
    run_summary = build_run_summary(summaries)
    fold_comparison = build_fold_comparison(summaries, base_name)

    report_dir.mkdir(parents=True, exist_ok=True)
    long_summary.to_csv(report_dir / "validation_summary_long.csv", index=False)
    run_summary.to_csv(report_dir / "run_summary.csv", index=False)
    fold_comparison.to_csv(report_dir / "fold_comparison.csv", index=False)
    return write_blend_report(report_dir, title, base_name, base_name, other_name, run_summary, fold_comparison)


def main() -> None:
    args = build_parser().parse_args()
    report_path = run_blending(
        base_run=parse_run_spec(args.base_run),
        other_run=parse_run_spec(args.other_run),
        base_weights=args.base_weight,
        artifacts_dir=args.artifacts_dir,
        report_dir=args.report_dir,
        title=args.title,
    )
    print(f"Blend report: {report_path}")


if __name__ == "__main__":
    main()
