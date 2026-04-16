from __future__ import annotations

import argparse
from pathlib import Path

from store_sales.config import PipelineConfig
from store_sales.experiment_log import append_experiment_log, build_experiment_log_row
from store_sales.pipeline import run_pipeline


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
    run_parser.add_argument("--model-type", choices=["hist_gbdt", "lightgbm"], default="hist_gbdt")
    run_parser.add_argument("--random-state", type=int, default=42)
    run_parser.add_argument("--log-experiment", action="store_true")
    run_parser.add_argument("--experiment-name", default=None)
    run_parser.add_argument("--experiment-log-path", type=Path, default=Path("docs/experiment_log.csv"))
    run_parser.add_argument("--data-snapshot", default=None)
    run_parser.add_argument("--experiment-conclusion", default=None)
    run_parser.add_argument("--experiment-next-action", default=None)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        config = PipelineConfig(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            train_start_date=args.train_start_date,
            validation_horizon=args.validation_horizon,
            validation_windows=args.validation_windows,
            validation_step_days=args.validation_step_days,
            model_type=args.model_type,
            random_state=args.random_state,
        )
        outputs = run_pipeline(config)
        print(f"Validation RMSLE: {outputs.validation_score:.6f}")
        print(f"Validation predictions: {outputs.validation_path}")
        print(f"Validation summary: {outputs.validation_summary_path}")
        print(f"Metrics: {outputs.metrics_path}")
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

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
