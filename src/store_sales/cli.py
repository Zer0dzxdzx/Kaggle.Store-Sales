from __future__ import annotations

import argparse
from pathlib import Path

from store_sales.config import PipelineConfig
from store_sales.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Kaggle Store Sales baseline pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Train, validate, and create a submission file.")
    run_parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    run_parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    run_parser.add_argument("--train-start-date", default="2015-01-01")
    run_parser.add_argument("--validation-horizon", type=int, default=16)
    run_parser.add_argument("--model-type", choices=["hist_gbdt", "lightgbm"], default="hist_gbdt")
    run_parser.add_argument("--random-state", type=int, default=42)
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
            model_type=args.model_type,
            random_state=args.random_state,
        )
        outputs = run_pipeline(config)
        print(f"Validation RMSLE: {outputs.validation_score:.6f}")
        print(f"Validation predictions: {outputs.validation_path}")
        print(f"Metrics: {outputs.metrics_path}")
        print(f"Submission: {outputs.submission_path}")
        return

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
