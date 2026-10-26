"""Score an NSCLC TTE_OS submission with Survprompt-compatible metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REQUIRED_LABEL_COLUMNS = {"sample_id", "observed_time_days", "event_observed"}
_REQUIRED_SUBMISSION_COLUMNS = {"sample_id", "prediction"}
DAYS_PER_YEAR = 365.25
IBS_TIME_GRID_YEARS = tuple(index / 2 for index in range(1, 21))


def parse_tte_prediction(
    raw_value: Any,
) -> tuple[float | None, str | None]:
    if raw_value is None or (isinstance(raw_value, float) and np.isnan(raw_value)):
        return None, "empty prediction"

    text = str(raw_value).strip()
    if not text:
        return None, "empty prediction"
    try:
        predicted_days = float(text)
    except ValueError:
        return None, "prediction must be a numeric survival time in days"

    if not np.isfinite(predicted_days):
        return None, "prediction must be finite"
    if predicted_days < 0:
        return None, "prediction must be non-negative"
    return predicted_days, None


def build_evaluation_frame(
    submission: pd.DataFrame,
    test_labels: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    missing_submission = sorted(_REQUIRED_SUBMISSION_COLUMNS - set(submission.columns))
    if missing_submission:
        raise ValueError(
            "submission is missing required columns: " + ", ".join(missing_submission)
        )
    missing_labels = sorted(_REQUIRED_LABEL_COLUMNS - set(test_labels.columns))
    if missing_labels:
        raise ValueError(
            "test labels are missing required columns: " + ", ".join(missing_labels)
        )

    predictions = submission.copy()
    labels = test_labels.copy()
    predictions["sample_id"] = predictions["sample_id"].astype(str)
    labels["sample_id"] = labels["sample_id"].astype(str)
    if labels["sample_id"].duplicated().any():
        raise ValueError("test labels contain duplicate sample_id values")

    duplicated_ids = set(
        predictions.loc[predictions["sample_id"].duplicated(keep=False), "sample_id"]
    )
    unique_predictions = predictions[
        ~predictions["sample_id"].isin(duplicated_ids)
    ].drop_duplicates("sample_id")
    prediction_by_id = dict(
        zip(unique_predictions["sample_id"], unique_predictions["prediction"])
    )

    rows = []
    for label in labels.itertuples(index=False):
        sample_id = str(label.sample_id)
        raw_prediction = prediction_by_id.get(sample_id)
        if sample_id in duplicated_ids:
            pred_time_days, parse_error = None, "duplicate prediction"
        elif sample_id not in prediction_by_id:
            pred_time_days, parse_error = None, "missing prediction"
        else:
            pred_time_days, parse_error = parse_tte_prediction(raw_prediction)
        rows.append(
            {
                "sample_id": sample_id,
                "observed_time_days": float(label.observed_time_days),
                "event_observed": _as_bool(label.event_observed),
                "pred_time_days": pred_time_days,
                "raw_text": raw_prediction,
                "parse_error": parse_error,
            }
        )

    expected_ids = set(labels["sample_id"])
    metadata = {
        "n_expected": len(labels),
        "n_submitted": len(predictions),
        "n_unexpected": int((~predictions["sample_id"].isin(expected_ids)).sum()),
        "n_duplicate_ids": len(duplicated_ids),
    }
    return pd.DataFrame(rows), metadata


def score_submission(
    submission_path: Path,
    test_labels_path: Path,
    train_outcomes_path: Path,
) -> dict[str, float | int | None]:
    submission = pd.read_csv(submission_path, keep_default_na=False)
    test_labels = pd.read_csv(test_labels_path)
    train_outcomes = pd.read_csv(train_outcomes_path)
    frame, metadata = build_evaluation_frame(submission, test_labels)

    total = len(frame)
    parsed_frame = frame[frame["parse_error"].isna()].copy()
    parsed = len(parsed_frame)
    metrics: dict[str, float | int | None] = {
        **metadata,
        "n_parsed": parsed,
        "coverage": parsed / total if total else None,
        "c_index": None,
        "cmae_years": None,
        "ibs": None,
    }
    if parsed:
        metrics["c_index"] = concordance_index(parsed_frame)
        metrics["cmae_years"] = censoring_adjusted_mae(parsed_frame, train_outcomes)
        metrics["ibs"] = integrated_brier_score(parsed_frame, train_outcomes)
    return metrics


def evaluate_against_baselines(
    metrics: dict[str, float | int | None],
    baselines: dict[str, Any],
) -> dict[str, Any]:
    cox = baselines["cox"]
    rsf = baselines["rsf"]
    thresholds = {
        "coverage": 1.0,
        "c_index": max(float(cox["c_index"]), float(rsf["c_index"])),
        "cmae_years": min(float(cox["cmae_years"]), float(rsf["cmae_years"])),
        "ibs": min(float(cox["ibs"]), float(rsf["ibs"])),
    }

    coverage = _finite_metric(metrics.get("coverage"))
    c_index = _finite_metric(metrics.get("c_index"))
    cmae = _finite_metric(metrics.get("cmae_years"))
    ibs = _finite_metric(metrics.get("ibs"))
    checks = {
        "coverage": (
            coverage == thresholds["coverage"]
            and int(metrics.get("n_submitted", -1))
            == int(metrics.get("n_expected", -2))
            and int(metrics.get("n_unexpected", -1)) == 0
            and int(metrics.get("n_duplicate_ids", -1)) == 0
        ),
        "c_index": c_index is not None and c_index > thresholds["c_index"],
        "cmae_years": cmae is not None and cmae < thresholds["cmae_years"],
        "ibs": ibs is not None and ibs < thresholds["ibs"],
    }
    return {
        **metrics,
        "reward": float(all(checks.values())),
        "thresholds": thresholds,
        "passes": checks,
    }


def concordance_index(frame: pd.DataFrame) -> float | None:
    from sksurv.metrics import concordance_index_censored

    predicted_days = frame["pred_time_days"].astype(float).to_numpy()
    estimate = -predicted_days
    valid = np.isfinite(estimate)
    if valid.sum() < 2:
        return None
    try:
        result = concordance_index_censored(
            event_indicator=frame.loc[valid, "event_observed"].astype(bool).to_numpy(),
            event_time=frame.loc[valid, "observed_time_days"].astype(float).to_numpy(),
            estimate=estimate[valid],
        )
    except ValueError:
        return None
    return float(result[0])


def censoring_adjusted_mae(
    frame: pd.DataFrame,
    train_frame: pd.DataFrame,
) -> float | None:
    pred = _prediction_times_years(frame)
    observed = frame["observed_time_days"].astype(float).to_numpy() / DAYS_PER_YEAR
    event = frame["event_observed"].astype(bool).to_numpy()
    valid = np.isfinite(pred) & np.isfinite(observed)
    if valid.sum() == 0:
        return None

    train_time, train_event = _outcome_arrays(train_frame)
    try:
        surrogate = _pseudo_obs_surrogate_times(
            observed[valid], event[valid], train_time, train_event
        )
        weights = _censoring_confidence_weights(
            observed[valid], event[valid], train_time, train_event
        )
        errors = np.abs(pred[valid] - surrogate)
        return float(
            np.average(errors, weights=weights)
            if weights.sum() > 0
            else np.mean(errors)
        )
    except (IndexError, ValueError, ZeroDivisionError, FloatingPointError):
        return None


def integrated_brier_score(
    frame: pd.DataFrame,
    train_frame: pd.DataFrame,
) -> float | None:
    from sksurv.metrics import brier_score

    time_points = np.asarray(IBS_TIME_GRID_YEARS, dtype=float)
    gt_time = frame["observed_time_days"].astype(float).to_numpy() / DAYS_PER_YEAR
    gt_event = frame["event_observed"].astype(bool).to_numpy()
    train_time, train_event = _outcome_arrays(train_frame)
    pred_survival = _survival_matrix(frame, time_points)

    valid = ~(np.isnan(pred_survival).any(axis=1) | np.isnan(gt_time))
    if valid.sum() == 0:
        return None
    gt_time = gt_time[valid]
    gt_event = gt_event[valid]
    pred_survival = pred_survival[valid]

    time_mask = (
        (time_points >= np.min(gt_time))
        & (time_points < np.max(gt_time))
        & (time_points < np.max(train_time))
    )
    if time_mask.sum() == 0:
        return None

    try:
        times_out, scores = brier_score(
            survival_train=_structured_outcomes(train_event, train_time),
            survival_test=_structured_outcomes(gt_event, gt_time),
            estimate=pred_survival[:, time_mask],
            times=time_points[time_mask],
        )
    except ValueError:
        return None

    finite = np.isfinite(scores)
    if finite.sum() == 0:
        return None
    valid_times = times_out[finite]
    valid_scores = scores[finite]
    if valid_scores.size == 1:
        return float(valid_scores[0])
    integrate = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return float(
        integrate(valid_scores, valid_times) / (valid_times[-1] - valid_times[0])
    )


def _prediction_times_years(frame: pd.DataFrame) -> np.ndarray:
    return frame["pred_time_days"].astype(float).to_numpy() / DAYS_PER_YEAR


def _survival_matrix(frame: pd.DataFrame, time_grid: np.ndarray) -> np.ndarray:
    predicted_years = _prediction_times_years(frame)
    return (time_grid[None, :] <= predicted_years[:, None]).astype(float)


def _outcome_arrays(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    missing = _REQUIRED_LABEL_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(
            "training outcomes are missing required columns: "
            + ", ".join(sorted(missing))
        )
    time = frame["observed_time_days"].astype(float).to_numpy() / DAYS_PER_YEAR
    event = frame["event_observed"].map(_as_bool).to_numpy(dtype=bool)
    valid = np.isfinite(time)
    return time[valid], event[valid]


def _structured_outcomes(events: np.ndarray, times: np.ndarray) -> np.ndarray:
    return np.asarray(
        list(zip(events, times)),
        dtype=[("status", "bool"), ("time", "<f8")],
    )


def _km_product_limit(
    times: np.ndarray,
    events: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    distinct = np.unique(times)
    at_risk = np.asarray([(times >= time).sum() for time in distinct], dtype=float)
    n_events = np.asarray(
        [events[times == time].sum() for time in distinct], dtype=float
    )
    survival = np.cumprod(1.0 - n_events / at_risk)
    return distinct, at_risk, n_events, survival


def _km_curve_mean(times: np.ndarray, survival: np.ndarray) -> float:
    time_array = np.concatenate([[0.0], np.asarray(times, dtype=float)])
    survival_array = np.concatenate([[1.0], np.asarray(survival, dtype=float)])
    if survival_array[-1] > 0:
        time_array = np.concatenate(
            [time_array, [time_array[-1] / (1.0 - survival_array[-1])]]
        )
        survival_array = np.concatenate([survival_array, [0.0]])
    integrate = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return float(integrate(survival_array, time_array))


def _km_survival_at(
    distinct: np.ndarray,
    survival: np.ndarray,
    query: np.ndarray,
) -> np.ndarray:
    index = np.searchsorted(distinct, query, side="right") - 1
    output = np.where(
        index >= 0,
        survival[np.clip(index, 0, len(survival) - 1)],
        1.0,
    )
    beyond = query > distinct[-1]
    if np.any(beyond):
        span = distinct[-1] - distinct[0]
        slope = 0.0 if span == 0 else (survival[-1] - survival[0]) / span
        output = np.where(
            beyond,
            np.maximum(survival[-1] + slope * (query - distinct[-1]), 0.0),
            output,
        )
    return output


def _pseudo_obs_surrogate_times(
    event_times: np.ndarray,
    event_indicators: np.ndarray,
    train_event_times: np.ndarray,
    train_event_indicators: np.ndarray,
) -> np.ndarray:
    n_train = train_event_times.size
    truncation = min(float(np.max(train_event_times)), 30.0)
    distinct, at_risk, n_events, survival = _km_product_limit(
        train_event_times, train_event_indicators
    )
    keep = np.flatnonzero(n_events > 0)
    if keep.size == 0:
        raise ValueError("cMAE needs at least one training event.")
    if keep[-1] != distinct.size - 1:
        keep = np.append(keep, distinct.size - 1)
    event_grid = distinct[keep]
    event_at_risk = at_risk[keep]
    event_counts = n_events[keep]
    event_survival = survival[keep]
    train_mean = _km_curve_mean(event_grid, event_survival)

    surrogate = event_times.copy()
    for censor_time in np.unique(event_times[~event_indicators]):
        prefix = int(np.searchsorted(event_grid, censor_time, side="right"))
        augmented_at_risk = event_at_risk.copy()
        augmented_at_risk[:prefix] += 1.0
        augmented_survival = np.cumprod(1.0 - event_counts / augmented_at_risk)
        if prefix == event_grid.size:
            augmented_mean = _km_curve_mean(
                np.append(event_grid, censor_time),
                np.append(augmented_survival, augmented_survival[-1]),
            )
        else:
            augmented_mean = _km_curve_mean(event_grid, augmented_survival)
        surrogate[event_times == censor_time] = (
            n_train + 1
        ) * augmented_mean - n_train * train_mean
    surrogate[event_indicators] = event_times[event_indicators]
    censored = ~event_indicators
    surrogate[censored] = np.minimum(surrogate[censored], truncation)
    return surrogate


def _censoring_confidence_weights(
    event_times: np.ndarray,
    event_indicators: np.ndarray,
    train_event_times: np.ndarray,
    train_event_indicators: np.ndarray,
) -> np.ndarray:
    distinct, _, _, survival = _km_product_limit(
        train_event_times, train_event_indicators
    )
    weights = np.ones(event_times.size)
    censored = ~event_indicators
    if np.any(censored):
        weights[censored] = 1.0 - _km_survival_at(
            distinct, survival, event_times[censored]
        )
    return weights


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
        raise ValueError(f"invalid boolean value: {value!r}")
    return bool(value)


def _finite_metric(value: float | None) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    return numeric if np.isfinite(numeric) else None
