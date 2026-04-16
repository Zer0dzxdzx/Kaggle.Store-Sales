from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def rmsle(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    true = np.clip(np.asarray(y_true, dtype=float), 0.0, None)
    pred = np.clip(np.asarray(y_pred, dtype=float), 0.0, None)
    return float(np.sqrt(np.mean(np.square(np.log1p(pred) - np.log1p(true)))))


def write_metrics(path: Path, metrics: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
