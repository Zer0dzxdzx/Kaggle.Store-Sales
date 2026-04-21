from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from store_sales.config import PipelineConfig
from store_sales.experiment_log import append_experiment_log, build_experiment_log_row
from store_sales.experiment_runner import available_experiments, run_experiment_suite
from store_sales.feature_profiles import apply_feature_profile, available_feature_profiles
from store_sales.pipeline import run_pipeline


def parse_validation_window_dates(values: list[str] | None) -> tuple[tuple[str, str], ...]:
    if not values:
        return ()

    windows = []
    for value in values:
        if ":" not in value:
            raise argparse.ArgumentTypeError(
                f"Invalid validation window `{value}`. Expected format: YYYY-MM-DD:YYYY-MM-DD."
            )
        raw_start, raw_end = value.split(":", maxsplit=1)
        try:
            start_date = date.fromisoformat(raw_start)
            end_date = date.fromisoformat(raw_end)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Invalid validation window `{value}`. Expected ISO dates: YYYY-MM-DD:YYYY-MM-DD."
            ) from exc
        if start_date > end_date:
            raise argparse.ArgumentTypeError(
                f"Invalid validation window `{value}`. Start date must be <= end date."
            )
        windows.append((start_date.isoformat(), end_date.isoformat()))
    return tuple(windows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Kaggle Store Sales baseline pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Train, validate, and create a submission file.")
    run_parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    run_parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    run_parser.add_argument("--train-start-date", default="2015-01-01")
    run_parser.add_argument("--validation-horizon", type=int, default=16)
    run_parser.add_argument("--validation-windows", type=int, default=1)
    run_parser.add_argument("--validation-step-days", type=int, default=None)
    run_parser.add_argument(
        "--validation-window",
        action="append",
        default=None,
        help=(
            "Explicit inclusive validation window in YYYY-MM-DD:YYYY-MM-DD format. "
            "Can be repeated; overrides rolling validation window generation."
        ),
    )
    run_parser.add_argument("--model-type", choices=["seasonal_naive", "ridge", "hist_gbdt", "lightgbm"], default="hist_gbdt")
    run_parser.add_argument("--feature-profile", choices=available_feature_profiles(), default="baseline")
    run_parser.add_argument("--random-state", type=int, default=42)
    run_parser.add_argument("--skip-submission", action="store_true")
    run_parser.add_argument("--log-experiment", action="store_true")
    run_parser.add_argument("--experiment-name", default=None)
    run_parser.add_argument("--experiment-log-path", type=Path, default=Path("docs/experiment_log.csv"))
    run_parser.add_argument("--data-snapshot", default=None)
    run_parser.add_argument("--experiment-conclusion", default=None)
    run_parser.add_argument("--experiment-next-action", default=None)

    compare_parser = subparsers.add_parser("compare", help="Run multiple validation experiments and write a comparison report.")
    compare_parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    compare_parser.add_argument("--output-dir", type=Path, default=Path("artifacts/experiments"))
    compare_parser.add_argument("--report-dir", type=Path, default=Path("reports/model_comparison"))
    compare_parser.add_argument(
        "--experiments",
        nargs="+",
        choices=available_experiments(),
        default=["seasonal_naive", "ridge_baseline", "histgbdt_baseline"],
    )
    compare_parser.add_argument("--validation-horizon", type=int, default=16)
    compare_parser.add_argument("--validation-windows", type=int, default=3)
    compare_parser.add_argument("--validation-step-days", type=int, default=16)
    compare_parser.add_argument(
        "--validation-window",
        action="append",
        default=None,
        help=(
            "Explicit inclusive validation window in YYYY-MM-DD:YYYY-MM-DD format. "
            "Can be repeated; overrides rolling validation window generation."
        ),
    )
    compare_parser.add_argument("--random-state", type=int, default=42)
    compare_parser.add_argument("--include-submission", action="store_true")
    compare_parser.add_argument("--log-experiments", action="store_true")
    compare_parser.add_argument("--experiment-log-path", type=Path, default=Path("docs/experiment_log.csv"))
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        try:
            validation_window_dates = parse_validation_window_dates(args.validation_window)
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        config = PipelineConfig(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            train_start_date=args.train_start_date,
            validation_horizon=args.validation_horizon,
            validation_windows=len(validation_window_dates) or args.validation_windows,
            validation_step_days=args.validation_step_days,
            validation_window_dates=validation_window_dates,
            model_type=args.model_type,
            feature_profile=args.feature_profile,
            random_state=args.random_state,
            make_submission=not args.skip_submission,
        )
        config = apply_feature_profile(config, args.feature_profile)
        outputs = run_pipeline(config)
        print(f"Validation RMSLE: {outputs.validation_score:.6f}")
        print(f"Validation predictions: {outputs.validation_path}")
        print(f"Validation summary: {outputs.validation_summary_path}")
        print(f"Metrics: {outputs.metrics_path}")
        if outputs.submission_path is None:
            print("Submission: skipped")
        else:
            print(f"Submission: {outputs.submission_path}")
        if args.log_experiment or args.experiment_name is not None:
            version_name = args.experiment_name or f"{args.model_type}_validation"
            data_snapshot = args.data_snapshot or args.data_dir.name
            row = build_experiment_log_row(
                config=config,
                outputs=outputs,
                version_name=version_name,
                data_snapshot=data_snapshot,
                conclusion=args.experiment_conclusion,
                next_action=args.experiment_next_action,
            )
            append_experiment_log(args.experiment_log_path, row)
            print(f"Experiment log updated: {args.experiment_log_path}")
        return

    if args.command == "compare":
        try:
            validation_window_dates = parse_validation_window_dates(args.validation_window)
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        results = run_experiment_suite(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            report_dir=args.report_dir,
            experiment_names=args.experiments,
            validation_horizon=args.validation_horizon,
            validation_windows=len(validation_window_dates) or args.validation_windows,
            validation_step_days=args.validation_step_days,
            validation_window_dates=validation_window_dates,
            random_state=args.random_state,
            make_submission=args.include_submission,
            log_experiments=args.log_experiments,
            experiment_log_path=args.experiment_log_path,
        )
        print("Model comparison complete.")
        print(f"Best experiment: {results.sort_values('validation_rmsle_mean').iloc[0]['experiment_name']}")
        print(f"Results: {args.report_dir / 'comparison_results.csv'}")
        print(f"Report: {args.report_dir / 'comparison_report.md'}")
        return

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
