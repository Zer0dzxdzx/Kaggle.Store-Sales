from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from store_sales.pipeline import build_submission_frame


def test_submission_frame_matches_sample_order_and_clips_negative_sales(tmp_path) -> None:
    sample_path = tmp_path / "sample_submission.csv"
    pd.DataFrame({"id": [3, 1, 2], "sales": [0.0, 0.0, 0.0]}).to_csv(sample_path, index=False)
    predictions = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "sales_pred": [-5.0, 2.5, 7.0],
        }
    )

    submission = build_submission_frame(predictions, sample_path)

    assert submission["id"].tolist() == [3, 1, 2]
    assert submission["sales"].tolist() == [7.0, 0.0, 2.5]


def test_submission_frame_rejects_duplicate_prediction_ids(tmp_path) -> None:
    sample_path = tmp_path / "sample_submission.csv"
    pd.DataFrame({"id": [1, 2], "sales": [0.0, 0.0]}).to_csv(sample_path, index=False)
    predictions = pd.DataFrame({"id": [1, 1], "sales_pred": [1.0, 2.0]})

    with pytest.raises(ValueError, match="duplicate ids"):
        build_submission_frame(predictions, sample_path)


def test_submission_frame_rejects_missing_or_extra_ids(tmp_path) -> None:
    sample_path = tmp_path / "sample_submission.csv"
    pd.DataFrame({"id": [1, 2], "sales": [0.0, 0.0]}).to_csv(sample_path, index=False)
    predictions = pd.DataFrame({"id": [1, 3], "sales_pred": [1.0, 3.0]})

    with pytest.raises(ValueError, match="do not match"):
        build_submission_frame(predictions, sample_path)


def test_submission_frame_rejects_non_finite_predictions(tmp_path) -> None:
    sample_path = tmp_path / "sample_submission.csv"
    pd.DataFrame({"id": [1], "sales": [0.0]}).to_csv(sample_path, index=False)
    predictions = pd.DataFrame({"id": [1], "sales_pred": [np.inf]})

    with pytest.raises(ValueError, match="non-finite"):
        build_submission_frame(predictions, sample_path)
